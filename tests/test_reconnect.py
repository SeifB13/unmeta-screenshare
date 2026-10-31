"""Automatic reconnection when the stream drops, with fake adb and scrcpy."""

import asyncio

import pytest
from textual.worker import WorkerCancelled

from unmeta import app as app_module
from unmeta import tools
from unmeta.config import Config, Profile

TOOLS = tools.Tools(adb="adb", scrcpy="scrcpy", scrcpy_version=(5, 0, 1))


class FakeAdb:
    def __init__(self, connects_after: int) -> None:
        self.connects_after = connects_after  # connect attempts before the headset is back
        self.attempts = 0
        self.connected = False

    def state(self, address):
        return "device" if self.connected else "offline"

    def connect(self, address):
        self.attempts += 1
        self.connected = self.attempts >= self.connects_after
        return ("ok", "") if self.connected else ("unreachable", "")

    def disconnect(self, address):
        self.connected = False

    def display_size(self, address):
        return (4128, 2208)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "detect", lambda: TOOLS)
    monkeypatch.setattr(app_module, "RECONNECT_EVERY_S", 0.01)
    monkeypatch.setattr(app_module, "RECONNECT_FOR_S", 2)
    cfg = Config(last_profile="Q")
    cfg.profiles["Q"] = Profile(name="Q", host="192.168.1.80")
    app = app_module.UnMetaApp(cfg, tmp_path / "config.json")
    started = []
    monkeypatch.setattr(app.runner, "start", lambda exe, args, adb_path=None: started.append(args))
    return app, cfg.profiles["Q"], started


async def drop(app, profile, lasted: float, code: int = 2):
    """Pretend scrcpy ran for `lasted` seconds and then exited on its own."""
    app._stream = (profile, None)
    app._started_at = app_module.time.monotonic() - lasted
    await asyncio.to_thread(app._on_scrcpy_exit, code, False)


async def test_dropped_stream_reconnects(setup):
    app, profile, started = setup
    async with app.run_test() as pilot:
        app.adb = FakeAdb(connects_after=3)
        await drop(app, profile, lasted=60)
        await pilot.pause()
        await app.workers.wait_for_complete()
        assert not app.reconnecting
        assert len(started) == 1 and "192.168.1.80:5555" in started[0]
        assert app.adb.attempts == 3


async def test_stream_that_dies_at_startup_does_not_reconnect(setup):
    app, profile, started = setup
    async with app.run_test():
        app.adb = FakeAdb(connects_after=1)
        await drop(app, profile, lasted=2)
        await app.workers.wait_for_complete()
        assert not started and not app.reconnecting


async def test_closing_the_window_does_not_reconnect(setup):
    app, profile, started = setup
    async with app.run_test():
        app.adb = FakeAdb(connects_after=1)
        await drop(app, profile, lasted=60, code=0)
        await app.workers.wait_for_complete()
        assert not started and not app.reconnecting


async def test_stop_cancels_reconnection(setup):
    app, profile, started = setup
    async with app.run_test() as pilot:
        app.adb = FakeAdb(connects_after=10**6)  # never comes back
        await drop(app, profile, lasted=60)
        await pilot.pause()
        assert app.reconnecting
        app.stop_stream()
        for worker in list(app.workers):
            try:
                await worker.wait()
            except WorkerCancelled:  # the reconnection, as intended
                pass
        assert not app.reconnecting and not started


async def test_gives_up_after_the_deadline(setup, monkeypatch):
    app, profile, started = setup
    monkeypatch.setattr(app_module, "RECONNECT_FOR_S", 0.1)
    async with app.run_test():
        app.adb = FakeAdb(connects_after=10**6)
        await drop(app, profile, lasted=60)
        await app.workers.wait_for_complete()
        assert not app.reconnecting and not started
