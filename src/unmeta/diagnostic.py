"""A plain-text report to paste in a bug report: app, system, tools, headset, settings, log."""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from collections.abc import Iterable

from . import __version__
from .adb import Adb, parse_wm_size
from .config import Profile
from .scrcpy import build_args, format_command
from .tools import Tools, format_version

LOG_LINES = 40
# getprop keys worth reporting. No serial number: the report is meant to be shared.
HEADSET_PROPS = {
    "model": "ro.product.model",
    "android": "ro.build.version.release",
    "build": "ro.build.display.id",
}


def headset_info(adb: Adb, address: str) -> dict[str, str]:
    """Ask the headset about itself. Blocking: call from a worker thread."""
    state = adb.state(address)
    info = {"state": state}
    if state != "device":
        return info
    for key, prop in HEADSET_PROPS.items():
        code, out = adb.run("shell", "getprop", prop, serial=address, timeout=10)
        info[key] = out.strip() if code == 0 else "?"
    code, out = adb.run("shell", "wm", "size", serial=address, timeout=10)
    size = parse_wm_size(out) if code == 0 else None
    info["frame"] = f"{size[0]}x{size[1]}" if size else "?"
    return info


def build_report(
    tools: Tools,
    profile: Profile | None,
    headset: dict[str, str] | None,
    log: Iterable[str],
) -> str:
    lines = [
        f"UnMeta Screenshare {__version__}",
        f"System: {platform.system()} {platform.release()} ({platform.machine()}), "
        f"Python {platform.python_version()}"
        + (" (frozen)" if getattr(sys, "frozen", False) else ""),
        f"adb: {tools.adb or 'not found'}",
        f"scrcpy: {tools.scrcpy or 'not found'} ({format_version(tools.scrcpy_version)})",
        "",
    ]
    if profile is None:
        lines.append("Headset: no profile saved")
    else:
        frame = f"{profile.frame_w}x{profile.frame_h}" if profile.frame else "not seen yet"
        lines += [
            f"Profile: {profile.name}, {profile.address}, model {profile.model or '?'}",
            f"Saved frame size: {frame}",
            f"Command: {format_command(build_args(profile.address, profile.display))}",
        ]
    if headset is not None:
        lines.append("Headset now: " + ", ".join(f"{k} {v}" for k, v in headset.items()))
    log = list(log)[-LOG_LINES:]
    lines += ["", f"Last {len(log)} log lines:", *log] if log else ["", "Log: empty"]
    return "\n".join(lines) + "\n"


def copy_to_clipboard(text: str) -> bool:
    """Copy with the system tool; False if none worked."""
    if sys.platform == "win32":
        commands = [["clip"]]
    elif sys.platform == "darwin":
        commands = [["pbcopy"]]
    else:
        commands = [["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "-ib"]]
    for cmd in commands:
        if not shutil.which(cmd[0]):
            continue
        # clip.exe takes UTF-16 as is; anything else goes through the console code page.
        data = text.encode("utf-16-le") if cmd == ["clip"] else text.encode()
        try:
            subprocess.run(cmd, input=data, check=True, timeout=5, capture_output=True)
        except (OSError, subprocess.SubprocessError):
            continue
        return True
    return False
