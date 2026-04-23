@echo off
REM ======================================================================
REM BioAccess Secure - Installation et Compilation Automatique
REM installerdesktop_fixed.bat
REM
REM VERSION SIMPIFIEE - sans setlocal enabledelayedexpansion
REM qui causait des problemes d'expansion de variables
REM ======================================================================

chcp 65001 >nul 2>&1
color 0B
cls

REM ======================================================================
REM Definir les chemins
REM ======================================================================
set "SCRIPT_DIR=%~dp0"
set "DIST_DIR=%SCRIPT_DIR%dist"
set "BUILD_DIR=%SCRIPT_DIR%build"
set "LOGS_DIR=%SCRIPT_DIR%logs"
set "MAIN_PY=%SCRIPT_DIR%maindesktop.py"
set "SPEC_FILE=%SCRIPT_DIR%bioaccess.spec"
set "PYTHON_CMD=python"

echo.
echo ======================================================================
echo BioAccess Secure - Installation Automatique Complete
echo Un clic pour installer les dependances et compiler l'executable
echo ======================================================================
echo.

REM ======================================================================
REM Creer le dossier de logs
REM ======================================================================
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

REM Date sans caracteres speciaux pour le nom du fichier log
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set "mydate=%%c%%a%%b"
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do set "mytime=%%a%%b"
set "LOG_FILE=%LOGS_DIR%\install_%mydate%_%mytime%.log"

echo [%date% %time%] Debut installation > "%LOG_FILE%"
echo Log: %LOG_FILE%
echo.

REM ======================================================================
REM ETAPE 1/7 - VERIFICATION DE PYTHON
REM ======================================================================
echo [1/7] Verification de Python...

"%PYTHON_CMD%" --version >nul 2>&1
if %errorlevel% neq 0 (
    set "PYTHON_CMD=py"
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        color 0C
        echo.
        echo ERREUR : Python n'est pas installe ou pas dans le PATH.
        echo.
        echo Pour continuer :
        echo   1. Telechargez Python depuis : https://www.python.org/downloads/
        echo   2. Lors de l'installation, COCHEZ : "Add Python to PATH"
        echo   3. Cliquez "Install Now"
        echo   4. Redemarrez Windows
        echo   5. Relancez ce fichier .bat
        echo.
        echo [%date% %time%] ECHEC : Python introuvable >> "%LOG_FILE%"
        pause
        exit /b 1
    )
)

REM Verification version >= 3.9
"%PYTHON_CMD%" -c "import sys; exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    for /f "usebackq tokens=2" %%V in (`"%PYTHON_CMD%" --version 2^>^&1`) do set "PY_VER=%%V"
    color 0C
    echo.
    echo ERREUR : Python !PY_VER! detecte. Version 3.9 minimum requise.
    echo Telechargez Python 3.11+ : https://www.python.org/downloads/
    echo.
    echo [%date% %time%] ECHEC : Python trop ancien >> "%LOG_FILE%"
    pause
    exit /b 1
)

for /f "usebackq tokens=2" %%V in (`"%PYTHON_CMD%" --version 2^>^&1`) do set "PY_VER=%%V"
echo OK  Python %PY_VER% detecte
echo [%date% %time%] Python %PY_VER% valide >> "%LOG_FILE%"
echo.

REM ======================================================================
REM ETAPE 2/7 - VERIFICATION DES FICHIERS SOURCES
REM ======================================================================
echo [2/7] Verification des fichiers sources...

