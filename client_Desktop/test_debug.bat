@echo on
REM VERSION DEBUG - Affiche toutes les commandes
REM Pour diagnostiquer le problème

setlocal enabledelayedexpansion

cd /d "%~dp0"
echo Répertoire courant: %cd%

echo.
echo === TEST 1: Vérifier Python ===
python --version
if errorlevel 1 (
    echo ERREUR Python !
    pause
    exit /b 1
)
echo OK Python

echo.
echo === TEST 2: Créer venv ===
if exist venv (
    echo Venv existe. Suppression...
    rmdir /s /q venv
)
python -m venv venv
if errorlevel 1 (
    echo ERREUR venv !
    pause
    exit /b 1
)
echo OK venv créé

echo.
echo === TEST 3: Activation venv ===
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERREUR activation !
    pause
    exit /b 1
)
echo OK venv activé
echo Chemin Python: %cd%\venv\Scripts\python.exe

echo.
echo === TEST 4: Vérifier pip ===
python -m pip --version
if errorlevel 1 (
    echo ERREUR pip !
    pause
    exit /b 1
)
echo OK pip

echo.
echo === TEST 5: Vérifier requirements.txt ===
if not exist requirements.txt (
    echo ERREUR: requirements.txt manquant!
    pause
    exit /b 1
)
echo OK requirements.txt existe

echo.
echo === TEST 6: Installer dépendances ===
echo Cela va prendre quelques minutes...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERREUR installation dépendances!
    pause
    exit /b 1
)
echo OK dépendances installées

echo.
echo === TEST 7: Vérifier PyInstaller ===
pip install pyinstaller
if errorlevel 1 (
    echo ERREUR installation PyInstaller!
    pause
    exit /b 1
)
echo OK PyInstaller installé

echo.
echo === TEST 8: Vérifier fichiers pour PyInstaller ===
if not exist main.py (
    echo ERREUR: main.py manquant!
    pause
    exit /b 1
)
echo OK main.py existe
if not exist ui (
    echo ERREUR: dossier ui manquant!
    pause
    exit /b 1
)
echo OK ui/ existe
if not exist biometric (
    echo ERREUR: dossier biometric manquant!
    pause
    exit /b 1
)
echo OK biometric/ existe
if not exist services (
    echo ERREUR: dossier services manquant!
    pause
    exit /b 1
)
echo OK services/ existe

echo.
echo === TEST 9: Compilation PyInstaller ===
echo Nettoyage anciens builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist main.spec del main.spec
echo Lancements PyInstaller...
pyinstaller --onefile --windowed --name "BioAccessSecure" --distpath "dist" --add-data "ui;ui" --add-data "biometric;biometric" --add-data "services;services" --hidden-import=cv2 --hidden-import=sounddevice --hidden-import=soundfile --hidden-import=scipy --hidden-import=PIL main.py
if errorlevel 1 (
    echo ERREUR compilation!
    pause
    exit /b 1
)
echo OK compilation réussie

echo.
echo === TEST 10: Vérifier exe ===
if exist dist\BioAccessSecure.exe (
    echo OK exe créé!
) else (
    echo ERREUR: exe non trouvé!
    pause
    exit /b 1
)

echo.
echo =============================
echo TOUS LES TESTS PASSÉS!
echo =============================
pause
