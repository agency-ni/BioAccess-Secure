# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for BioAccess Secure Setup
Créé pour Client Desktop/installer/ location
"""

from pathlib import Path
import sys

# Determine project root (relative to this spec file location)
spec_dir = Path(__file__).parent.absolute()
if spec_dir.name == 'installer':
    project_root = spec_dir.parent.parent
else:
    project_root = Path.cwd()

# Key paths
setup_script = project_root / 'setup.py'
logs_dir = project_root / 'logs'
build_dir = project_root / 'build'
dist_dir = project_root / 'dist'

# Block list - modules to exclude
hiddenimports = [
    'pkg_resources',
    'setuptools',
    'six',
    'distutils',
    'certifi',
]

excludedimports = [
    'matplotlib',
    'numpy',
    'scipy',
    'pandas',
    'PIL',
    'cv2',
    'sklearn',
    'tensorflow',
    'torch',
]

a = Analysis(
    [str(setup_script)],
    pathex=[str(project_root), str(project_root / 'BACKEND')],
    binaries=[],
    datas=[
        (str(project_root / 'FRONTEND'), 'frontend'),
        (str(project_root / 'BACKEND'), 'backend'),
        (str(logs_dir), 'logs'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=excludedimports,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BioAccessSetup',
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

# Optional: Create Windows installer with NSIS
# coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, upx_exclude=[], name='BioAccessSetup')
