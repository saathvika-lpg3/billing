# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

root = Path(SPECPATH).resolve()
installer_database = root / "build" / "installer_payload" / "database" / "prm_billing_inventory.db"
if not installer_database.is_file():
    raise FileNotFoundError(
        "Installer database seed is missing. Run tools/prepare_installer_database.py before PyInstaller."
    )

datas = [
    (str(root / "themes"), "themes"),
    (str(installer_database), "database"),
    (str(root / "assets"), "assets"),
    (str(root / "audit"), "audit"),
    (str(root / "docs"), "docs"),
    (str(root / "print_templates"), "print_templates"),
    (str(root / "requirements.txt"), "."),
]

a = Analysis(
    [str(root / "app.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtPrintSupport",
        "PyQt6.QtWidgets",
        "reportlab",
        "reportlab.lib",
        "reportlab.platypus",
        "cryptography",
        "cryptography.hazmat.primitives",
        "cryptography.hazmat.primitives.ciphers",
        "cryptography.hazmat.primitives.kdf.pbkdf2",
        "openpyxl",
        "pypdf",
    ],
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
    name="PRM_Billing_Inventory",
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
    icon=str(root / "assets" / "PRM_SoftSolutions.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PRM_Billing_Inventory",
)
