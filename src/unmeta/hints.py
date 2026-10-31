"""Turn known scrcpy and adb error lines into a plain-language hint (an i18n key)."""

from __future__ import annotations

# (all of these words, in lower case) -> i18n key. First match wins; keep the specific first.
PATTERNS: list[tuple[tuple[str, ...], str]] = [
    (("unauthorized",), "hint.unauthorized"),
    (("encod", "error"), "hint.encoder"),
    (("mediacodec",), "hint.encoder"),
    (("audio", "disabled"), "hint.audio"),
    (("audio", "capture", "fail"), "hint.audio"),
    (("output file",), "hint.record"),
    (("could not open", "record"), "hint.record"),
    (("could not create window",), "hint.window"),
    (("could not create renderer",), "hint.window"),
    (("could not find any adb device",), "hint.offline"),
    (("device", "not found"), "hint.offline"),
    (("device", "offline"), "hint.offline"),
    (("state=offline",), "hint.offline"),
]


def explain(line: str) -> str | None:
    """The i18n key of the hint for a scrcpy/adb output line, if it is a known problem."""
    text = line.lower()
    if "error" not in text and "warn" not in text and "fail" not in text:
        return None  # only look at problems: INFO lines mention devices and audio too
    for words, key in PATTERNS:
        if all(word in text for word in words):
            return key
    return None
