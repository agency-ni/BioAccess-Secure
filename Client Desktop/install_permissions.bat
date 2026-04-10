@echo off
REM Script d'installation des dépendances pour BioAccess Secure
REM Windows - Configuration automatique
REM -------------------------------------------

echo.
echo ========================================================
echo  Installation - BioAccess Secure
echo  Configuration des périphériques biométriques
echo ========================================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python n'est pas installé ou n'est pas dans le PATH
    echo.
    echo Installez Python depuis: https://www.python.org/downloads/
    echo Lors de l'installation, cochez "Add Python to PATH"
    pause
    exit /b 1
)

echo ✅ Python détecté
python --version
echo.

REM Créer dossier logs
if not exist "logs" (
    mkdir logs
    echo ✅ Dossier logs créé
)

REM Installer les dépendances
echo.
echo 📦 Installation des dépendances...
echo.

python -m pip install --upgrade pip

echo.
echo 📷 Installation OpenCV...
python -m pip install opencv-python

echo.
echo 🎤 Installation sounddevice, soundfile et scipy...
python -m pip install sounddevice soundfile scipy

echo.
echo.
echo ========================================================
echo  ✅ Installation terminée!
echo ========================================================
echo.
echo Prochaines étapes:
echo.
echo 1. Lancez le diagnostic:
echo    python device_diagnostic.py
echo.
echo 2. Puis configurez les permissions:
echo    python device_setup.py
echo.
echo 3. Suivez les instructions à l'écran
echo.
pause
