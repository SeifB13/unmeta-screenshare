import json

from unmeta import config
from unmeta.config import Config, DisplaySettings, Profile


def test_round_trip(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config(language="fr", last_profile="Salon")
    cfg.profiles["Salon"] = Profile(
        name="Salon", host="192.168.1.80", serial="2G0Y", display=DisplaySettings(angle=15)
    )
    config.save(cfg, path)
    loaded = config.load(path)
    assert loaded == cfg
    assert loaded.current is not None and loaded.current.address == "192.168.1.80:5555"


def test_missing_or_broken_file_gives_empty_config(tmp_path):
    assert config.load(tmp_path / "nope.json") == Config()
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert config.load(broken) == Config()


def test_unknown_keys_and_bad_values_are_tolerated(tmp_path):
    path = tmp_path / "config.json"
    data = {
        "profiles": [
            {"name": "A", "host": "1.2.3.4", "display": {"angle": 5, "future": 1, "audio": "x"}},
            {"host": "no name"},
        ]
    }
    path.write_text(json.dumps(data), encoding="utf-8")
    cfg = config.load(path)
    assert list(cfg.profiles) == ["A"]
    assert cfg.profiles["A"].display.angle == 5
    assert cfg.profiles["A"].display.audio == "dup"


def test_current_falls_back_to_first_profile():
    cfg = Config(last_profile="gone")
    assert cfg.current is None
    cfg.profiles["A"] = Profile(name="A", host="h")
    assert cfg.current is cfg.profiles["A"]


def test_preset_scales_to_the_headset_frame():
    from unmeta.presets import PRESETS, QUEST3_FRAME

    quest3 = PRESETS["quest3"]
    assert quest3.crop_for(None) == quest3.crop_for(QUEST3_FRAME) == (1900, 1400, 100, 300)
    assert quest3.crop_for((2064, 1104)) == (950, 700, 50, 150)
    assert PRESETS["full"].crop_for((2064, 1104)) is None


def test_new_frame_rescales_a_preset_crop_but_keeps_a_tuned_one():
    p = Profile(name="Q", host="h")
    assert p.frame is None
    assert p.update_frame((4128, 2208))  # first sight, same size as the reference
    assert (p.display.crop_w, p.display.crop_x) == (1900, 100)
    assert not p.update_frame((4128, 2208))
    p.update_frame((2064, 1104))
    assert (p.display.crop_w, p.display.crop_h, p.display.crop_x) == (950, 700, 50)

    p.display.crop_x += 10  # tuned by hand
    p.update_frame((4128, 2208))
    assert p.display.crop_x == 60 and p.frame == (4128, 2208)


def test_frame_size_round_trips(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config()
    cfg.profiles["Q"] = Profile(name="Q", host="h", frame_w=4128, frame_h=2208)
    config.save(cfg, path)
    assert config.load(path).profiles["Q"].frame == (4128, 2208)
