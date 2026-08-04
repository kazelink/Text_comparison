# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\GX\\Text_comparison\\src\\main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('C:\\Users\\GX\\Text_comparison\\assets\\文档对比.ico', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['C:\\Users\\GX\\Text_comparison\\src\\hook.py'],
    excludes=[
        'unittest', 'email', 'html', 'http', 'xml', 'pydoc',
        'doctest', 'argparse', 'logging', 'pickle', 'sqlite3',
        'decimal', 'fractions', 'csv', 'configparser',
        'concurrent', 'multiprocessing', 'asyncio',
        'urllib', 'ftplib', 'imaplib', 'smtplib',
        'tarfile', 'lzma', 'bz2',
    ],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='文本校对',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\GX\\Text_comparison\\assets\\文档对比.ico'],
)
