# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os

datas = []
binaries = []
hiddenimports = []

# اجمع بيانات pyfiglet و playwright تلقائيًا
for package in ['pyfiglet', 'playwright']:
    tmp_ret = collect_all(package)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

# أضف clients.json يدويًا
datas += [(os.path.abspath("clients.json"), "clients.json")]

# أضف quotexapi (يدويًا)
quotex_path = os.path.abspath("quotexapi")
if os.path.exists(quotex_path):
    datas.append((quotex_path, "quotexapi"))

# أضف جلسة تليجرام إذا كانت موجودة
if os.path.exists("session_name.session"):
    datas.append(("session_name.session", "."))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
