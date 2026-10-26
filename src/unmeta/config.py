"""Saved headsets ("profiles") and their display settings, stored as JSON."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir

from .presets import DEFAULT_PRESET, PRESETS

DEFAULT_PORT = 5555
AUDIO_MODES = ("off", "pc", "dup")


@dataclass
class DisplaySettings:
    preset: str = DEFAULT_PRESET
    crop_enabled: bool = True
    crop_w: int = 1900
    crop_h: int = 1400
    crop_x: int = 100
    crop_y: int = 300
    angle: int = 20
    max_fps: int = 60
    bitrate_mbps: int = 12
    max_size: int = 0
    audio: str = "dup"  # off | pc (PC only) | dup (headset + PC)
    fullscreen: bool = False  # windowed by default: the app's menu stays reachable
    always_on_top: bool = False
    record_path: str = ""

    def apply_preset(self, key: str) -> None:
        preset = PRESETS[key]
        self.preset = key
        self.angle = preset.angle
        self.crop_enabled = preset.crop is not None
        if preset.crop:
            self.crop_w, self.crop_h, self.crop_x, self.crop_y = preset.crop

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DisplaySettings:
        known = {f.name for f in fields(cls)}
        settings = cls(**{k: v for k, v in data.items() if k in known})
        if settings.audio not in AUDIO_MODES:
            settings.audio = "dup"
        return settings


@dataclass
class Profile:
    name: str
    host: str
    port: int = DEFAULT_PORT
    serial: str = ""  # hardware serial seen over USB, kept to recognise the headset
    model: str = ""
    display: DisplaySettings = field(default_factory=DisplaySettings)

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Profile:
        return cls(
            name=str(data["name"]),
            host=str(data.get("host", "")),
            port=int(data.get("port", DEFAULT_PORT)),
            serial=str(data.get("serial", "")),
            model=str(data.get("model", "")),
            display=DisplaySettings.from_dict(data.get("display", {})),
        )


@dataclass
class Config:
    language: str | None = None  # None = follow the system locale
    last_profile: str | None = None
    profiles: dict[str, Profile] = field(default_factory=dict)

    @property
    def current(self) -> Profile | None:
        if self.last_profile in self.profiles:
            return self.profiles[self.last_profile]
        return next(iter(self.profiles.values()), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "last_profile": self.last_profile,
            "profiles": [asdict(p) for p in self.profiles.values()],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        profiles = {}
        for item in data.get("profiles", []):
            try:
                profile = Profile.from_dict(item)
            except (KeyError, TypeError, ValueError):
                continue
            profiles[profile.name] = profile
        return cls(
            language=data.get("language"),
            last_profile=data.get("last_profile"),
            profiles=profiles,
        )


def default_path() -> Path:
    return Path(user_config_dir("unmeta-screenshare", appauthor=False)) / "config.json"


def load(path: Path | None = None) -> Config:
    path = path or default_path()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Config()
    if not isinstance(data, dict):
        return Config()
    return Config.from_dict(data)


def save(config: Config, path: Path | None = None) -> None:
    path = path or default_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(config.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)
