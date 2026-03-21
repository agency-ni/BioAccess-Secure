@echo off
REM Script de compilation - Convertit l'application Python en .exe autonome
REM BioAccess Secure Client Desktop

color 0A
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║    BioAccess Secure - Compilation en .exe              ║
echo ║    (pour utilisateurs finaux - version autonome)       ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Vérifier Python
echo Vérification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou non accessible
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% trouvé
echo.

REM Vérifier venv
echo Vérification de l'environnement virtuel...
if not exist venv (
    echo ❌ Environnement virtuel non trouvé
    echo    Lancer d'abord: install.bat
    pause
    exit /b 1
)
echo ✅ Environnement virtuel trouvé
echo.

REM Activer venv
call venv\Scripts\activate.bat

REM Vérifier PyInstaller
echo Vérification de PyInstaller...
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo ❌ PyInstaller non installé
    echo    Installation...
    pip install pyinstaller>=5.0.0
    if errorlevel 1 (
        echo ❌ Erreur lors de l'installation de PyInstaller
        pause
        exit /b 1
    )
)
for /f "tokens=1" %%i in ('pyinstaller --version 2^>^&1') do set PYINST_VERSION=%%i
echo ✅ PyInstaller %PYINST_VERSION% trouvé
echo.

REM Nettoyer les anciens builds
echo Nettoyage des anciens builds...
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1
if exist main.spec del main.spec >nul 2>&1
echo ✅ Nettoyage effectué
echo.

REM Compiler avec PyInstaller
echo Compilation en cours... (cela peut prendre 1-2 minutes)
echo.

REM Créer l'exécutable avec options optimisées
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "BioAccessSecure" ^
    --icon=main.py ^
    --add-data "ui;ui" ^
    --add-data "biometric;biometric" ^
    --add-data "services;services" ^
    --add-data ".env.example;." ^
    --hidden-import=cv2 ^
    --hidden-import=sounddevice ^
    --hidden-import=soundfile ^
    --hidden-import=scipy ^
    main.py

if errorlevel 1 (
    echo.
    echo ❌ Erreur lors de la compilation
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Compilation réussie!
echo.

REM Vérifier le fichier généré
if exist dist\BioAccessSecure.exe (
    echo ╔════════════════════════════════════════════════════════╗
    echo ║          ✅ Exécutable créé avec succès!              ║
    echo ╚════════════════════════════════════════════════════════╝
    echo.
    echo 📦 Fichier généré:
    echo    %CD%\dist\BioAccessSecure.exe
    echo.
    echo 📁 Dossier contenant l'exécutable:
    echo    %CD%\dist\
    echo.
    echo 💡 Prochaines étapes:
    echo    1. Copier le dossier dist\ sur le PC de l'utilisateur
    echo    2. Double-cliquer sur BioAccessSecure.exe
    echo    3. Configurer .env (API_BASE_URL)
    echo.
) else (
    echo ❌ Fichier exécutable non trouvé après compilation
    pause
    exit /b 1
)

echo 🚀 Appuyez sur une touche pour terminer...
pause
