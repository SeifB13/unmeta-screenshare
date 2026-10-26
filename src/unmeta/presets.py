"""Display presets per headset model.

The Quest mirrors a side-by-side stereo frame, so a preset crops one eye out of it and
straightens its tilt. Crop and angle depend on each other: change them together.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    key: str
    crop: tuple[int, int, int, int] | None  # width, height, x, y
    angle: int


PRESETS: dict[str, Preset] = {
    p.key: p
    for p in (
        # Tested on a Quest 3.
        Preset("quest3", crop=(1900, 1400, 100, 300), angle=20),
        # Raw frame, useful as a starting point for an untested headset.
        Preset("full", crop=None, angle=0),
    )
}

DEFAULT_PRESET = "quest3"
