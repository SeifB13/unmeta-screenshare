"""Thin wrapper around the adb command line."""

from __future__ import annotations

import re
import subprocess
import threading
from dataclasses import dataclass

_IPV4 = r"(\d{1,3}(?:\.\d{1,3}){3})"
_DEVICE_PROPS = ("product", "model", "device", "transport_id", "usb")


@dataclass(frozen=True)
class Device:
    serial: str
    state: str  # device | unauthorized | offline | no permissions | ...
    model: str = ""

    @property
    def is_network(self) -> bool:
        return ":" in self.serial or "._adb-tls-connect." in self.serial

    @property
    def is_usb(self) -> bool:
        return not self.is_network and not self.serial.startswith("emulator-")

    @property
    def label(self) -> str:
        return f"{self.model} ({self.serial})" if self.model else self.serial


def parse_devices(output: str) -> list[Device]:
    """Parse `adb devices -l`."""
    devices = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith(("List of devices", "*", "adb server")):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, rest = parts[0], parts[1:]
        if rest[0] == "no" and len(rest) > 1 and rest[1] == "permissions":
            state = "no permissions"
        else:
            state = rest[0]
        props = {}
        for part in rest:
            key, sep, value = part.partition(":")
            if sep and key in _DEVICE_PROPS:
                props[key] = value
        devices.append(Device(serial, state, props.get("model", "").replace("_", " ")))
    return devices


def parse_ip_addr(output: str) -> str | None:
    """Parse `ip -f inet addr show wlan0`."""
    for ip in re.findall(rf"inet {_IPV4}/", output):
        if not ip.startswith("127."):
            return ip
    return None


def parse_ip_route(output: str) -> str | None:
    """Parse `ip route`, preferring the Wi-Fi interface."""
    lines = sorted(output.splitlines(), key=lambda line: "wlan" not in line)
    for line in lines:
        match = re.search(rf"\bsrc {_IPV4}", line)
        if match and not match.group(1).startswith("127."):
            return match.group(1)
    return None


def parse_wm_size(output: str) -> tuple[int, int] | None:
    """Parse `wm size`, preferring the override size when one is set."""
    sizes = dict(re.findall(r"(Physical|Override) size: (\d+x\d+)", output))
    size = sizes.get("Override") or sizes.get("Physical")
    if not size:
        return None
    w, h = size.split("x")
    return int(w), int(h)


def classify_connect(output: str) -> str:
    """Map `adb connect` output to ok | unauthorized | unreachable."""
    text = output.lower()
    if "connected to" in text and "cannot" not in text and "failed" not in text:
        return "ok"
    if "authenticate" in text or "unauthorized" in text:
        return "unauthorized"
    return "unreachable"


class Adb:
    def __init__(self, path: str) -> None:
        self.path = path
        self._server_lock = threading.Lock()
        self._server_started = False

    def _ensure_server(self) -> None:
        # The adb daemon inherits the handles of the command that spawns it; started from a
        # captured command, it would keep the pipe open and make that call hang.
        with self._server_lock:
            if self._server_started:
                return
            try:
                subprocess.run(
                    [self.path, "start-server"],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=30,
                )
            except (OSError, subprocess.TimeoutExpired):
                pass
            self._server_started = True

    def run(self, *args: str, serial: str | None = None, timeout: float = 15) -> tuple[int, str]:
        self._ensure_server()
        cmd = [self.path, *(["-s", serial] if serial else []), *args]
        try:
            proc = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return -1, "timeout"
        except OSError as exc:
            return -1, str(exc)
        return proc.returncode, (proc.stdout + proc.stderr).strip()

    def devices(self) -> list[Device]:
        code, out = self.run("devices", "-l", timeout=10)
        return parse_devices(out) if code == 0 else []

    def state(self, serial: str) -> str:
        code, out = self.run("get-state", serial=serial, timeout=10)
        return out.strip() if code == 0 else "offline"

    def model(self, serial: str) -> str:
        code, out = self.run("shell", "getprop", "ro.product.model", serial=serial)
        return out.strip() if code == 0 else ""

    def wifi_ip(self, serial: str) -> str | None:
        code, out = self.run("shell", "ip", "-f", "inet", "addr", "show", "wlan0", serial=serial)
        ip = parse_ip_addr(out) if code == 0 else None
        if ip:
            return ip
        code, out = self.run("shell", "ip", "route", serial=serial)
        return parse_ip_route(out) if code == 0 else None

    def display_size(self, serial: str) -> tuple[int, int] | None:
        code, out = self.run("shell", "wm", "size", serial=serial, timeout=10)
        return parse_wm_size(out) if code == 0 else None

    def tcpip(self, serial: str, port: int) -> tuple[bool, str]:
        code, out = self.run("tcpip", str(port), serial=serial)
        return code == 0, out

    def connect(self, address: str) -> tuple[str, str]:
        """Return (ok | unauthorized | unreachable, raw adb output)."""
        code, out = self.run("connect", address, timeout=12)
        if code != 0 and not out:
            return "unreachable", out
        return classify_connect(out), out

    def disconnect(self, address: str) -> None:
        self.run("disconnect", address, timeout=10)
