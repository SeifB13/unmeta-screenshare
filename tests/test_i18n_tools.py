import string

from unmeta import i18n
from unmeta.presets import PRESETS
from unmeta.tools import MIN_SCRCPY, parse_version


def _fields(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def test_french_has_every_english_key_with_same_placeholders():
    assert set(i18n.FR) == set(i18n.EN)
    for key, text in i18n.EN.items():
        assert _fields(i18n.FR[key]) == _fields(text), key


def test_every_preset_has_a_label():
    for key in PRESETS:
        assert f"preset.{key}" in i18n.EN


def test_parse_scrcpy_version():
    assert parse_version("scrcpy 5.0.1 <https://github.com/Genymobile/scrcpy>") == (5, 0, 1)
    assert parse_version("scrcpy 3.0 <https://github.com/Genymobile/scrcpy>") >= MIN_SCRCPY
    assert parse_version("scrcpy 1.25") < MIN_SCRCPY
    assert parse_version("garbage") is None
