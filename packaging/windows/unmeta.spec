# PyInstaller spec: pyinstaller packaging/windows/unmeta.spec --noconfirm
# Output: dist/unmeta/ (unmeta.exe + _internal/, with scrcpy in _internal/vendor/scrcpy).
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

root = Path(SPECPATH).parents[1]
vendor = root / "vendor" / "scrcpy"
if not (vendor / "scrcpy.exe").is_file():
    raise SystemExit("vendor/scrcpy is empty: run packaging/windows/fetch_scrcpy.py first")

a = Analysis(
    [str(root / "packaging" / "windows" / "entry.py")],
    pathex=[str(root / "src")],
    datas=[(str(vendor), "vendor/scrcpy"), *collect_data_files("textual")],
    # Textual imports its widgets lazily, out of PyInstaller's sight.
    hiddenimports=collect_submodules("textual.widgets"),
    excludes=["tkinter"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="unmeta",
    console=True,  # terminal app
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="unmeta", upx=False)
