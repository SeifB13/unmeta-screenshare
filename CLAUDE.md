# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and other coding agents when working with code in this repository. Human contributors may find it a useful map too.

## Overview

UnMeta Screenshare: a cross-platform terminal app (Python + Textual) that mirrors a Meta Quest headset's view and sound to the PC over Wi-Fi by driving `adb` and `scrcpy`. It grew out of [legacy/Quest3-TV.bat](legacy/Quest3-TV.bat), kept for reference. Published on GitHub under MIT; code and README in English, [README.fr.md](README.fr.md) in French.

## Commands

```bash
# Inside the venv (.venv/bin on macOS/Linux, .venv/Scripts on Windows)
python -m venv .venv && pip install -e ".[dev]"
pytest -q                                          # all tests
pytest tests/test_adb.py -q                        # one file
ruff check . && ruff format --check .
python -m unmeta [--lang fr] [--config path]       # run the app
```

Windows build: `pip install -e ".[build]"`, `python packaging/windows/fetch_scrcpy.py` (fills `vendor/scrcpy/`), `pyinstaller packaging/windows/unmeta.spec --noconfirm`, then `iscc /DAppVersion=X.Y.Z packaging/windows/installer.iss` (Inno Setup 6; CI does it). The logo source is `assets/logo.svg`; `assets/logo.png` and `packaging/windows/unmeta.ico` (exe and installer icon) are renders of it. Releases: push a `vX.Y.Z` tag matching `__version__` in `src/unmeta/__init__.py`; `release.yml` makes a draft GitHub release.

## Architecture

- `adb.py`: subprocess wrapper plus pure parsers (`parse_devices`, `parse_ip_addr`, `parse_ip_route`, `classify_connect`) that the tests cover. `Adb._ensure_server` starts the adb daemon with DEVNULL handles first, otherwise the first captured adb call hangs on Windows.
- `scrcpy.py`: `build_args(serial, DisplaySettings)` and `ScrcpyRunner` (one child process, output/exit callbacks on a reader thread, `ADB` env var set so scrcpy uses our adb). scrcpy cannot change crop/angle/audio live, so "apply" means restart.
- `hints.py`: `explain(line)` maps known scrcpy/adb error lines to a plain-language i18n hint (`hint.*`), shown once per stream by `UnMetaApp._scrcpy_line`. Only lines with error/warn/fail are matched; add a test line for each pattern.
- `diagnostic.py`: shareable report (versions, headset props, settings, log tail; no serial) copied with the system clipboard tool and saved next to the config (`I` on home and help).
- `config.py`: `Config` → `Profile` (headset address, serial, model, raw frame size) → `DisplaySettings`, JSON in the platformdirs user config dir. Loading tolerates unknown keys and broken files.
- `presets.py`: per-model crop and angle. Only Quest 3 is verified (`1900:1400:100:300`, 20°, on its 4128x2208 frame); crop and angle depend on each other. Crops are scaled to the frame size the headset reports (`wm size`, read at each stream start and saved in the profile); `Profile.update_frame` rescales a crop still on its preset and keeps a hand-tuned one.
- `tools.py`: finds adb/scrcpy in the bundled `vendor/scrcpy` (frozen: `sys._MEIPASS/vendor/scrcpy`) then `PATH`; requires scrcpy ≥ 3.0 (`--angle`).
- `app.py` + `screens/`: `UnMetaApp` owns config, tools, `Adb`, `ScrcpyRunner`, and the `start_stream`/`stop_stream` thread workers, and `_reconnect`: a stream that ran 10 s or more and then exits on its own is restarted once the headset answers again (every 3 s, for up to 60 s; Space cancels). Screens: `home` (profile, connect, start/stop, log), `wizard` (7 steps; plug/authorize/unplug poll `adb devices` every second), `tuning` (form + `NudgePad` arrow-key panel, `FrameMap` drawing the raw frame and crop, V/F6 uncropped preview, debounced auto-apply, windowed preview), `help`.

## Conventions

- Every UI string goes through `i18n.t()` with a key in both `EN` and `FR` (a test checks key and placeholder parity). French uses proper accents.
- Call `i18n.set_language()` before importing `app`/`screens`: Textual `BINDINGS` read strings at class definition. `__main__.py` does this.
- Blocking adb/scrcpy calls run in `@work(thread=True)` workers and return to the UI with `app.call_from_thread`.
- `DisplaySettings()` defaults must keep matching `legacy/Quest3-TV.bat`, except `fullscreen` which defaults to False so the TUI stays reachable (`test_default_settings_match_original_script`).
- The GitHub account is `SeifB13` (README, pyproject, install.sh, installer.iss).
