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