if not exist "%MAIN_PY%" (
    color 0C
    echo.
    echo ERREUR : maindesktop.py introuvable dans :
    echo   %SCRIPT_DIR%
    echo.
    echo Assurez-vous que ces fichiers sont dans le MEME dossier :
    echo   - maindesktop.py     (application principale)
    echo   - bioaccess.spec     (configuration PyInstaller)
    echo.
    echo [%date% %time%] ECHEC : maindesktop.py manquant >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo OK  maindesktop.py trouve

if not exist "%SPEC_FILE%" (
    echo AVERT  bioaccess.spec absent - compilation en mode direct
    echo [%date% %time%] AVERTISSEMENT : bioaccess.spec absent >> "%LOG_FILE%"
) else (
    echo OK  bioaccess.spec trouve
)

if exist "%SCRIPT_DIR%vosk-model" (
    echo OK  Modele Vosk detecte
) else (
    echo INFO   Modele Vosk absent - reconnaissance vocale limitee
)
echo.

REM ======================================================================
REM ETAPE 3/7 - CREATION DES DOSSIERS
REM ======================================================================
echo [3/7] Preparation des dossiers...
if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
if not exist "%DIST_DIR%"  mkdir "%DIST_DIR%"
echo OK  Dossiers prets
echo.

REM ======================================================================
REM ETAPE 4/7 - MISE A JOUR DE PIP
REM ======================================================================
echo [4/7] Mise a jour de pip...
"%PYTHON_CMD%" -m pip install --upgrade pip --quiet 2>>"%LOG_FILE%"
if %errorlevel% neq 0 (
    echo AVERT  pip n'a pas pu etre mis a jour (continuons)
) else (
    echo OK  pip a jour
)
echo.

REM ======================================================================
REM ETAPE 5/7 - INSTALLATION DES DEPENDANCES
REM ======================================================================
echo [5/7] Installation des dependances Python...
echo   (3 a 8 minutes selon votre connexion - ne fermez pas cette fenetre)
echo.

"%PYTHON_CMD%" -m pip install --upgrade setuptools wheel --quiet 2>>"%LOG_FILE%"

echo   Installation opencv-contrib-python ...
"%PYTHON_CMD%" -m pip install "opencv-contrib-python>=4.8.0" --quiet 2>>"%LOG_FILE%"
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ERREUR : opencv-contrib-python n'a pas pu etre installe.
    echo C'est une dependance critique pour la reconnaissance faciale.
    echo.
    echo Solutions :
    echo   1. Installez Visual C++ Build Tools :
    echo      https://visualstudio.microsoft.com/visual-cpp-build-tools/
    echo   2. Redemarrez et relancez installerdesktop.bat
    echo   3. Ou manuellement : python -m pip install opencv-contrib-python
    echo.
    echo [%date% %time%] ECHEC : opencv-contrib-python >> "%LOG_FILE%"
    pause
    exit /b 1
)
echo OK  opencv-contrib-python

echo   Installation numpy ...
"%PYTHON_CMD%" -m pip install "numpy>=1.24.0" --quiet 2>>"%LOG_FILE%"
if %errorlevel% neq 0 (
    echo AVERT  numpy echec
    echo [%date% %time%] AVERTISSEMENT : numpy >> "%LOG_FILE%"
) else (
    echo OK  numpy
)

echo   Installation vosk ...
"%PYTHON_CMD%" -m pip install "vosk>=0.3.45" --quiet 2>>"%LOG_FILE%"
if %errorlevel% neq 0 (
    echo AVERT  vosk echec (reconnaissance vocale indisponible)
    echo [%date% %time%] AVERTISSEMENT : vosk >> "%LOG_FILE%"
) else (
    echo OK  vosk
)

echo   Installation pyaudio ...
"%PYTHON_CMD%" -m pip install "pyaudio>=0.2.14" --quiet 2>>"%LOG_FILE%"
if %errorlevel% neq 0 (
    echo   Tentative via pipwin ...
    "%PYTHON_CMD%" -m pip install pipwin --quiet 2>>"%LOG_FILE%"
    "%PYTHON_CMD%" -m pipwin install pyaudio 2>>"%LOG_FILE%"
    if %errorlevel% neq 0 (
        echo AVERT  pyaudio non installe (micro indisponible)
        echo [%date% %time%] AVERTISSEMENT : pyaudio echec >> "%LOG_FILE%"
    ) else (
        echo OK  pyaudio (via pipwin)
    )
) else (
    echo OK  pyaudio
)

echo   Installation requests ...
"%PYTHON_CMD%" -m pip install "requests>=2.28.0" --quiet 2>>"%LOG_FILE%"
if %errorlevel% neq 0 (
    echo AVERT  requests echec
    echo [%date% %time%] AVERTISSEMENT : requests >> "%LOG_FILE%"
) else (
    echo OK  requests
)

echo   Installation cryptography pillow ...
"%PYTHON_CMD%" -m pip install cryptography pillow --quiet 2>>"%LOG_FILE%"
if %errorlevel% neq 0 (
    echo AVERT  cryptography/pillow echec
) else (
    echo OK  cryptography + pillow
)

echo.
echo OK  Toutes les dependances traitees
echo [%date% %time%] Dependances OK >> "%LOG_FILE%"
echo.

REM ======================================================================
REM ETAPE 6/7 - INSTALLATION DE PYINSTALLER
REM ======================================================================
echo [6/7] Installation de PyInstaller...

