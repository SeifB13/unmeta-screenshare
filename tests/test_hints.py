import pytest

from unmeta.hints import explain
from unmeta.i18n import EN, FR


@pytest.mark.parametrize(
    ("line", "key"),
    [
        ("adb: error: device unauthorized.", "hint.unauthorized"),
        ("ERROR: Could not find any ADB device", "hint.offline"),
        ("adb: error: device '192.168.1.80:5555' not found", "hint.offline"),
        ("ERROR: Device could not be connected (state=offline)", "hint.offline"),
        ("[server] ERROR: Encoding error: android.media.MediaCodec$CodecException", "hint.encoder"),
        ("[server] WARN: Audio disabled: it is not supported before Android 11", "hint.audio"),
        ("ERROR: Failed to open output file: capture.mp4", "hint.record"),
        ("ERROR: Could not create window: No available video device", "hint.window"),
    ],
)
def test_known_problems_get_a_hint(line, key):
    assert explain(line) == key


@pytest.mark.parametrize(
    "line",
    [
        "INFO: ADB device found:",
        "INFO:     --> (tcpip)  192.168.1.194:5555   device  Quest_3",
        'Audio duplication enabled: audio source switched to "playback"',
        "[server] INFO: Device: [Oculus] oculus Quest 3 (Android 14)",
        "INFO: Texture (D3D11VA): 1904x1408",
    ],
)
def test_normal_output_gets_no_hint(line):
    assert explain(line) is None


def test_every_hint_is_translated():
    from unmeta.hints import PATTERNS

    for _, key in PATTERNS:
        assert key in EN and key in FR


async def test_hint_is_shown_once_per_stream(tmp_path, monkeypatch):
    from unmeta import tools
    from unmeta.app import UnMetaApp
    from unmeta.config import Config, Profile

    found = tools.Tools(adb="adb", scrcpy="scrcpy", scrcpy_version=(5, 0, 1))
    monkeypatch.setattr(tools, "detect", lambda: found)
    cfg = Config(last_profile="Q")
    cfg.profiles["Q"] = Profile(name="Q", host="192.168.1.80")
    app = UnMetaApp(cfg, tmp_path / "config.json")
    shown = []
    async with app.run_test() as pilot:
        monkeypatch.setattr(app, "notify", lambda message, **kw: shown.append(message))
        line = "[server] ERROR: Encoding error: android.media.MediaCodec$CodecException"
        app._scrcpy_line(line)
        app._scrcpy_line(line)
        await pilot.pause()
    assert len(shown) == 1 and "1920" in shown[0]
    assert line in app.output  # still in the log for the diagnostic report
