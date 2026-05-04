# -*- mode: python ; coding: utf-8 -*-
# bioaccess.spec — PyInstaller spec file for BioAccess Secure Desktop

import sys
import os
from pathlib import Path

block_cipher = None

# Chemins absolus basés sur l'emplacement de ce fichier .spec
SPEC_DIR = Path(__file__).parent.resolve()
BIOMETRIC_DIR = SPEC_DIR / "biometric"
UI_DIR = SPEC_DIR / "ui"
UTILS_DIR = SPEC_DIR / "utils"
SERVICES_DIR = SPEC_DIR / "services"
VOSK_MODEL_DIR = SPEC_DIR / "vosk-model"

# Tentative de récupération du dossier des données OpenCV (contient haarcascade_frontalface_default.xml)
try:
    import cv2
    CV2_DATA = os.path.join(os.path.dirname(cv2.__file__), 'data')
    if not os.path.isdir(CV2_DATA):
        CV2_DATA = None
except ImportError:
    CV2_DATA = None

# Construction de la liste des données à inclure
datas = [
    (str(BIOMETRIC_DIR), 'biometric'),
]

if UI_DIR.exists():
    datas.append((str(UI_DIR), 'ui'))
if UTILS_DIR.exists():
    datas.append((str(UTILS_DIR), 'utils'))
if SERVICES_DIR.exists():
    datas.append((str(SERVICES_DIR), 'services'))
if VOSK_MODEL_DIR.exists():
    datas.append((str(VOSK_MODEL_DIR), 'vosk-model'))

# ⚠️ CRITIQUE : Ajout du dossier de données OpenCV pour la détection de visages
if CV2_DATA:
    datas.append((CV2_DATA, 'cv2/data'))
    print(f"[SPEC] Inclut les données OpenCV depuis : {CV2_DATA}")
else:
    print("[SPEC] AVERTISSEMENT : Impossible de localiser le dossier 'cv2/data'.")

# Liste des imports cachés
hiddenimports = [
    'cv2',
    'cv2.face',
    'numpy',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'requests',
    'vosk',
    'sounddevice',
    'ctypes',
    'hashlib',
    'hmac',
    'platform',
]

if sys.platform == 'win32':
    hiddenimports.append('winreg')

excludedimports = [
    'matplotlib',
    'pandas',
    'scipy',
    'IPython',
    'jupyter',
    'notebook',
]

# === Analyse ===
a = Analysis(
    [str(SPEC_DIR / "maindesktop.py")],
    pathex=[str(SPEC_DIR), str(BIOMETRIC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludedimports=excludedimports,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# === PYZ (archive compressée) ===
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# === Exécutable ===
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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(SPEC_DIR / 'icon.ico') if (SPEC_DIR / 'icon.ico').exists() else None,
)