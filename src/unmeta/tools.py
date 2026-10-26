"""Locate adb and scrcpy: copy bundled with the app first, then PATH."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MIN_SCRCPY = (3, 0)  # --angle appeared in scrcpy 3.0


@dataclass(frozen=True)
class Tools:
    adb: str | None
    scrcpy: str | None
    scrcpy_version: tuple[int, ...] | None

    @property
    def scrcpy_ok(self) -> bool:
        return bool(self.scrcpy and self.scrcpy_version and self.scrcpy_version >= MIN_SCRCPY)

    @property
    def ok(self) -> bool:
        return bool(self.adb) and self.scrcpy_ok


def vendor_dirs() -> list[Path]:
    if getattr(sys, "frozen", False):
        dirs = [Path(sys.executable).parent / "vendor" / "scrcpy"]
        if hasattr(sys, "_MEIPASS"):
            dirs.insert(0, Path(sys._MEIPASS) / "vendor" / "scrcpy")
        return dirs
    # Running from a source checkout: packaging/windows/fetch_scrcpy.py fills this folder.
    return [Path(__file__).resolve().parents[2] / "vendor" / "scrcpy"]


def find(name: str) -> str | None:
    exe = f"{name}.exe" if sys.platform == "win32" else name
    for directory in vendor_dirs():
        candidate = directory / exe
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def parse_version(text: str) -> tuple[int, ...] | None:
    match = re.search(r"scrcpy (\d+)\.(\d+)(?:\.(\d+))?", text)
    if not match:
        return None
    return tuple(int(g) for g in match.groups() if g is not None)


def scrcpy_version(path: str) -> tuple[int, ...] | None:
    try:
        proc = subprocess.run(
            [path, "--version"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_version(proc.stdout + proc.stderr)


def detect() -> Tools:
    scrcpy = find("scrcpy")
    return Tools(
        adb=find("adb"),
        scrcpy=scrcpy,
        scrcpy_version=scrcpy_version(scrcpy) if scrcpy else None,
    )


def install_hint() -> str:
    if sys.platform == "win32":
        return "winget install --exact Genymobile.scrcpy"
    if sys.platform == "darwin":
        return "brew install scrcpy && brew install --cask android-platform-tools"
    return "https://github.com/Genymobile/scrcpy/blob/master/doc/linux.md"


def format_version(version: tuple[int, ...] | None) -> str:
    return ".".join(map(str, version)) if version else "?"
