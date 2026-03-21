@echo off
REM Assistant d'installation complet - Pour UTILISATEURS FINAUX
REM BioAccess Secure Client Desktop v1.0
REM Installation automatique de A à Z avec suivi en direct

setlocal enabledelayedexpansion

color 0A
title BioAccess Secure - Installation [0%%]

cls
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║    🔐 BioAccess Secure - Installation Complète         ║
echo ║    Assistant Installation Utilisateur v1.0             ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo 📊 Suivi en DIRECT du processus d'installation
echo.
timeout /t 2 /nobreak >nul

REM Initialiser le compteur de progression
set TOTAL_STEPS=5
set CURRENT_STEP=0


REM ========== ÉTAPE 1: Vérifier Python ==========
set /a CURRENT_STEP=1
set /a PROGRESS=CURRENT_STEP*100/TOTAL_STEPS
title BioAccess Secure - Installation [%PROGRESS%%%]
cls
echo ╔════════════════════════════════════════════════════════╗
echo ║    🔐 BioAccess Secure - Installation Complète         ║
echo ║    Progression: [1/5]                                 ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo ┌──────────────────────────────────────────────────────┐
echo │█████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 20%%│
echo └──────────────────────────────────────────────────────┘
echo.
echo 📋 ÉTAPE 1/5: Vérification de Python
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR CRITIQUE: Python n'est pas installé
    echo.
    echo 🔧 POUR CORRIGER:
    echo    1. Allez sur https://www.python.org/downloads/
    echo    2. Télécharger Python 3.9 ou plus récent
    echo    3. 🔴 IMPORTANT: Cocher "Add Python to PATH"
    echo    4. Cliquer "Install Now"
    echo    5. Attendre la fin de l'installation
    echo    6. Relancer ce script (setup_wizard.bat)
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% trouvé
echo.
timeout /t 2 /nobreak >nul


REM ========== ÉTAPE 2: Créer environnement virtuel ==========
set /a CURRENT_STEP=2
set /a PROGRESS=CURRENT_STEP*100/TOTAL_STEPS
title BioAccess Secure - Installation [%PROGRESS%%%]
cls
echo ╔════════════════════════════════════════════════════════╗
echo ║    🔐 BioAccess Secure - Installation Complète         ║
echo ║    Progression: [2/5]                                 ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo ┌──────────────────────────────────────────────────────┐
echo │██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 40%%│
echo └──────────────────────────────────────────────────────┘
echo.
echo 📋 ÉTAPE 2/5: Configuration de l'environnement
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

echo ⏳ Étape 1/4: Vérification d'un environnement existant...
if exist venv (
    echo ⏳ Étape 2/4: Suppression de l'ancienne installation...
    rmdir /s /q venv >nul 2>&1
) else (
    echo ⏳ Étape 2/4: Aucun ancien environnement trouvé
)

echo ⏳ Étape 3/4: Création de l'environnement virtuel...
python -m venv venv >nul 2>&1
if errorlevel 1 (
    echo ❌ Erreur lors de la création de l'environnement
    pause
    exit /b 1
)

echo ⏳ Étape 4/4: Activation et mise à jour de pip...
call venv\Scripts\activate.bat >nul 2>&1
python -m pip install --upgrade pip >nul 2>&1

echo ✅ Environnement configuré avec succès
echo.
timeout /t 2 /nobreak >nul


REM ========== ÉTAPE 3: Installer dépendances ==========
set /a CURRENT_STEP=3
set /a PROGRESS=CURRENT_STEP*100/TOTAL_STEPS
title BioAccess Secure - Installation [%PROGRESS%%%]
cls
echo ╔════════════════════════════════════════════════════════╗
echo ║    🔐 BioAccess Secure - Installation Complète         ║
echo ║    Progression: [3/5]                                 ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo ┌──────────────────────────────────────────────────────┐
echo │███████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 60%%│
echo └──────────────────────────────────────────────────────┘
echo.
echo 📋 ÉTAPE 3/5: Installation des dépendances (2-3 minutes)
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo ⏳ Installation en cours:
echo.
echo    Packages à télécharger:
echo    • Pillow (interface graphique)
echo    • OpenCV (traitement d'image - ~200MB)
echo    • NumPy (calculs numériques)
echo    • Requests (communication API)
echo    • SoundDevice + SoundFile (audio)
echo    • SciPy (traitement signal)
echo    • Python-dotenv (configuration)
echo.
echo ⏳ Téléchargement et installation en cours...
echo    (cela peut prendre 2-3 minutes avec votre connexion)
echo.

pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ❌ Erreur lors de l'installation des dépendances
    echo.
    echo 💡 Solution: Vérifier votre connexion internet
    pause
    exit /b 1
)

echo ✅ Dépendances installées (environ 200-300 MB)
echo.
timeout /t 2 /nobreak >nul


REM ========== ÉTAPE 4: Compiler en .exe ==========
set /a CURRENT_STEP=4
set /a PROGRESS=CURRENT_STEP*100/TOTAL_STEPS
title BioAccess Secure - Installation [%PROGRESS%%%]
cls
echo ╔════════════════════════════════════════════════════════╗
echo ║    🔐 BioAccess Secure - Installation Complète         ║
echo ║    Progression: [4/5]                                 ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo ┌──────────────────────────────────────────────────────┐
echo │████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 80%%│
echo └──────────────────────────────────────────────────────┘
echo.
echo 📋 ÉTAPE 4/5: Création de l'exécutable (1-2 minutes)
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

echo ⏳ Étape 1/3: Installation de PyInstaller...
pip install pyinstaller^>^=5.0.0 >nul 2>&1

