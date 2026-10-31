from unmeta.config import DisplaySettings
from unmeta.scrcpy import build_args, parse_texture

ADDR = "192.168.1.80:5555"


def test_default_settings_match_original_script():
    # Exact flags of legacy/Quest3-TV.bat, except that the default is now windowed.
    assert build_args(ADDR, DisplaySettings(fullscreen=True)) == [
        "-s", ADDR, "--no-control", "--max-fps=60", "--crop=1900:1400:100:300",
        "--angle=20", "--video-bit-rate=12M", "--audio-dup", "--fullscreen",
    ]  # fmt: skip


def test_audio_modes():
    assert "--no-audio" in build_args(ADDR, DisplaySettings(audio="off"))
    pc = build_args(ADDR, DisplaySettings(audio="pc"))
    assert "--no-audio" not in pc and "--audio-dup" not in pc


def test_full_frame_preset_has_no_crop_or_angle():
    s = DisplaySettings()
    s.apply_preset("full")
    args = build_args(ADDR, s)
    assert not any(a.startswith(("--crop", "--angle")) for a in args)


def test_optional_flags():
    s = DisplaySettings(always_on_top=True, max_size=1280, record_path="out.mp4")
    args = build_args(ADDR, s, window_title="Quest")
    assert "--fullscreen" not in args
    for flag in ("--always-on-top", "--max-size=1280", "--record=out.mp4", "--window-title=Quest"):
        assert flag in args


def test_parse_texture():
    assert parse_texture("INFO: Texture (D3D11VA): 1904x1408") == (1904, 1408)
    assert parse_texture("INFO: Texture: 3664x1920") == (3664, 1920)
    assert parse_texture("INFO: Renderer: direct3d11") is None
