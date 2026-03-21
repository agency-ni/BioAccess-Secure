# -*- mode: python ; coding: utf-8 -*-
"""
Configuration PyInstaller pour BioAccess Secure Client Desktop
Compile l'application Python en exécutable Windows autonome
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('ui', 'ui'),
        ('biometric', 'biometric'),
        ('services', 'services'),
        ('config.py', '.'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'cv2',
        'sounddevice',
        'soundfile',
        'scipy',
        'scipy.signal',
        'numpy',
        'requests',
        'PIL',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BioAccessSecure',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
