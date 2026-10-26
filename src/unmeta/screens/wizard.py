"""First-time setup: USB, debugging prompt, Wi-Fi ADB, then connection over Wi-Fi."""

from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, ContentSwitcher, Footer, Header, Input, Label, Markdown, Static

from .. import tools
from ..adb import Device
from ..config import DEFAULT_PORT, Profile
from ..i18n import t

if TYPE_CHECKING:
    from ..app import UnMetaApp

STEPS = ("tools", "prereq", "plug", "authorize", "wifi", "unplug", "connect")
POLLED_STEPS = ("plug", "authorize", "unplug")


def _pick_usb(devices: list[Device]) -> Device | None:
    usb = [d for d in devices if d.is_usb]
    quests = [d for d in usb if "quest" in d.model.lower()]
    return (quests or usb or [None])[0]


class WizardScreen(Screen[None]):
    CSS = """
    #stepbar { text-style: bold; color: $accent; padding-bottom: 1; }
    #steps { height: 1fr; }
    #steps > VerticalScroll { height: 1fr; }
    #nav { height: auto; dock: bottom; padding: 1 2 0 2; }
    #nav Button { margin-right: 1; }
    """

    BINDINGS = [Binding("escape", "cancel", t("key.cancel"))]

    app: UnMetaApp

    def __init__(self) -> None:
        super().__init__()
        self.step = 0
        self.usb_serial: str | None = None
        self.host = ""
        self.port = DEFAULT_PORT
        self.model = ""
        self._poll_timer: Timer | None = None
        self._connected = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="page"):
            yield Static(id="stepbar")
            with ContentSwitcher(initial="step-tools", id="steps"):
                with VerticalScroll(id="step-tools"):
                    yield Markdown(t("wiz.tools.body"))
                    yield Static(id="tools-status", classes="status")
                    yield Button(t("wiz.tools.recheck"), id="recheck")
                with VerticalScroll(id="step-prereq"):
                    yield Markdown(t("wiz.prereq.body"))
                    yield Button(t("wiz.prereq.skip"), id="skip")
                with VerticalScroll(id="step-plug"):
                    yield Markdown(t("wiz.plug.body"))
                    yield Static(t("wiz.plug.waiting"), id="plug-status", classes="status")
                with VerticalScroll(id="step-authorize"):
                    yield Markdown(t("wiz.authorize.body"))
                    yield Static(id="authorize-status", classes="status")
                with VerticalScroll(id="step-wifi"):
                    yield Markdown(t("wiz.wifi.body"))
                    yield Button(t("wiz.wifi.button"), id="enable-wifi", variant="primary")
                    yield Static(id="wifi-status", classes="status")
                with VerticalScroll(id="step-unplug"):
                    yield Markdown(t("wiz.unplug.body"))
                    yield Static(t("wiz.unplug.waiting"), id="unplug-status", classes="status")
                with VerticalScroll(id="step-connect"):
                    yield Markdown(t("wiz.connect.body"))
                    with Horizontal(classes="row"):
                        yield Label(t("wiz.connect.address"), classes="label")
                        yield Input(id="host", placeholder="192.168.1.80")
                        yield Input(str(DEFAULT_PORT), id="port", type="integer", classes="port")
                    yield Button(t("wiz.connect.button"), id="do-connect", variant="primary")
                    yield Static(id="connect-status", classes="status")
                    with Horizontal(classes="row"):
                        yield Label(t("wiz.connect.name"), classes="label")
                        yield Input(id="name", placeholder="Quest 3")
                    yield Button(
                        t("wiz.connect.finish"), id="finish", variant="success", disabled=True
                    )
        with Horizontal(id="nav"):
            yield Button(t("wiz.back"), id="back")
            yield Button(t("wiz.next"), id="next", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        self.go(0)

    def on_unmount(self) -> None:
        self._stop_polling()

    # Navigation ----------------------------------------------------------------------

    @property
    def step_name(self) -> str:
        return STEPS[self.step]

    def go(self, index: int) -> None:
        self._stop_polling()
        self.step = index
        name = self.step_name
        self.query_one("#steps", ContentSwitcher).current = f"step-{name}"
        self.query_one("#stepbar", Static).update(
            t("wiz.stepbar", n=index + 1, total=len(STEPS), title=t(f"wiz.{name}.title"))
        )
        self.query_one("#back", Button).disabled = index == 0
        next_button = self.query_one("#next", Button)
        next_button.display = name != "connect"
        next_button.disabled = name in ("tools", "plug", "authorize", "wifi")
        getattr(self, f"_enter_{name}", lambda: None)()
        if name in POLLED_STEPS:
            self._poll_timer = self.set_interval(1.0, self._poll)
            self._poll()

    def go_to(self, name: str) -> None:
        self.go(STEPS.index(name))

    def _stop_polling(self) -> None:
        if self._poll_timer:
            self._poll_timer.stop()
            self._poll_timer = None

    def _status(self, widget_id: str, text: str) -> None:
        self.query_one(f"#{widget_id}", Static).update(text)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "back":
                self.go(max(0, self.step - 1))
            case "next":
                self.go(min(len(STEPS) - 1, self.step + 1))
            case "recheck":
                self._enter_tools()
            case "skip":
                self.go_to("connect")
            case "enable-wifi":
                event.button.disabled = True
                self._status("wifi-status", t("wiz.wifi.working"))
                self._enable_wifi(self.usb_serial or "")
            case "do-connect":
                self._start_connect()
            case "finish":
                self._finish()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in ("host", "port"):
            self._start_connect()
        elif event.input.id == "name" and self._connected:
            self._finish()

    def action_cancel(self) -> None:
        self.app.pop_screen()

    # Step: tools ---------------------------------------------------------------------

    def _enter_tools(self) -> None:
        self._status("tools-status", t("wiz.tools.checking"))
        self._check_tools()

    @work(thread=True, exclusive=True, group="tools")
    def _check_tools(self) -> None:
        self.app.call_from_thread(self._show_tools, tools.detect())

    def _show_tools(self, found: tools.Tools) -> None:
        self.app.set_tools(found)
        lines = [t("wiz.tools.adb_ok", path=found.adb) if found.adb else t("wiz.tools.adb_missing")]
        version = tools.format_version(found.scrcpy_version)
        if not found.scrcpy:
            lines.append(t("wiz.tools.scrcpy_missing"))
        elif found.scrcpy_ok:
            lines.append(t("wiz.tools.scrcpy_ok", version=version, path=found.scrcpy))
        else:
            lines.append(t("wiz.tools.scrcpy_old", version=version, path=found.scrcpy))
        if not found.ok:
            lines += ["", t("wiz.tools.hint", hint=tools.install_hint())]
        self._status("tools-status", "\n".join(lines))
        if self.step_name == "tools":
            self.query_one("#next", Button).disabled = not found.ok

    # Steps polling adb devices: plug, authorize, unplug ----------------------------------

    def _poll(self) -> None:
        if self.app.adb:
            self._poll_devices()

    @work(thread=True, exclusive=True, group="poll")
    def _poll_devices(self) -> None:
        assert self.app.adb is not None
        devices = self.app.adb.devices()
        self.app.call_from_thread(self._on_devices, devices)

    def _on_devices(self, devices: list[Device]) -> None:
        name = self.step_name
        if name == "plug":
            device = _pick_usb(devices)
            if device:
                self.usb_serial = device.serial
                self.go_to("authorize")
        elif name == "authorize":
            device = next((d for d in devices if d.serial == self.usb_serial), None)
            device = device or _pick_usb(devices)
            if device is None:
                self._status("authorize-status", t("wiz.authorize.lost"))
                return
            self.usb_serial = device.serial
            if device.state == "device":
                self.model = device.model
                self.go_to("wifi")
            elif device.state == "no permissions":
                self._status("authorize-status", t("wiz.authorize.no_permissions"))
            else:
                self._status("authorize-status", t("wiz.authorize.waiting", name=device.label))
        elif name == "unplug":
            if not any(d.serial == self.usb_serial for d in devices):
                self.go_to("connect")

    # Step: wifi ----------------------------------------------------------------------

    def _enter_wifi(self) -> None:
        self.query_one("#enable-wifi", Button).disabled = False
        self._status("wifi-status", "")

    @work(thread=True, exclusive=True, group="wifi")
    def _enable_wifi(self, serial: str) -> None:
        adb = self.app.adb
        assert adb is not None
        model = adb.model(serial)
        ip = adb.wifi_ip(serial)  # before tcpip: the USB link restarts right after it
        ok, message = adb.tcpip(serial, self.port)
        self.app.call_from_thread(self._wifi_done, ok, ip, model, message)

    def _wifi_done(self, ok: bool, ip: str | None, model: str, message: str) -> None:
        if not ok:
            self._status("wifi-status", t("wiz.wifi.failed", msg=message))
            self.query_one("#enable-wifi", Button).disabled = False
            return
        self.model = model or self.model
        self.host = ip or ""
        self._status("wifi-status", t("wiz.wifi.ok", ip=ip) if ip else t("wiz.wifi.no_ip"))
        if self.step_name == "wifi":
            self.query_one("#next", Button).disabled = False

    # Step: connect -------------------------------------------------------------------

    def _enter_connect(self) -> None:
        host_input = self.query_one("#host", Input)
        if self.host:
            host_input.value = self.host
        self.query_one("#port", Input).value = str(self.port)
        if self.model and not self.query_one("#name", Input).value:
            self.query_one("#name", Input).value = self.model
        if host_input.value:
            self._start_connect()
        else:
            host_input.focus()

    def _address(self) -> tuple[str, int]:
        host = self.query_one("#host", Input).value.strip()
        try:
            port = int(self.query_one("#port", Input).value)
        except ValueError:
            port = DEFAULT_PORT
        return host, port

    def _start_connect(self) -> None:
        if not self.app.adb:
            self._status("connect-status", t("err.no_adb"))
            return
        host, port = self._address()
        if not host:
            self.query_one("#host", Input).focus()
            return
        self._connected = False
        self.query_one("#finish", Button).disabled = True
        self._status("connect-status", t("wiz.connect.working", addr=f"{host}:{port}"))
        self._connect(f"{host}:{port}")

    @work(thread=True, exclusive=True, group="connect")
    def _connect(self, address: str) -> None:
        adb = self.app.adb
        assert adb is not None
        status, raw = adb.connect(address)
        ok = status == "ok" and adb.state(address) == "device"
        model = adb.model(address) if ok else ""
        self.app.call_from_thread(self._connect_done, address, ok, status, model)

    def _connect_done(self, address: str, ok: bool, status: str, model: str) -> None:
        if not ok:
            key = "err.unauthorized" if status == "unauthorized" else "err.unreachable"
            self._status("connect-status", "✗ " + t(key, addr=address))
            return
        self._connected = True
        self.model = model or self.model
        self._status("connect-status", t("wiz.connect.ok", model=self.model or address))
        name_input = self.query_one("#name", Input)
        if not name_input.value:
            name_input.value = self.model or "Quest"
        self.query_one("#finish", Button).disabled = False
        self.query_one("#finish", Button).focus()

    def _finish(self) -> None:
        host, port = self._address()
        cfg = self.app.config
        name = self.query_one("#name", Input).value.strip() or self.model or "Quest"
        profile = cfg.profiles.get(name) or Profile(name=name, host=host)
        profile.host, profile.port = host, port
        profile.serial = self.usb_serial or profile.serial
        profile.model = self.model or profile.model
        cfg.profiles[name] = profile
        cfg.last_profile = name
        self.app.save_config()
        self.app.pop_screen()
        self.app.notify(t("wiz.saved", name=name))