"%PYTHON_CMD%" -m pip install "pyinstaller>=6.0.0" --quiet 2>>"%LOG_FILE%"
if %errorlevel% neq 0 (
    color 0C
    echo ERREUR : Impossible d'installer PyInstaller
    echo [%date% %time%] ECHEC : PyInstaller >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo OK  PyInstaller installe
echo.

REM ======================================================================
REM ETAPE 7/7 - COMPILATION PYINSTALLER
REM ======================================================================
echo [7/7] Compilation de l'executable...
echo   (10 a 20 minutes - ne fermez pas cette fenetre)
echo.

cd /d "%SCRIPT_DIR%"

if exist "%SPEC_FILE%" (
    echo   Mode : compilation via bioaccess.spec
    echo.
    "%PYTHON_CMD%" -m PyInstaller bioaccess.spec --noconfirm --clean 2>>"%LOG_FILE%"
    set "COMPILE_OK=%errorlevel%"
) else (
    echo   Mode : compilation directe depuis maindesktop.py
    echo.
    "%PYTHON_CMD%" -c "import cv2,os; print(os.path.join(os.path.dirname(cv2.__file__),'data','haarcascade_frontalface_default.xml'))" > "%LOGS_DIR%\cv2path.tmp" 2>nul
    set /p CASCADE_SRC= < "%LOGS_DIR%\cv2path.tmp"
    del "%LOGS_DIR%\cv2path.tmp" >nul 2>&1

    "%PYTHON_CMD%" -m PyInstaller "%MAIN_PY%" --name BioAccessSecure --onefile --windowed --noconfirm --clean --add-data "%CASCADE_SRC%;cv2/data" --hidden-import cv2 --hidden-import cv2.face --hidden-import vosk --hidden-import pyaudio --hidden-import requests --hidden-import numpy --hidden-import tkinter --hidden-import tkinter.ttk --hidden-import tkinter.messagebox --hidden-import ctypes --hidden-import hashlib --hidden-import hmac --hidden-import platform --hidden-import winreg --exclude-module matplotlib --exclude-module pandas --exclude-module scipy --exclude-module IPython 2>>"%LOG_FILE%"
    set "COMPILE_OK=%errorlevel%"
)

if %COMPILE_OK% neq 0 (
    color 0C
    echo.
    echo ERREUR : La compilation a echoue (code %COMPILE_OK%).
    echo.
    echo Consultez le journal d'erreurs :
    echo   %LOG_FILE%
    echo.
    echo Causes frequentes :
    echo   1. Antivirus bloquant PyInstaller
    echo      - Desactivez temporairement l'antivirus
    echo      - Ou ajoutez une exception pour le dossier du projet
    echo.
    echo   2. Manque d'espace disque (besoin de 2 Go libres minimum)
    echo.
    echo   3. Module manquant - verifiez :
    echo      %PYTHON_CMD% -m pip install opencv-contrib-python vosk pyaudio
    echo.
    echo   4. Visual C++ Redistributable absent :
    echo      https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo.
    echo [%date% %time%] ECHEC : compilation PyInstaller code=%COMPILE_OK% >> "%LOG_FILE%"
    pause
    exit /b 1
)

echo [%date% %time%] Compilation reussie >> "%LOG_FILE%"

REM Verification que l'exe existe bien
set "EXE_PATH=%DIST_DIR%\BioAccessSecure.exe"
if not exist "%EXE_PATH%" (
    set "EXE_PATH=%DIST_DIR%\BioAccessSecure\BioAccessSecure.exe"
)

if exist "%EXE_PATH%" (
    echo.
    echo OK  Executable genere :
    echo     %EXE_PATH%
) else (
    echo.
    echo AVERT  Executable non trouve a l'emplacement attendu.
    echo        Verifiez le dossier dist\ manuellement.
)

REM ======================================================================
REM SUCCES
REM ======================================================================
color 0A
echo.
echo ======================================================================
echo SUCCES ! INSTALLATION ET COMPILATION TERMINEES
echo ======================================================================
echo.
echo   Executable genere :
echo     %DIST_DIR%\BioAccessSecure.exe
echo.
echo   UTILISATION :
echo     1. Double-cliquez sur dist\BioAccessSecure.exe
echo     2. L'application se lance directement
echo     3. Aucune installation Python necessaire sur le poste cible
echo.
echo   DISTRIBUTION :
echo     Copiez uniquement BioAccessSecure.exe
echo     (et le dossier vosk-model\ si vous utilisez la reconnaissance vocale)
echo.
echo   Journal d'installation :
echo     %LOG_FILE%
echo.
echo ======================================================================
echo.

echo [%date% %time%] Installation terminee avec succes >> "%LOG_FILE%"
pause
