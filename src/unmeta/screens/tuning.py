"""Display settings, with live adjustment while streaming (scrcpy restarts on change)."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, Switch

from ..config import AUDIO_MODES, DisplaySettings, Profile
from ..i18n import t
from ..presets import PRESETS
from ..scrcpy import build_args, format_command

if TYPE_CHECKING:
    from ..app import UnMetaApp

STEP_PX = 10
AUTO_APPLY_DELAY = 0.8

# Input id -> (min, max). Ids match DisplaySettings attributes.
INT_FIELDS = {
    "crop_w": (1, 10000),
    "crop_h": (1, 10000),
    "crop_x": (0, 10000),
    "crop_y": (0, 10000),
    "angle": (-180, 180),
    "max_fps": (1, 240),
    "bitrate_mbps": (1, 200),
    "max_size": (0, 10000),
}
BOOL_FIELDS = ("crop_enabled", "fullscreen", "always_on_top")


class NudgePad(Static, can_focus=True):
    """Focusable panel turning arrow keys into crop/angle nudges."""

    DEFAULT_CSS = """
    NudgePad { border: round $primary; padding: 1 2; height: auto; }
    NudgePad:focus { border: heavy $accent; background: $boost; }
    """

    BINDINGS = [
        Binding("left", f"screen.nudge({-STEP_PX}, 0)", show=False),
        Binding("right", f"screen.nudge({STEP_PX}, 0)", show=False),
        Binding("up", f"screen.nudge(0, {-STEP_PX})", show=False),
        Binding("down", f"screen.nudge(0, {STEP_PX})", show=False),
        Binding("shift+left", f"screen.resize({-STEP_PX}, 0)", show=False),
        Binding("shift+right", f"screen.resize({STEP_PX}, 0)", show=False),
        Binding("shift+up", f"screen.resize(0, {-STEP_PX})", show=False),
        Binding("shift+down", f"screen.resize(0, {STEP_PX})", show=False),
        Binding("plus,equals_sign", "screen.rotate(1)", show=False),
        Binding("minus", "screen.rotate(-1)", show=False),
        Binding("enter", "screen.apply", show=False),
    ]


def _clamp(field: str, value: int) -> int:
    low, high = INT_FIELDS[field]
    return max(low, min(high, value))


class TuningScreen(Screen[None]):
    CSS = """
    #form { width: 1fr; }
    #side { width: 50; padding-left: 2; }
    .crop Input { width: 1fr; }
    #cmd { padding-top: 1; }
    """

    BINDINGS = [
        Binding("escape", "back", t("key.back")),
        Binding("f5", "apply", t("tuning.key.apply")),
        Binding("ctrl+r", "reset", t("tuning.key.reset")),
    ]

    app: UnMetaApp

    def __init__(self, profile: Profile) -> None:
        super().__init__()
        self.profile = profile
        self.s: DisplaySettings = profile.display
        self.auto_apply = True
        self.windowed = True
        self._timer: Timer | None = None

    # Layout --------------------------------------------------------------------------

    def _row(self, label: str, *widgets) -> Horizontal:
        return Horizontal(Label(label, classes="label"), *widgets, classes="row")

    def _int_input(self, field: str, placeholder: str = "") -> Input:
        return Input(str(getattr(self.s, field)), id=field, type="integer", placeholder=placeholder)

    def compose(self) -> ComposeResult:
        s = self.s
        preset = s.preset if s.preset in PRESETS else None
        yield Header()
        with Horizontal(classes="page"):
            with VerticalScroll(id="form"):
                yield self._row(
                    t("tuning.preset"),
                    Select(
                        [(t(f"preset.{k}"), k) for k in PRESETS],
                        value=preset or Select.BLANK,
                        id="preset",
                    ),
                )
                yield self._row(t("tuning.crop"), Switch(s.crop_enabled, id="crop_enabled"))
                yield Horizontal(
                    Label(t("tuning.crop_dims"), classes="label"),
                    *(self._int_input(f) for f in ("crop_w", "crop_h", "crop_x", "crop_y")),
                    classes="row crop",
                )
                yield self._row(t("tuning.angle"), self._int_input("angle"))
                yield self._row(t("tuning.fps"), self._int_input("max_fps"))
                yield self._row(t("tuning.bitrate"), self._int_input("bitrate_mbps"))
                yield self._row(
                    t("tuning.max_size"), self._int_input("max_size", t("tuning.max_size_ph"))
                )
                yield self._row(
                    t("tuning.audio"),
                    Select(
                        [(t(f"audio.{m}"), m) for m in AUDIO_MODES],
                        value=s.audio,
                        allow_blank=False,
                        id="audio",
                    ),
                )
                yield self._row(t("tuning.fullscreen"), Switch(s.fullscreen, id="fullscreen"))
                yield self._row(t("tuning.on_top"), Switch(s.always_on_top, id="always_on_top"))
                yield self._row(
                    t("tuning.record"),
                    Input(s.record_path, id="record_path", placeholder=t("tuning.record_ph")),
                )
            with Vertical(id="side"):
                yield NudgePad(t("tuning.pad"), id="pad")
                yield self._row(t("tuning.auto"), Switch(self.auto_apply, id="auto_apply"))
                yield self._row(t("tuning.windowed"), Switch(self.windowed, id="windowed"))
                with Horizontal(classes="buttons"):
                    yield Button(t("tuning.apply"), id="apply", variant="primary")
                    yield Button(t("tuning.reset"), id="reset")
                yield Static(id="cmd", classes="muted")
        yield Footer()

    def on_mount(self) -> None:
        self.title = t("tuning.title", name=self.profile.name)
        self._update_preview()
        self.query_one("#pad", NudgePad).focus()

    # Settings <-> widgets ------------------------------------------------------------

    def effective(self) -> DisplaySettings:
        """Settings used for the preview stream: no fullscreen while tuning if asked."""
        return replace(self.s, fullscreen=False) if self.windowed else self.s

    def _update_preview(self) -> None:
        args = build_args(self.profile.address, self.effective())
        self.query_one("#cmd", Static).update(format_command(args))

    def _sync_inputs(self) -> None:
        for field in INT_FIELDS:
            widget = self.query_one(f"#{field}", Input)
            value = str(getattr(self.s, field))
            if widget.value != value:
                widget.value = value
        self.query_one("#crop_enabled", Switch).value = self.s.crop_enabled

    def _changed(self) -> None:
        self._update_preview()
        if self._timer:
            self._timer.stop()
            self._timer = None
        if self.auto_apply and self.app.runner.running:
            self._timer = self.set_timer(AUTO_APPLY_DELAY, self.action_apply)

    def on_input_changed(self, event: Input.Changed) -> None:
        field = event.input.id or ""
        if field == "record_path":
            self.s.record_path = event.value.strip()
        elif field in INT_FIELDS:
            try:
                value = int(event.value)
            except ValueError:
                return
            if _clamp(field, value) != value or getattr(self.s, field) == value:
                return
            setattr(self.s, field, value)
        else:
            return
        self._changed()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.action_apply()

    def on_switch_changed(self, event: Switch.Changed) -> None:
        field = event.switch.id or ""
        if field == "auto_apply":
            self.auto_apply = event.value
            return
        if field == "windowed":
            self.windowed = event.value
        elif field in BOOL_FIELDS:
            if getattr(self.s, field) == event.value:
                return
            setattr(self.s, field, event.value)
        self._changed()

    def on_select_changed(self, event: Select.Changed) -> None:
        if not isinstance(event.value, str):
            return
        if event.select.id == "preset" and event.value != self.s.preset:
            self.s.apply_preset(event.value)
            self._sync_inputs()
            self._changed()
        elif event.select.id == "audio" and event.value != self.s.audio:
            self.s.audio = event.value
            self._changed()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "apply":
            self.action_apply()
        elif event.button.id == "reset":
            self.action_reset()

    # Actions -------------------------------------------------------------------------

    def action_nudge(self, dx: int, dy: int) -> None:
        self.s.crop_x = _clamp("crop_x", self.s.crop_x + dx)
        self.s.crop_y = _clamp("crop_y", self.s.crop_y + dy)
        self._sync_inputs()
        self._changed()

    def action_resize(self, dw: int, dh: int) -> None:
        self.s.crop_w = _clamp("crop_w", self.s.crop_w + dw)
        self.s.crop_h = _clamp("crop_h", self.s.crop_h + dh)
        self._sync_inputs()
        self._changed()

    def action_rotate(self, delta: int) -> None:
        self.s.angle = _clamp("angle", self.s.angle + delta)
        self._sync_inputs()
        self._changed()

    def action_reset(self) -> None:
        key = self.s.preset if self.s.preset in PRESETS else next(iter(PRESETS))
        self.s.apply_preset(key)
        self.query_one("#preset", Select).value = key
        self._sync_inputs()
        self._changed()

    def action_apply(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self.app.save_config()
        self.app.start_stream(self.profile, self.effective())

    def action_back(self) -> None:
        if self._timer:
            self._timer.stop()
        self.app.save_config()
        if self.app.runner.running and self.windowed and self.s.fullscreen:
            self.app.start_stream(self.profile)  # leave the preview: back to fullscreen
        self.app.pop_screen()
        self.app.notify(t("tuning.saved"))
