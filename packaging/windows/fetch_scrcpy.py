"""Download the official scrcpy Windows build (it includes adb) into vendor/scrcpy.

Bump SCRCPY_VERSION and SCRCPY_SHA256 together; the hash is the one of the release zip.
"""

from __future__ import annotations

import hashlib
import io
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

SCRCPY_VERSION = "5.0.1"
SCRCPY_SHA256 = "b12a2c4ee8be317422451fc7dcf8ee20a71b5ea7ef9ad73ddd825a25316227a5"
URL = (
    "https://github.com/Genymobile/scrcpy/releases/download/"
    f"v{SCRCPY_VERSION}/scrcpy-win64-v{SCRCPY_VERSION}.zip"
)
DEST = Path(__file__).resolve().parents[2] / "vendor" / "scrcpy"


def main() -> int:
    print(f"Downloading {URL}")
    with urllib.request.urlopen(URL, timeout=120) as response:
        data = response.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != SCRCPY_SHA256:
        print(f"SHA-256 mismatch: expected {SCRCPY_SHA256}, got {digest}", file=sys.stderr)
        return 1

    shutil.rmtree(DEST, ignore_errors=True)
    DEST.mkdir(parents=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            # Drop the top-level "scrcpy-win64-vX.Y.Z/" folder.
            name = Path(member.filename).name
            (DEST / name).write_bytes(archive.read(member))
    print(f"scrcpy {SCRCPY_VERSION} extracted to {DEST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