echo ⏳ Étape 2/3: Nettoyage des builds précédents...
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1
if exist main.spec del main.spec >nul 2>&1

echo ⏳ Étape 3/3: Compilation en cours...
echo     (cela peut prendre 1-2 minutes, soyez patient...)
echo.

pyinstaller ^
    --onefile ^
    --windowed ^
    --name "BioAccessSecure" ^
    --add-data "ui;ui" ^
    --add-data "biometric;biometric" ^
    --add-data "services;services" ^
    --hidden-import=cv2 ^
    --hidden-import=sounddevice ^
    --hidden-import=soundfile ^
    --hidden-import=scipy ^
    main.py >nul 2>&1

if not exist dist\BioAccessSecure.exe (
    echo ❌ Erreur lors de la compilation
    echo.
    echo 💡 Assurez-vous qu'aucun antivirus ne bloque le processus
    pause
    exit /b 1
)

echo ✅ Exécutable créé: BioAccessSecure.exe
echo.
timeout /t 2 /nobreak >nul


REM ========== ÉTAPE 5: Destination d'installation ==========
set /a CURRENT_STEP=5
set /a PROGRESS=CURRENT_STEP*100/TOTAL_STEPS
title BioAccess Secure - Installation [%PROGRESS%%%]
cls
echo ╔════════════════════════════════════════════════════════╗
echo ║    🔐 BioAccess Secure - Installation Complète         ║
echo ║    Progression: [5/5]                                 ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo ┌──────────────────────────────────────────────────────┐
echo │█████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░ 90%%│
echo └──────────────────────────────────────────────────────┘
echo.
echo 📋 ÉTAPE 5/5: Destination d'installation
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo Où voulez-vous installer BioAccessSecure?
echo.
echo   1 - C:\Program Files\BioAccessSecure [RECOMMANDÉ]
echo   2 - Bureau (facile d'accès)
echo   3 - Dossier personnalisé (entrez le chemin)
echo.
set /p INSTALL_CHOICE="Choisissez (1-3) [1]: "
if "%INSTALL_CHOICE%"=="" set INSTALL_CHOICE=1

if "%INSTALL_CHOICE%"=="1" (
    set "INSTALL_PATH=C:\Program Files\BioAccessSecure"
) else if "%INSTALL_CHOICE%"=="2" (
    set "INSTALL_PATH=%USERPROFILE%\Desktop\BioAccessSecure"
) else if "%INSTALL_CHOICE%"=="3" (
    echo.
    set /p INSTALL_PATH="Chemin complet: "
) else (
    set "INSTALL_PATH=C:\Program Files\BioAccessSecure"
)

echo.
echo ⏳ Création des dossiers...
if not exist "!INSTALL_PATH!" mkdir "!INSTALL_PATH!"
if not exist "!INSTALL_PATH!\logs" mkdir "!INSTALL_PATH!\logs"
if not exist "!INSTALL_PATH!\temp" mkdir "!INSTALL_PATH!\temp"

echo ⏳ Copie de l'exécutable...
copy "dist\BioAccessSecure.exe" "!INSTALL_PATH!" >nul 2>&1

echo ⏳ Copie des fichiers de configuration...
if exist ".env.example" copy ".env.example" "!INSTALL_PATH!\.env" >nul 2>&1

echo ⏳ Copie de la documentation...
if exist "README.md" copy "README.md" "!INSTALL_PATH!" >nul 2>&1
if exist "QUICKSTART.md" copy "QUICKSTART.md" "!INSTALL_PATH!" >nul 2>&1
if exist "DEBUG.md" copy "DEBUG.md" "!INSTALL_PATH!" >nul 2>&1

echo ⏳ Création du raccourci sur le Bureau...
powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut([System.Environment]::GetFolderPath('Desktop') + '\BioAccessSecure.lnk'); " ^
    "$Shortcut.TargetPath = '!INSTALL_PATH!\BioAccessSecure.exe'; " ^
    "$Shortcut.WorkingDirectory = '!INSTALL_PATH!'; " ^
    "$Shortcut.Description = 'BioAccess Secure - Authentification Biométrique'; " ^
    "$Shortcut.Save()" >nul 2>&1

echo.

cls
title BioAccess Secure - Installation [100%%]
echo ╔════════════════════════════════════════════════════════╗
echo ║    🔐 BioAccess Secure - Installation Complète         ║
echo ║    Progression: [5/5] - TERMINÉE!                     ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo ┌──────────────────────────────────────────────────────┐
echo │█████████████████████████████████████████████████ 100%%│
echo └──────────────────────────────────────────────────────┘
echo.
echo ✅ INSTALLATION 100%% RÉUSSIE!
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 📍 Emplacement d'installation: !INSTALL_PATH!
echo.
echo 🎯 PROCHAINES ÉTAPES:
echo.
echo 1️⃣  CONFIGURATION IMPORTANTE:
echo     • Ouvrir le fichier: !INSTALL_PATH!\.env
echo     • Modifier la ligne: API_BASE_URL=...
echo     • Entrer l'adresse CORRECTE de votre serveur
echo.
echo 2️⃣  DÉMARRAGE DE L'APPLICATION:
echo     • Double-cliquer "BioAccessSecure" sur le Bureau
echo     OU
echo     • Ouvrir le dossier: !INSTALL_PATH!
echo     • Double-cliquer sur BioAccessSecure.exe
echo.
echo 📚 DOCUMENTATION DISPONIBLE:
echo     • README.md - Guide complet et détaillé
echo     • QUICKSTART.md - Démarrage rapide
echo     • DEBUG.md - Résolution de problèmes
echo.
echo ═════════════════════════════════════════════════════════
echo Appuyez sur une touche pour terminer...
pause
exit /b 0
