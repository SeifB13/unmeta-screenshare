from __future__ import annotations

from typing import TYPE_CHECKING

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, RichLog, Select, Static

from ..config import Profile
from ..i18n import get_language, t

if TYPE_CHECKING:
    from ..app import UnMetaApp


class HomeScreen(Screen[None]):
    CSS = """
    #log { height: 1fr; border: round $panel; }
    """

    BINDINGS = [
        # Priority, or a focused button would swallow Space.
        Binding("space", "toggle_stream", t("home.key.stream"), priority=True),
        Binding("c", "connect", t("home.key.connect")),
        Binding("d", "display", t("home.key.display")),
        Binding("w", "setup", t("home.key.setup")),
        Binding("i", "app.copy_diagnostic", t("key.diagnostic")),
        Binding("question_mark,f1", "help", t("key.help")),
        Binding("l", "language", t("home.key.language")),
        Binding("q", "app.quit", t("key.quit")),
    ]

    app: UnMetaApp

    def __init__(self) -> None:
        super().__init__()
        self._conn_text = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(classes="page"):
            with Horizontal(classes="row"):
                yield Label(t("home.profile"), classes="label")
                yield Select[str]([], id="profile", prompt=t("home.no_profile"))
            with Horizontal(classes="row"):
                yield Label(t("home.address"), classes="label")
                yield Input(id="host", placeholder="192.168.1.80")
                yield Input(id="port", type="integer", classes="port")
            yield Static(id="status", classes="status")
            with Horizontal(classes="buttons"):
                yield Button(t("home.btn.start"), id="stream", variant="success")
                yield Button(t("home.btn.connect"), id="connect")
                yield Button(t("home.btn.display"), id="display")
                yield Button(t("home.btn.setup"), id="setup")
                yield Button(t("home.btn.help"), id="help")
            yield Label(t("home.log"), classes="muted")
            yield RichLog(id="log", wrap=True, markup=False)
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log", RichLog)
        for line in self.app.output:
            log.write(line)
        self.refresh_profiles()
        self.set_interval(0.5, self.update_status)
        self.query_one("#stream", Button).focus()

    def on_screen_resume(self) -> None:
        self.refresh_profiles()

    def write_log(self, line: str) -> None:
        self.query_one("#log", RichLog).write(line)

    # Profile -------------------------------------------------------------------------

    def refresh_profiles(self) -> None:
        cfg = self.app.config
        select = self.query_one("#profile", Select)
        select.set_options([(name, name) for name in cfg.profiles])
        profile = cfg.current
        if profile:
            select.value = profile.name
            self._fill_address(profile)
        self.update_status()

    def _fill_address(self, profile: Profile) -> None:
        self.query_one("#host", Input).value = profile.host
        self.query_one("#port", Input).value = str(profile.port)

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id != "profile" or not isinstance(event.value, str):
            return
        cfg = self.app.config
        if cfg.last_profile != event.value:
            cfg.last_profile = event.value
            self.app.save_config()
        self._fill_address(cfg.profiles[event.value])
        self._conn_text = ""

    def profile(self) -> Profile | None:
        """Current profile, updated with the address typed on screen."""
        profile = self.app.config.current
        if profile is None:
            self.notify(t("err.no_profile"), severity="warning")
            return None
        host = self.query_one("#host", Input).value.strip()
        try:
            port = int(self.query_one("#port", Input).value)
        except ValueError:
            port = profile.port
        if host and (host, port) != (profile.host, profile.port):
            profile.host, profile.port = host, port
            self.app.save_config()
        return profile

    # Status --------------------------------------------------------------------------

    def update_status(self) -> None:
        profile = self.app.config.current
        streaming = self.app.runner.running or self.app.reconnecting
        if profile is None:
            text = t("home.status.no_profile")
        elif self.app.reconnecting:
            text = t("home.status.reconnecting", addr=profile.address)
        elif streaming:
            text = t("home.status.streaming", addr=profile.address)
        else:
            text = self._conn_text or t("home.status.idle")
        self.query_one("#status", Static).update(text)
        button = self.query_one("#stream", Button)
        button.label = t("home.btn.stop") if streaming else t("home.btn.start")
        button.variant = "error" if streaming else "success"

    # Actions -------------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "stream": self.action_toggle_stream,
            "connect": self.action_connect,
            "display": self.action_display,
            "setup": self.action_setup,
            "help": self.action_help,
        }
        if event.button.id in actions:
            actions[event.button.id]()

    def action_toggle_stream(self) -> None:
        if self.app.runner.running or self.app.reconnecting:
            self.app.stop_stream()
            return
        profile = self.profile()
        if profile:
            self._conn_text = t("home.status.connecting", addr=profile.address)
            self.update_status()
            self.app.start_stream(profile)

    def action_connect(self) -> None:
        profile = self.profile()
        if not profile:
            return
        if not self.app.adb:
            self.notify(t("err.no_adb"), severity="error")
            return
        self._conn_text = t("home.status.connecting", addr=profile.address)
        self.update_status()
        self._connect(profile)

    @work(thread=True, exclusive=True, group="connect")
    def _connect(self, profile: Profile) -> None:
        ok = self.app.ensure_connected(profile)
        text = t("home.status.connected" if ok else "home.status.idle", addr=profile.address)
        self.app.call_from_thread(self._set_conn_text, text)

    def _set_conn_text(self, text: str) -> None:
        self._conn_text = text
        self.update_status()

    def action_display(self) -> None:
        from .tuning import TuningScreen

        profile = self.profile()
        if profile:
            self.app.push_screen(TuningScreen(profile))

    def action_setup(self) -> None:
        from .wizard import WizardScreen

        self.app.push_screen(WizardScreen())

    def action_help(self) -> None:
        from .help import HelpScreen

        self.app.push_screen(HelpScreen())

    def action_language(self) -> None:
        lang = "en" if get_language() == "fr" else "fr"
        self.app.config.language = lang
        self.app.save_config()
        self.notify(t("lang.changed", lang={"en": "English", "fr": "Français"}[lang]))
