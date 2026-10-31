"""Build scrcpy command lines and run scrcpy as a child process.

scrcpy cannot change crop, angle or audio while it runs, so applying new settings means
restarting it (about 1-2 s; the adb connection stays up).
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
import threading
from collections.abc import Callable
from pathlib import Path

from .config import DisplaySettings


def build_args(serial: str, s: DisplaySettings, window_title: str | None = None) -> list[str]:
    args = ["-s", serial, "--no-control", f"--max-fps={s.max_fps}"]
    if s.crop_enabled:
        args.append(f"--crop={s.crop_w}:{s.crop_h}:{s.crop_x}:{s.crop_y}")
    if s.angle:
        args.append(f"--angle={s.angle}")
    args.append(f"--video-bit-rate={s.bitrate_mbps}M")
    if s.audio == "off":
        args.append("--no-audio")
    elif s.audio == "dup":
        args.append("--audio-dup")
    if s.max_size:
        args.append(f"--max-size={s.max_size}")
    if s.fullscreen:
        args.append("--fullscreen")
    if s.always_on_top:
        args.append("--always-on-top")
    if window_title:
        args.append(f"--window-title={window_title}")
    if s.record_path:
        args.append(f"--record={s.record_path}")
    return args


def parse_texture(line: str) -> tuple[int, int] | None:
    """Size of the decoded video from a scrcpy log line like `INFO: Texture: 1904x1408`."""
    match = re.search(r"\bTexture\b[^:]*:\s*(\d+)x(\d+)", line)
    return (int(match.group(1)), int(match.group(2))) if match else None


def format_command(args: list[str]) -> str:
    if sys.platform == "win32":
        return subprocess.list2cmdline(["scrcpy", *args])
    return shlex.join(["scrcpy", *args])


class ScrcpyRunner:
    """Owns at most one scrcpy process. Callbacks run on a background thread."""

    def __init__(
        self,
        on_output: Callable[[str], None] | None = None,
        on_exit: Callable[[int, bool], None] | None = None,
    ) -> None:
        self.on_output = on_output
        self.on_exit = on_exit  # (exit code, stopped by us)
        self._proc: subprocess.Popen[str] | None = None
        self._stopped: set[int] = set()
        self._lock = threading.Lock()

    @property
    def running(self) -> bool:
        proc = self._proc
        return proc is not None and proc.poll() is None

    def start(self, exe: str, args: list[str], adb_path: str | None = None) -> None:
        with self._lock:
            self._stop_locked()
            env = os.environ.copy()
            if adb_path:
                # Make scrcpy use the same adb as us: two adb versions fight over the server.
                env["ADB"] = adb_path
            proc = subprocess.Popen(
                [exe, *args],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                cwd=str(Path(exe).parent) if os.path.isabs(exe) else None,
                env=env,
            )
            self._proc = proc
        threading.Thread(target=self._pump, args=(proc,), daemon=True).start()

    def stop(self) -> None:
        with self._lock:
            self._stop_locked()

    def _stop_locked(self) -> None:
        proc, self._proc = self._proc, None
        if proc is None or proc.poll() is not None:
            return
        self._stopped.add(proc.pid)
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    def _pump(self, proc: subprocess.Popen[str]) -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            if self.on_output:
                self.on_output(line.rstrip())
        code = proc.wait()
        intentional = proc.pid in self._stopped
        self._stopped.discard(proc.pid)
        if self.on_exit:
            self.on_exit(code, intentional)
