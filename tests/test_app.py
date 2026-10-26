"""Smoke tests driving the UI without a headset."""

import pytest

from unmeta import tools
from unmeta.config import Config, Profile

NO_ADB = tools.Tools(adb=None, scrcpy="scrcpy", scrcpy_version=(5, 0, 1))
ALL_TOOLS = tools.Tools(adb="adb", scrcpy="scrcpy", scrcpy_version=(5, 0, 1))


@pytest.fixture
def make_app(tmp_path, monkeypatch):
    from unmeta.app import UnMetaApp

    def make(cfg, found=ALL_TOOLS):
        monkeypatch.setattr(tools, "detect", lambda: found)
        return UnMetaApp(cfg, tmp_path / "config.json")

    return make


async def test_first_run_opens_wizard(make_app):
    from unmeta.screens.wizard import WizardScreen

    app = make_app(Config(), NO_ADB)
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, WizardScreen)
        assert app.screen.query_one("#next").disabled  # tools step: adb is missing
        app.screen.go_to("prereq")
        app.screen.query_one("#skip").press()
        await pilot.pause()
        assert app.screen.step_name == "connect"
        await pilot.press("escape")
        assert type(app.screen).__name__ == "HomeScreen"


async def test_tuning_nudges_crop_and_saves(make_app, tmp_path):
    from unmeta import config
    from unmeta.screens.tuning import TuningScreen

    cfg = Config(last_profile="Q")
    cfg.profiles["Q"] = Profile(name="Q", host="192.168.1.80")
    app = make_app(cfg)
    async with app.run_test(size=(140, 45)) as pilot:
        await pilot.pause()
        await pilot.press("d")
        assert isinstance(app.screen, TuningScreen)
        await pilot.press("right", "down", "shift+left", "plus", "plus")
        s = cfg.profiles["Q"].display
        assert (s.crop_x, s.crop_y, s.crop_w, s.angle) == (110, 310, 1890, 22)
        await pilot.press("escape")
    saved = config.load(tmp_path / "config.json")
    assert saved.profiles["Q"].display.angle == 22
