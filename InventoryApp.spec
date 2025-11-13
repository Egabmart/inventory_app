# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

def first_existing_path(paths: list[str]) -> str | None:
    for path in paths:
        if Path(path).exists():
            return path
    return None

extra_datas: list[tuple[str, str]] = []
for source, target in [
    ('forms', 'forms'),
    ('windows', 'windows'),
    ('models.py', '.'),
    ('storage.py', '.'),
    ('forms.py', '.'),
    ('UiNewWindow.py', '.'),
    ('assets', 'assets'),
    ('Assets', 'Assets'),
]:
    if Path(source).exists():
        extra_datas.append((source, target))

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
    hiddenimports=[],
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
