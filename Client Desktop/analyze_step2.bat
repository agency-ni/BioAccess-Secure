@echo off
REM ======================================================================
REM ANALYSE DETAILLEE DE L'ETAPE 2
REM ======================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
color 0B
cls

echo.
echo ======================================================================
echo ANALYSE - Variables d'environnement
echo ======================================================================
echo.

REM Afficher toutes les variables d'env pertinentes
echo [INFO] SCRIPT_DIR avant: %SCRIPT_DIR%
echo [INFO] MAIN_PY avant: %MAIN_PY%
echo.

REM Definir les chemins - copie exacte du script original
set "SCRIPT_DIR=%~dp0"
set "DIST_DIR=%SCRIPT_DIR%dist"
set "BUILD_DIR=%SCRIPT_DIR%build"
set "LOGS_DIR=%SCRIPT_DIR%logs"
set "MAIN_PY=%SCRIPT_DIR%maindesktop.py"
set "SPEC_FILE=%SCRIPT_DIR%bioaccess.spec"
set "PYTHON_CMD=python"

echo [INFO] Apres les SET
echo [INFO] SCRIPT_DIR = "%SCRIPT_DIR%"
echo [INFO] MAIN_PY = "%MAIN_PY%"
echo [INFO] SPEC_FILE = "%SPEC_FILE%"
echo.

REM Creer le dossier de logs
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"

REM Date et heure
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do set "mydate=%%c%%a%%b"
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do set "mytime=%%a%%b"
set "LOG_FILE=%LOGS_DIR%\debug_analyze_%mydate%_%mytime%.log"

echo [%date% %time%] DEBUG: Debut analyse >> "%LOG_FILE%"
echo [%date% %time%] SCRIPT_DIR="%SCRIPT_DIR%" >> "%LOG_FILE%"
echo [%date% %time%] MAIN_PY="%MAIN_PY%" >> "%LOG_FILE%"
echo.

REM ======================================================================
REM Test 1 : Verifier avec %MAIN_PY%
REM ======================================================================
echo TEST 1: if not exist "%%MAIN_PY%%" 
if not exist "%MAIN_PY%" (
    echo   RESULTAT: FICHIER INTROUVABLE
    echo [%date% %time%] TEST 1 ECHEC: %MAIN_PY% introuvable >> "%LOG_FILE%"
) else (
    echo   RESULTAT: FICHIER TROUVE
    echo [%date% %time%] TEST 1 OK: %MAIN_PY% trouve >> "%LOG_FILE%"
)
echo.

REM ======================================================================
REM Test 2 : Verifier avec delayed expansion
REM ======================================================================
echo TEST 2: if not exist "!MAIN_PY!"
if not exist "!MAIN_PY!" (
    echo   RESULTAT: FICHIER INTROUVABLE (delayed expansion)
    echo [%date% %time%] TEST 2 ECHEC: !MAIN_PY! introuvable >> "%LOG_FILE%"
) else (
    echo   RESULTAT: FICHIER TROUVE (delayed expansion)
    echo [%date% %time%] TEST 2 OK: !MAIN_PY! trouve >> "%LOG_FILE%"
)
echo.

REM ======================================================================
REM Test 3: Verifier SCRIPT_DIR meme
REM ======================================================================
echo TEST 3: Verifier que SCRIPT_DIR est correctement defini
echo [INFO] Longueur de SCRIPT_DIR: 
echo "%SCRIPT_DIR%" | find /c "Client Desktop"
echo.

REM ======================================================================
REM Test 4: Afficher le contenu de SCRIPT_DIR
REM ======================================================================
echo TEST 4: Contenu du repertoire SCRIPT_DIR
dir "%SCRIPT_DIR%" | find "maindesktop"
echo.

REM ======================================================================
REM Test 5: Test avec chemin complet hardcoded
REM ======================================================================
set "HARDCODED_PATH=c:\Users\Charbelus\Desktop\BioAccess-Secure\Client Desktop\maindesktop.py"
echo TEST 5: Avec chemin hardcode
if exist "%HARDCODED_PATH%" (
    echo   RESULTAT: FICHIER TROUVE avec chemin hardcoded
) else (
    echo   RESULTAT: FICHIER INTROUVABLE avec chemin hardcoded
)
echo.

REM ======================================================================
REM Test 6: Afficher toutes les variables
REM ======================================================================
echo TEST 6: Valeur de toutes les variables
echo DIST_DIR = "%DIST_DIR%"
echo BUILD_DIR = "%BUILD_DIR%"
echo LOGS_DIR = "%LOGS_DIR%"
echo PYTHON_CMD = "%PYTHON_CMD%"
echo.

REM ======================================================================
REM Test 7: Verifier les caracteres speciaux
REM ======================================================================
echo TEST 7: Verifier les caracteres invisibles ou speciaux
echo [DEBUG] MAIN_PY length test
"%PYTHON_CMD%" -c "s='%MAIN_PY%'; print(f'Length: {len(s)}, contains backslash: {chr(92) in s}')" 2>nul
if %errorlevel% neq 0 (
    echo   Python test failed
)
echo.

echo [%date% %time%] Analyse terminee >> "%LOG_FILE%"
echo.
echo Log sauvegarde dans: %LOG_FILE%
echo.

type "%LOG_FILE%"
echo.
pause
