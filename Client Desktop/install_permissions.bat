@echo off
echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║   INSTALLATION - GESTION PERMISSIONS ET DIAGNOSTIC             ║
echo ║   BioAccess Secure - Périphériques Biométriques               ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ✗ Python n'est pas installé ou non accessible
    echo   Téléchargez depuis: https://www.python.org
    pause
    exit /b 1
)

echo ✓ Python détecté
echo.

REM Aller au dossier Client Desktop
cd /d "%~dp0Client Desktop"
if errorlevel 1 (
    echo ✗ Impossible de changer de répertoire
    pause
    exit /b 1
)

echo ✓ Dossier Client Desktop actif
echo.

REM Vérifier les packages requis
echo Vérification des packages requis...
python -m pip show opencv-python >nul 2>&1
if errorlevel 1 (
    echo ⚠ opencv-python manquant
    echo   Installation...
    python -m pip install --upgrade opencv-python
)

python -m pip show sounddevice >nul 2>&1
if errorlevel 1 (
    echo ⚠ sounddevice manquant
    echo   Installation...
    python -m pip install --upgrade sounddevice
)

python -m pip show soundfile >nul 2>&1
if errorlevel 1 (
    echo ⚠ soundfile manquant
    echo   Installation...
    python -m pip install --upgrade soundfile
)

python -m pip show scipy >nul 2>&1
if errorlevel 1 (
    echo ⚠ scipy manquant
    echo   Installation...
    python -m pip install --upgrade scipy
)

echo.
echo ✓ Tous les packages sont installés
echo.

REM Créer dossier logs
if not exist logs (
    mkdir logs
    echo ✓ Dossier logs créé
)

echo.
echo ════════════════════════════════════════════════════════════════
echo Configuration terminée avec succès!
echo.
echo Pour commencer:
echo.
echo   1. Configuration complète (recommandé):
echo      python device_setup.py
echo.
echo   2. Diagnostic uniquement:
echo      python device_diagnostic.py
echo.
echo   3. Gestionnaire de permissions:
echo      python permissions_manager.py
echo.
echo   4. Afficher le guide:
echo      python DEVICE_SETUP_GUIDE.py
echo.
echo ════════════════════════════════════════════════════════════════
echo.

pause
