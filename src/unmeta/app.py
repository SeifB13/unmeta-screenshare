from __future__ import annotations

from collections import deque
from pathlib import Path

from textual import work
from textual.app import App

from . import APP_NAME, __version__, config, diagnostic, tools
from .adb import Adb
from .config import Config, DisplaySettings, Profile
from .i18n import t
from .scrcpy import ScrcpyRunner, build_args, format_command
from .screens.home import HomeScreen
from .screens.tuning import TuningScreen
from .screens.wizard import WizardScreen

CSS = """
.page { padding: 1 2; }
.row { height: auto; margin-bottom: 1; }
.label { width: 22; padding-top: 1; }
.row Input { width: 1fr; }
.row Select { width: 1fr; }
.row Switch { width: auto; }
Input.port { width: 12; }
.buttons { height: auto; margin-bottom: 1; }
.buttons Button { margin-right: 1; }
.status { height: auto; padding: 1 0; }
.muted { color: $text-muted; }
"""


class UnMetaApp(App[None]):
    TITLE = APP_NAME
    # Textual's Ctrl+P palette only offers themes and the like: noise for this app's users.
    ENABLE_COMMAND_PALETTE = False
    SUB_TITLE = f"v{__version__}"
    CSS = CSS

    def __init__(self, cfg: Config, config_path: Path | None = None) -> None:
        super().__init__()
        self.config = cfg
        self.config_path = config_path
        self.tools = tools.Tools(adb=None, scrcpy=None, scrcpy_version=None)
        self.adb: Adb | None = None
        self.output: deque[str] = deque(maxlen=500)
        self.runner = ScrcpyRunner(on_output=self._on_scrcpy_output, on_exit=self._on_scrcpy_exit)

    def set_tools(self, found: tools.Tools) -> None:
        self.tools = found
        if found.adb and (self.adb is None or self.adb.path != found.adb):
            self.adb = Adb(found.adb)

    def save_config(self) -> None:
        config.save(self.config, self.config_path)

    def on_mount(self) -> None:
        self.set_tools(tools.detect())
        self.push_screen(HomeScreen())
        if not self.config.profiles or not self.tools.ok:
            self.push_screen(WizardScreen())

    def on_unmount(self) -> None:
        self.runner.stop()

    # scrcpy process ------------------------------------------------------------------

    @work(thread=True, exclusive=True, group="stream")
    def start_stream(self, profile: Profile, settings: DisplaySettings | None = None) -> None:
        if not self.adb:
            self.call_from_thread(self.notify, t("err.no_adb"), severity="error")
            return
        if not self.tools.scrcpy_ok or not self.tools.scrcpy:
            self.call_from_thread(self.notify, t("err.no_scrcpy"), severity="error")
            return
        if not self.ensure_connected(profile):
            return
        frame = self.adb.display_size(profile.address)
        if frame and settings is None:
            self.call_from_thread(self.adopt_frame, profile, frame)
        args = build_args(
            profile.address, settings or profile.display, f"{APP_NAME} · {profile.name}"
        )
        self.call_from_thread(self.append_output, f"$ {format_command(args)}")
        self.runner.start(self.tools.scrcpy, args, adb_path=self.tools.adb)

    @work(thread=True, exclusive=True, group="stream")
    def stop_stream(self) -> None:
        self.runner.stop()

    # Diagnostic ----------------------------------------------------------------------

    def action_copy_diagnostic(self) -> None:
        self.notify(t("diag.working"))
        self._collect_diagnostic()

    @work(thread=True, exclusive=True, group="diagnostic")
    def _collect_diagnostic(self) -> None:
        profile = self.config.current
        headset = (
            diagnostic.headset_info(self.adb, profile.address) if self.adb and profile else None
        )
        report = diagnostic.build_report(self.tools, profile, headset, self.output)
        path = (self.config_path or config.default_path()).with_name("diagnostic.txt")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report, encoding="utf-8")
        except OSError:
            path = None
        copied = diagnostic.copy_to_clipboard(report)
        self.call_from_thread(self._diagnostic_done, report, copied, path)

    def _diagnostic_done(self, report: str, copied: bool, path: Path | None) -> None:
        if not copied:
            self.copy_to_clipboard(report)  # terminal clipboard (OSC 52), when supported
        if copied:
            text = t("diag.copied")
        elif path:
            text = t("diag.saved", path=path)
        else:
            text = t("diag.failed")
        if copied and path:
            text += "\n" + t("diag.also_saved", path=path)
        self.notify(text, timeout=15)

    def adopt_frame(self, profile: Profile, frame: tuple[int, int]) -> None:
        """Record the headset's frame size; a crop still on its preset is rescaled to it."""
        if profile.update_frame(frame):
            self.save_config()

    def ensure_connected(self, profile: Profile) -> bool:
        """Connect if needed. Blocking: call from a worker thread."""
        assert self.adb is not None
        if self.adb.state(profile.address) == "device":
            return True
        status, raw = self.adb.connect(profile.address)
        if raw:
            self.call_from_thread(self.append_output, raw)
        if status == "ok" and self.adb.state(profile.address) == "device":
            return True
        key = "err.unauthorized" if status == "unauthorized" else "err.unreachable"
        self.call_from_thread(
            self.notify, t(key, addr=profile.address), severity="error", timeout=10
        )
        return False

    def append_output(self, line: str) -> None:
        self.output.append(line)
        for screen in self.screen_stack:
            if isinstance(screen, HomeScreen):
                screen.write_log(line)
            elif isinstance(screen, TuningScreen):
                screen.scrcpy_line(line)

    def _on_scrcpy_output(self, line: str) -> None:
        self.call_from_thread(self.append_output, line)

    def _on_scrcpy_exit(self, code: int, intentional: bool) -> None:
        if intentional:
            return
        if code == 0:
            self.call_from_thread(self.notify, t("stream.ended"))
        else:
            self.call_from_thread(
                self.notify, t("stream.crashed", code=code), severity="error", timeout=10
            )
