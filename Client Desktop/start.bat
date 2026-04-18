@echo off
REM Script de vérification et démarrage du client BioAccess
chcp 65001 >nul
color 0B
cls

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                                                                  ║
echo ║         BioAccess Secure - Démarrage du Client Desktop          ║
echo ║                                                                  ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

REM Vérifier Python
echo 🔍 Vérification de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo ❌ Python n'est pas installé ou pas trouvé!
    echo.
    echo Solution:
    echo   1. Installez Python desde https://www.python.org/downloads/
    echo   2. Cochez "Add Python to PATH" pendant l'installation
    echo   3. Redémarrez votre ordinateur
    echo   4. Réexécutez ce fichier
    echo.
    pause
    exit /b 1
)
echo ✅ Python détecté
python --version
echo.

REM Vérifier dossiers
echo 🔍 Vérification de la configuration...
if not exist "logs" (
    mkdir logs
)

if not exist ".env" (
    echo ⚠️  Configuration non trouvée, création...
    (
        echo API_SERVER=http://localhost:5000
        echo API_PREFIX=/api/v1
        echo DEBUG=false
    ) > .env
    echo ✅ Configuration créée
) else (
    echo ✅ Configuration trouvée
)
echo.

REM Vérifier dépendances
echo 🔍 Vérification des dépendances...
python -c "import cv2; import sounddevice; import soundfile; import scipy" >nul 2>&1

if %errorlevel% neq 0 (
    color 0E
    echo ⚠️  Certaines dépendances manquent!
    echo.
    echo Installation automatique des dépendances...
    python -m pip install --upgrade pip >nul 2>&1
    python -m pip install opencv-python requests pyaudio sounddevice soundfile scipy pillow cryptography -q
    
    if %errorlevel% neq 0 (
        color 0C
        echo ❌ Erreur lors de l'installation des dépendances
        pause
        exit /b 1
    )
    echo ✅ Dépendances installées
) else (
    echo ✅ Toutes les dépendances sont présentes
)
echo.

REM Démarrage
color 0A
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║  ✅ Tout est prêt! Démarrage du client...                       ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

python -m biometric.examples_quickstart

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ❌ Erreur lors du démarrage de l'application
    echo Contactez le support: support@bioaccess.secure
    pause
    exit /b 1
)
