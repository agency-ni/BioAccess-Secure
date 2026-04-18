@echo off
chcp 65001 >nul
color 0B
cls

echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                                                                  ║
echo ║         BioAccess Secure - Installation du Client Desktop       ║
echo ║                   Installation Automatique                       ║
echo ║                                                                  ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

REM Vérifier Python
echo 📋 Étape 1: Vérification de Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ❌ ERREUR: Python n'est pas installé
    echo.
    echo Veuillez installer Python depuis: https://www.python.org/downloads/
    echo IMPORTANT: Lors de l'installation, cochez "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo ✅ Python trouvé
python --version
echo.

REM Créer dossiers nécessaires
echo 📋 Étape 2: Préparation des dossiers...
if not exist "logs" mkdir logs
if not exist ".env" (
    echo Configuration de base créée
)
echo ✅ Dossiers prêts
echo.

REM Installer dépendances
echo 📋 Étape 3: Installation des dépendances (cela peut prendre 2-3 minutes)...
echo.

python -m pip install --upgrade pip >nul 2>&1
python -m pip install opencv-python requests pyaudio sounddevice soundfile scipy pillow cryptography -q

if %errorlevel% neq 0 (
    color 0C
    echo ❌ Erreur lors de l'installation des dépendances
    echo Contactez l'administrateur: support@bioaccess.secure
    pause
    exit /b 1
)

echo ✅ Dépendances installées avec succès
echo.

REM Vérifier configuration
echo 📋 Étape 4: Configuration de base...
if not exist ".env" (
    (
        echo API_SERVER=http://localhost:5000
        echo API_PREFIX=/api/v1
        echo DEBUG=false
    ) > .env
    echo ✅ Fichier de configuration créé
) else (
    echo ✅ Configuration trouvée
)
echo.

REM Résumé
color 0A
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║                                                                  ║
echo ║  ✅ INSTALLATION RÉUSSIE                                        ║
echo ║                                                                  ║
echo ║  Prochaines étapes:                                             ║
echo ║  1. Lancez le client: python -m biometric.examples_quickstart   ║
echo ║                                                                  ║
echo ║  OU                                                              ║
echo ║                                                                  ║
echo ║  1. Double-cliquez sur l'icône BioAccess (si disponible)        ║
echo ║                                                                  ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

pause
