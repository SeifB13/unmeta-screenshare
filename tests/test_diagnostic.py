from unmeta import diagnostic, tools
from unmeta.config import Config, Profile

TOOLS = tools.Tools(adb="adb", scrcpy="scrcpy", scrcpy_version=(5, 0, 1))


def test_report_lists_tools_profile_headset_and_log_tail():
    profile = Profile(name="Salon", host="192.168.1.80", model="Quest 3", serial="SECRET123")
    profile.update_frame((4128, 2208))
    log = [f"line {i}" for i in range(100)]
    headset = {"state": "device", "build": "v72"}
    report = diagnostic.build_report(TOOLS, profile, headset, log)
    assert "scrcpy: scrcpy (5.0.1)" in report
    assert "Salon, 192.168.1.80:5555, model Quest 3" in report
    assert "Saved frame size: 4128x2208" in report
    assert "--crop=1900:1400:100:300" in report
    assert "Headset now: state device, build v72" in report
    assert "line 99" in report and "line 59" not in report  # last 40 lines only
    assert "SECRET123" not in report  # meant to be shared


def test_report_without_profile():
    report = diagnostic.build_report(tools.Tools(None, None, None), None, None, [])
    assert "adb: not found" in report and "no profile saved" in report and "Log: empty" in report


async def test_diagnostic_key_copies_and_saves(tmp_path, monkeypatch):
    from unmeta.app import UnMetaApp

    copied = []
    monkeypatch.setattr(tools, "detect", lambda: TOOLS)
    monkeypatch.setattr(diagnostic, "copy_to_clipboard", lambda text: copied.append(text) or True)
    monkeypatch.setattr(diagnostic, "headset_info", lambda adb, address: {"state": "offline"})
    cfg = Config(last_profile="Q")
    cfg.profiles["Q"] = Profile(name="Q", host="192.168.1.80")
    app = UnMetaApp(cfg, tmp_path / "config.json")
    async with app.run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.press("i")
        await app.workers.wait_for_complete()
        await pilot.pause()
    assert copied and "Headset now: state offline" in copied[0]
    assert (tmp_path / "diagnostic.txt").read_text(encoding="utf-8") == copied[0]
