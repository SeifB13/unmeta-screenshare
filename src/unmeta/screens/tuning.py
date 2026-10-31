"""Display settings, with live adjustment while streaming (scrcpy restarts on change)."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static, Switch

from ..config import AUDIO_MODES, DisplaySettings, Profile
from ..i18n import t
from ..presets import PRESETS, Rect, Size
from ..scrcpy import build_args, format_command, parse_texture

if TYPE_CHECKING:
    from ..app import UnMetaApp

STEP_PX = 10
BIG_STEP_PX = 50
MAP_COLS = 42
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
        Binding("ctrl+left", f"screen.nudge({-BIG_STEP_PX}, 0)", show=False),
        Binding("ctrl+right", f"screen.nudge({BIG_STEP_PX}, 0)", show=False),
        Binding("ctrl+up", f"screen.nudge(0, {-BIG_STEP_PX})", show=False),
        Binding("ctrl+down", f"screen.nudge(0, {BIG_STEP_PX})", show=False),
        Binding("shift+left", f"screen.resize({-STEP_PX}, 0)", show=False),
        Binding("shift+right", f"screen.resize({STEP_PX}, 0)", show=False),
        Binding("shift+up", f"screen.resize(0, {-STEP_PX})", show=False),
        Binding("shift+down", f"screen.resize(0, {STEP_PX})", show=False),
        Binding("plus,equals_sign", "screen.rotate(1)", show=False),
        Binding("minus", "screen.rotate(-1)", show=False),
        Binding("enter", "screen.apply", show=False),
        Binding("v", "screen.full_view", show=False),
    ]


def frame_map(frame: Size, crop: Rect, cols: int = MAP_COLS) -> list[str]:
    """Draw the raw frame and the crop rectangle as character rows.

    `.` frame, `|` middle of the frame (between the two eyes), `#` crop border, `o` inside
    the crop, `!` part of the crop outside the frame, space outside both. Terminal cells
    are about twice as tall as wide, hence the halved row count.
    """
    fw, fh = frame
    cw, ch, cx, cy = crop
    left, top = min(0, cx), min(0, cy)
    right, bottom = max(fw, cx + cw), max(fh, cy + ch)
    scale = cols / (right - left)
    rows = max(1, round((bottom - top) * scale / 2))

    def at(r: int, c: int) -> tuple[float, float]:
        return left + (c + 0.5) / scale, top + (r + 0.5) * 2 / scale

    def in_crop(r: int, c: int) -> bool:
        if not (0 <= r < rows and 0 <= c < cols):
            return False
        x, y = at(r, c)
        return cx <= x < cx + cw and cy <= y < cy + ch

    mid_col = int((fw / 2 - left) * scale)
    lines = []
    for r in range(rows):
        line = []
        for c in range(cols):
            x, y = at(r, c)
            inside_frame = 0 <= x < fw and 0 <= y < fh
            if in_crop(r, c):
                if not inside_frame:
                    char = "!"
                elif all(in_crop(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                    char = "o"
                else:
                    char = "#"
            elif inside_frame:
                char = "|" if c == mid_col else "."
            else:
                char = " "
            line.append(char)
        lines.append("".join(line))
    return lines


MAP_GLYPHS = {"#": "█", "!": "█", "o": "░", "|": "┆", ".": "·"}


class FrameMap(Static):
    """The raw frame with the crop rectangle drawn on it."""

    DEFAULT_CSS = """
    FrameMap { border: round $primary; padding: 0 1; height: auto; margin-bottom: 1; }
    """

    def show(self, frame: Size | None, s: DisplaySettings, full_view: bool) -> None:
        if frame is None:
            self.update(t("tuning.map.unknown"))
            return
        accent = self.app.current_theme.accent or "yellow"
        styles = {".": "dim", "|": "dim", "#": f"bold {accent}", "o": accent, "!": "bold red"}
        crop = (s.crop_w, s.crop_h, s.crop_x, s.crop_y) if s.crop_enabled else (0, 0, 0, 0)
        text = Text()
        for line in frame_map(frame, crop):
            for char in line:
                text.append(MAP_GLYPHS.get(char, char), styles.get(char, ""))
            text.append("\n")
        w, h = frame
        text.append(t("tuning.map.size", w=w, h=h), "bold")
        if s.crop_enabled:
            text.append("\n" + t("tuning.map.crop", w=s.crop_w, h=s.crop_h, x=s.crop_x, y=s.crop_y))
            if s.crop_x + s.crop_w > w or s.crop_y + s.crop_h > h:
                text.append("\n" + t("tuning.map.outside"), "bold red")
        if full_view:
            text.append("\n" + t("tuning.map.full_view"), "italic")
        self.update(text)


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
        Binding("f6", "full_view", t("tuning.key.full_view")),
    ]

    app: UnMetaApp

    def __init__(self, profile: Profile) -> None:
        super().__init__()
        self.profile = profile
        self.s: DisplaySettings = profile.display
        self.auto_apply = True
        self.windowed = True
        self.full_view = False  # stream the raw frame to find the eye; the crop is kept
        self.frame: Size | None = profile.frame  # raw frame size, once known
        self._frame_from_device = self.frame is not None
        self._applied: DisplaySettings | None = None  # what the running preview uses
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
            with VerticalScroll(id="side"):
                yield FrameMap(id="map")
                yield NudgePad(t("tuning.pad"), id="pad")
                yield self._row(t("tuning.key.full_view"), Switch(self.full_view, id="full_view"))
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
        self._fetch_frame_size()

    @work(thread=True, exclusive=True, group="frame")
    def _fetch_frame_size(self) -> None:
        if self.app.adb is None:
            return
        size = self.app.adb.display_size(self.profile.address)
        if size:
            self.app.call_from_thread(self._set_frame, size, True)

    def _set_frame(self, size: Size, from_device: bool) -> None:
        # The crop is in headset pixels, so `wm size` wins. scrcpy's video size is only a
        # fallback: it may be scaled down (a Quest 3 frame, 4128 px, is too wide for most
        # encoders) or rounded.
        if from_device and self.profile.update_frame(size):
            self._sync_inputs()  # a crop still on its preset was rescaled
            self.app.save_config()
            self._changed()
        if from_device or not self._frame_from_device:
            self.frame = size
            self._frame_from_device = from_device
            self._update_preview()

    def scrcpy_line(self, line: str) -> None:
        """Fall back on scrcpy's log for the raw frame size while the preview is uncropped."""
        size = parse_texture(line)
        if size and not self._frame_from_device:
            self._fetch_frame_size()  # streaming, so connected now: ask the headset again
        a = self._applied
        if size and a and not a.crop_enabled and not a.angle and not a.max_size:
            self._set_frame(size, False)

    # Settings <-> widgets ------------------------------------------------------------

    def effective(self) -> DisplaySettings:
        """Settings used for the preview stream: windowed and uncropped if asked."""
        s = replace(self.s, fullscreen=False) if self.windowed else self.s
        if self.full_view:
            s = replace(s, crop_enabled=False, angle=0, max_size=0, record_path="")
        return s

    def _update_preview(self) -> None:
        args = build_args(self.profile.address, self.effective())
        self.query_one("#cmd", Static).update(format_command(args))
        self.query_one("#map", FrameMap).show(self.frame, self.s, self.full_view)

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
        if self.auto_apply and self.app.runner.running and self.effective() != self._applied:
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
        elif field == "full_view":
            # Asked for explicitly: show it now, even without auto-apply or a running stream.
            self.full_view = event.value
            self._update_preview()
            self.action_apply()
            return
        elif field in BOOL_FIELDS:
            if getattr(self.s, field) == event.value:
                return
            setattr(self.s, field, event.value)
        self._changed()

    def on_select_changed(self, event: Select.Changed) -> None:
        if not isinstance(event.value, str):
            return
        if event.select.id == "preset" and event.value != self.s.preset:
            self.s.apply_preset(event.value, self.profile.frame)
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

    def action_full_view(self) -> None:
        self.query_one("#full_view", Switch).toggle()  # on_switch_changed does the rest

    def action_reset(self) -> None:
        key = self.s.preset if self.s.preset in PRESETS else next(iter(PRESETS))
        self.s.apply_preset(key, self.profile.frame)
        self.query_one("#preset", Select).value = key
        self._sync_inputs()
        self._changed()

    def action_apply(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None
        self.app.save_config()
        self._applied = self.effective()
        self.app.start_stream(self.profile, self._applied)

    def action_back(self) -> None:
        if self._timer:
            self._timer.stop()
        self.app.save_config()
        if self.app.runner.running and self._applied not in (None, self.s):
            self.app.start_stream(self.profile)  # leave the preview: back to the real settings
        self.app.pop_screen()
        self.app.notify(t("tuning.saved"))
