@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo.
echo ========================================
echo  BioAccess Secure - Installation Simple
echo ========================================
echo.

REM Test Python
echo [1/5] Vérification Python...
python --version
if errorlevel 1 (
    color 0c
    echo ERREUR: Python non trouvé!
    pause
    exit /b 1
)
color 0a
echo OK Python
pause

REM Créer venv
echo.
echo [2/5] Création environnement virtuel...
if exist venv (
    echo Suppression venv existant...
    rmdir /s /q venv
)
python -m venv venv
if errorlevel 1 (
    color 0c
    echo ERREUR: Impossible de créer venv!
    pause
    exit /b 1
)
color 0a
echo OK venv créé
pause

REM Activer venv
echo.
echo [3/5] Installation dépendances...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    color 0c
    echo ERREUR: Installation dépendances échouée!
    pause
    exit /b 1
)
color 0a
echo OK Dépendances installées
pause

REM Installer PyInstaller
echo.
echo Vérification PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    color 0c
    echo ERREUR: Impossible d'installer PyInstaller!
    pause
    exit /b 1
)
color 0a

REM Compilation
echo.
echo [4/5] Compilation PyInstaller (cela peut prendre 2-3 minutes)...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist main.spec del main.spec

pyinstaller --onefile --windowed --name "BioAccessSecure" ^
    --distpath "dist" ^
    --add-data "ui;ui" ^
    --add-data "biometric;biometric" ^
    --add-data "services;services" ^
    --hidden-import=cv2 ^
    --hidden-import=sounddevice ^
    --hidden-import=soundfile ^
    --hidden-import=scipy ^
    --hidden-import=PIL ^
    main.py

if errorlevel 1 (
    color 0c
    echo ERREUR: Compilation échouée!
    echo Vérifiez les messages ci-dessus
    pause
    exit /b 1
)

if not exist dist\BioAccessSecure.exe (
    color 0c
    echo ERREUR: exe non créé!
    pause
    exit /b 1
)

color 0a
echo OK Compilation réussie!
pause

REM Résumé
echo.
echo [5/5] Installation terminée!
echo.
echo Fichier: %cd%\dist\BioAccessSecure.exe
echo Taille: 
dir dist\BioAccessSecure.exe
echo.
color 0a
echo Succès!
color 07
pause
