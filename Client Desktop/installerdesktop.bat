@echo off
REM ======================================================================
REM BioAccess Secure - Installation PRO v3.4 (STABLE)
REM ======================================================================

chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
color 0A
cls

REM ===== CONFIGURATION =====
set "SCRIPT_DIR=%~dp0"
set "LOG_FILE=%SCRIPT_DIR%install.log"
set "VENV_DIR=%SCRIPT_DIR%venv"
set "DIST_DIR=%SCRIPT_DIR%dist"
set "MAIN_PY=%SCRIPT_DIR%maindesktop.py"
set "VOSK_MODEL_DIR=%SCRIPT_DIR%vosk-model-small-fr-0.22"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "PYINSTALLER_EXE=%VENV_DIR%\Scripts\pyinstaller.exe"
set "XML_FILE=%SCRIPT_DIR%haarcascade_frontalface_default.xml"


echo [INFO] START %date% %time% > "%LOG_FILE%"

REM ===== 1. VALIDATION PRÉALABLE =====
if not exist "%MAIN_PY%" (
    echo ❌ ERREUR : %MAIN_PY% est introuvable.
    echo [ERROR] Main script missing >> "%LOG_FILE%"
    pause
    exit /b 1
)

where python >nul 2>&1 || (
    echo ❌ ERREUR : Python n'est pas dans le PATH.
    pause
    exit /b 1
)

REM ===== 2. EXÉCUTION DU FLUX =====
call :progress 1 "Initialisation de l'environnement..."
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%" >> "%LOG_FILE%" 2>&1
    if !errorlevel! neq 0 (
        echo ❌ ERREUR : Impossible de créer l'environnement virtuel.
        pause
        exit /b 1
    )
)

call :progress 2 "Mise à jour de PIP et outils..."
"%PYTHON_EXE%" -m pip install --upgrade pip wheel setuptools >> "%LOG_FILE%" 2>&1

call :progress 3 "Installation des dépendances (OpenCV, Vosk)..."
:: On verrouille les versions pour éviter les ruptures futures
"%PYTHON_EXE%" -m pip install ^
opencv-contrib-python==4.10.0.84 ^
numpy==1.26.4 ^
vosk==0.3.45 ^
requests cryptography pillow tqdm pyinstaller >> "%LOG_FILE%" 2>&1

call :progress 4 "Récupération du modèle vocal (Vosk)..."
if not exist "%VOSK_MODEL_DIR%\am" (
    call :DownloadVosk || (echo ❌ Échec Vosk >> "%LOG_FILE%" & exit /b 1)
)

call :progress 5 "Configuration des ressources binaires..."

:: Tentative 1 : Extraction dynamique (corrigée)
for /f "delims=" %%i in ('"%PYTHON_EXE%" -c "import cv2,os; print(os.path.join(os.path.dirname(cv2.__file__), 'data'))" 2^>nul') do set "CV2_DATA_PATH=%%i"

:: Tentative 2 : Si la 1 a échoué, on force le chemin relatif au VENV
if "!CV2_DATA_PATH!"=="" (
    set "CV2_DATA_PATH=%VENV_DIR%\Lib\site-packages\cv2\data"
    echo [INFO] Utilisation du chemin statique : !CV2_DATA_PATH! >> "%LOG_FILE%"
)

:: Vérification physique : Si le dossier n'existe vraiment pas, on alerte
if not exist "!CV2_DATA_PATH!" (
    echo ❌ ERREUR : Le dossier data d'OpenCV est introuvable dans le VENV.
    echo [ERROR] OpenCV data folder missing at !CV2_DATA_PATH! >> "%LOG_FILE%"
    pause
    exit /b 1
)

call :progress 6 "Nettoyage des anciens builds..."
if exist "%DIST_DIR%" (
    rmdir /s /q "%DIST_DIR%" >> "%LOG_FILE%" 2>&1
    if !errorlevel! neq 0 (
        echo [WARN] Impossible de supprimer l'ancien build, tentative de suppression complète >> "%LOG_FILE%"
        timeout /t 2 /nobreak >nul
        rmdir /s /q "%DIST_DIR%" >> "%LOG_FILE%" 2>&1
    )
)

call :progress 7 "Compilation BioAccessSecure..."

"%SCRIPT_DIR%venv\Scripts\pyinstaller.exe" --noconfirm --clean --onefile --windowed --name "BioAccessSecure" --add-data "%VOSK_MODEL_DIR%;model" --add-data "%SCRIPT_DIR%haarcascade_frontalface_default.xml;." --collect-all vosk --hidden-import=cv2 "%MAIN_PY%" >> "%LOG_FILE%" 2>&1

REM ===== FIN =====
cls
echo ╔════════════════════════════════════════════╗
echo ║             INSTALLATION TERMINÉE          ║
echo ╚════════════════════════════════════════════╝
echo Localisation : %DIST_DIR%\BioAccessSecure\
pause
exit /b 0

REM ======================================================================
REM FONCTIONS
REM ======================================================================

:progress
set "BAR="
for /l %%A in (1,1,30) do (
    if %%A lss !BAR_COUNT! (set "BAR=!BAR!█") else (set "BAR=!BAR! ")
)
cls
echo.
echo ╔════════════════════════════════════════════╗
echo ║   BIOACCESS SECURE INSTALL v3.4            ║
echo ╠════════════════════════════════════════════╣
echo ║ [!BAR!] !PERCENT!%% ║
echo ╚════════════════════════════════════════════╝
echo.
echo Statut : %~2
echo.
exit /b

:DownloadVosk
echo [INFO] Téléchargement du modèle... >> "%LOG_FILE%"
for /f "delims=" %%A in ('cd') do set "PWD=%%A"
powershell -ExecutionPolicy Bypass -NoProfile -Command "Set-Location '%SCRIPT_DIR%'; $url='https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip'; $out='model.zip'; $tmp='tmp_model'; $dst='%VOSK_MODEL_DIR%'; try { Invoke-WebRequest -Uri $url -OutFile $out -ErrorAction Stop; Expand-Archive -Path $out -DestinationPath $tmp -Force -ErrorAction Stop; if (!(Test-Path $dst)) { New-Item -ItemType Directory -Path $dst -Force | Out-Null }; $dir=@(Get-ChildItem -Path $tmp -Directory -ErrorAction Stop)[0]; if ($dir) { Get-ChildItem -Path $dir.FullName -Recurse | Move-Item -Destination $dst -Force -ErrorAction Continue }; Remove-Item -Path $out -Force -ErrorAction Continue; Remove-Item -Path $tmp -Recurse -Force -ErrorAction Continue; exit 0 } catch { exit 1 }"
exit /b %errorlevel%
