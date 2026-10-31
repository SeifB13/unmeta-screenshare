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


def test_frame_map_draws_crop_on_frame():
    from unmeta.screens.tuning import frame_map

    rows = frame_map((400, 200), (100, 100, 50, 50), cols=40)
    assert len(rows) == 10 and all(len(r) == 40 for r in rows)
    assert "!" not in "".join(rows)
    assert rows[0] == "." * 20 + "|" + "." * 19  # top line: frame only, eye divider
    assert rows[2][5:15] == "#" * 10 and rows[4][6:14] == "o" * 8


def test_frame_map_flags_crop_outside_frame():
    from unmeta.screens.tuning import frame_map

    rows = frame_map((400, 200), (100, 100, 350, 150), cols=45)
    assert "!" in "".join(rows)  # crop sticks out right and bottom: the map grows to show it


async def test_tuning_full_view_streams_raw_frame(make_app, monkeypatch):
    from unmeta.adb import Adb
    from unmeta.screens.tuning import TuningScreen

    headset_size = [None]  # not connected yet
    monkeypatch.setattr(Adb, "display_size", lambda self, serial: headset_size[0])

    cfg = Config(last_profile="Q")
    cfg.profiles["Q"] = Profile(name="Q", host="192.168.1.80")
    app = make_app(cfg)
    started = []
    monkeypatch.setattr(app, "start_stream", lambda profile, s=None: started.append(s))
    async with app.run_test(size=(140, 50)) as pilot:
        await pilot.pause()
        await pilot.press("d")
        screen = app.screen
        assert isinstance(screen, TuningScreen)
        await pilot.press("v")
        await pilot.pause()
        assert started and not started[-1].crop_enabled and started[-1].angle == 0
        assert cfg.profiles["Q"].display.crop_enabled  # saved settings keep the crop
        app.append_output("INFO: Texture (D3D11VA): 1920x1026")
        await pilot.pause()
        assert screen.frame == (1920, 1026)  # fallback while the headset gives no size
        headset_size[0] = (4128, 2208)
        app.append_output("INFO: Texture (D3D11VA): 1920x1026")  # scaled down by scrcpy
        await app.workers.wait_for_complete()
        await pilot.pause()
        assert screen.frame == (4128, 2208)  # the headset's own size wins
        assert cfg.profiles["Q"].frame == (4128, 2208)  # remembered for next time
        app.append_output("INFO: Texture (D3D11VA): 1920x1026")
        assert screen.frame == (4128, 2208)
        await pilot.press("ctrl+right")
        assert cfg.profiles["Q"].display.crop_x == 150
