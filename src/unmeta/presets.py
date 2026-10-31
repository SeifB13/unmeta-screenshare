"""Display presets per headset model.

The Quest mirrors a side-by-side stereo frame, so a preset crops one eye out of it and
straightens its tilt. Crop and angle depend on each other: change them together.

A crop is measured on a frame of a given size and scaled to the size of the connected
headset's frame, so a headset that mirrors a different resolution still gets the eye.
"""

from __future__ import annotations

from dataclasses import dataclass

Rect = tuple[int, int, int, int]  # width, height, x, y
Size = tuple[int, int]

# Raw frame of the Quest 3 the presets were measured on (`adb shell wm size`).
QUEST3_FRAME: Size = (4128, 2208)


@dataclass(frozen=True)
class Preset:
    key: str
    crop: Rect | None  # on `frame`
    angle: int
    frame: Size = QUEST3_FRAME

    def crop_for(self, frame: Size | None) -> Rect | None:
        """The crop scaled to `frame`; as measured when the frame size is unknown."""
        if self.crop is None or frame is None or frame == self.frame:
            return self.crop
        sx, sy = frame[0] / self.frame[0], frame[1] / self.frame[1]
        w, h, x, y = self.crop
        return round(w * sx), round(h * sy), round(x * sx), round(y * sy)


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
