@echo off
REM Assistant d'installation complet - Pour UTILISATEURS FINAUX
REM BioAccess Secure Client Desktop v1.0
REM Installation automatique de A à Z

setlocal enabledelayedexpansion

color 0A
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║    🔐 BioAccess Secure - Installation Complète         ║
echo ║    Assistant Installation Utilisateur v1.0             ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM ========== ÉTAPE 1: Vérifier Python ==========
echo 📋 ÉTAPE 1/5: Vérification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ❌ ERREUR: Python n'est pas installé
    echo.
    echo 🔧 Pour corriger le problème:
    echo    1. Ouvrir: https://www.python.org/downloads/
    echo    2. Télécharger Python 3.9 ou plus récent
    echo    3. IMPORTANT: Cocher "Add Python to PATH"
    echo    4. Finir l'installation
    echo    5. Relancer ce script
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% détecté
echo.

REM ========== ÉTAPE 2: Créer environnement virtuel ==========
echo 📋 ÉTAPE 2/5: Préparation de l'environnement...
if exist venv (
    echo    ⚠️  Environnement existant détecté - réinitialisation...
    rmdir /s /q venv
)
python -m venv venv >nul 2>&1
if errorlevel 1 (
    echo ❌ Erreur lors de la création de l'environnement
    pause
    exit /b 1
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
echo ✅ Environnement prêt
echo.

REM ========== ÉTAPE 3: Installer dépendances ==========
echo 📋 ÉTAPE 3/5: Installation des dépendances (2-3 minutes)...
pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ❌ Erreur lors de l'installation des dépendances
    pause
    exit /b 1
)
echo ✅ Dépendances installées
echo.

REM ========== ÉTAPE 4: Installer PyInstaller et compiler ==========
echo 📋 ÉTAPE 4/5: Création de l'exécutable (1-2 minutes)...
echo    Installation de PyInstaller...
pip install pyinstaller>=5.0.0 >nul 2>&1

REM Nettoyer anciens builds
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1
if exist main.spec del main.spec >nul 2>&1

echo    Compilation en cours...
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
    pause
    exit /b 1
)
echo ✅ Exécutable créé
echo.

REM ========== ÉTAPE 5: Demander emplacement d'installation ==========
echo 📋 ÉTAPE 5/5: Installation finale...
echo.
echo Où voulez-vous installer l'application?
echo.
echo Options:
echo   1 - C:\Program Files\BioAccessSecure (recommandé)
echo   2 - Bureau (facile d'accès)
echo   3 - Emplacement personnalisé
echo.
set /p INSTALL_CHOICE="Votre choix (1-3) [1]: "
if "%INSTALL_CHOICE%"=="" set INSTALL_CHOICE=1

if "%INSTALL_CHOICE%"=="1" (
    set "INSTALL_PATH=C:\Program Files\BioAccessSecure"
) else if "%INSTALL_CHOICE%"=="2" (
    set "INSTALL_PATH=%USERPROFILE%\Desktop\BioAccessSecure"
) else if "%INSTALL_CHOICE%"=="3" (
    echo.
    set /p INSTALL_PATH="Entrez le chemin complet: "
) else (
    set "INSTALL_PATH=C:\Program Files\BioAccessSecure"
)

REM Créer le dossier d'installation
if not exist "!INSTALL_PATH!" (
    mkdir "!INSTALL_PATH!"
)

REM Copier l'exe et les fichiers de configuration
echo Copie des fichiers...
copy "dist\BioAccessSecure.exe" "!INSTALL_PATH!" >nul 2>&1
if exist ".env.example" copy ".env.example" "!INSTALL_PATH!\.env" >nul 2>&1
if exist "README.md" copy "README.md" "!INSTALL_PATH!" >nul 2>&1
if exist "QUICKSTART.md" copy "QUICKSTART.md" "!INSTALL_PATH!" >nul 2>&1

REM Créer raccourci desktop
echo Création du raccourci...
powershell -Command ^
    "$WshShell = New-Object -ComObject WScript.Shell; " ^
    "$Shortcut = $WshShell.CreateShortcut([System.Environment]::GetFolderPath('Desktop') + '\BioAccessSecure.lnk'); " ^
    "$Shortcut.TargetPath = '!INSTALL_PATH!\BioAccessSecure.exe'; " ^
    "$Shortcut.WorkingDirectory = '!INSTALL_PATH!'; " ^
    "$Shortcut.Description = 'BioAccess Secure - Authentification Biométrique'; " ^
    "$Shortcut.Save()" >nul 2>&1

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║         ✅ Installation réussie!                      ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo 📍 Emplacement: !INSTALL_PATH!
echo.
echo 🎯 Votre application est prête!
echo.
echo 📝 Avant de lancer:
echo    1. Ouvrir: !INSTALL_PATH!\.env
echo    2. Vérifier/modifier API_BASE_URL (adresse du serveur)
echo.
echo 🚀 Pour démarrer:
echo    • Double-cliquer sur l'icône "BioAccessSecure" sur le Bureau
echo    OU
echo    • Ouvrir !INSTALL_PATH!
echo    • Double-cliquer sur BioAccessSecure.exe
echo.
echo 📚 Documentation disponible dans le dossier d'installation
echo.
echo Appuyez sur une touche pour fermer...
pause
