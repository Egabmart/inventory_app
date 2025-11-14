# -*- mode: python ; coding: utf-8 -*-

from collections.abc import Iterable
from pathlib import Path

def first_existing_path(paths: Iterable[str]) -> str | None:
    for raw_path in paths:
        path = Path(raw_path)
        if path.exists():
            return str(path)
    return None


def build_extra_data(entries: list[tuple[Iterable[str], str | None]]):
    seen_targets: set[str] = set()
    result: list[tuple[str, str]] = []
    for candidates, target in entries:
        existing = first_existing_path(candidates)
        if not existing:
            continue
        resolved_target = Path(target) if target is not None else Path(Path(existing).name)
        key = resolved_target.as_posix().lower()
        if key in seen_targets:
            continue
        seen_targets.add(key)
        result.append((existing, resolved_target.as_posix()))
    return result


extra_datas = build_extra_data([
    (['forms'], 'forms'),
    (['windows'], 'windows'),
    (['models.py'], '.'),
    (['storage.py'], '.'),
    (['forms.py'], '.'),
    (['UiNewWindow.py'], '.'),
    (['assets', 'Assets'], None),
])


icon_path = first_existing_path([
    'assets/app.icns',
    'Assets/app.icns',
    'assets/app.ico',
    'Assets/app.ico',
])

icon_path = first_existing_path([
    'assets/app.icns',
    'Assets/app.icns',
    'assets/app.ico',
    'Assets/app.ico',
])

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=extra_datas,
    hiddenimports=['html', 'PyQt6.QtPrintSupport'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='InventoryApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='InventoryApp',
)
app = BUNDLE(
    coll,
    name='InventoryApp.app',
    icon=icon_path,
    bundle_identifier=None,
)
