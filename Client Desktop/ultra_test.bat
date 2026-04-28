@echo off

REM Test ultra-simple de la macro  

set "SCRIPT_DIR=%~dp0"
echo AVANT setlocal: SCRIPT_DIR=%SCRIPT_DIR%

setlocal enabledelayedexpansion
echo APRES setlocal: SCRIPT_DIR=%SCRIPT_DIR%
echo APRES setlocal (delayed): !SCRIPT_DIR!

set "MAIN_PY=!SCRIPT_DIR!maindesktop.py"
echo MAIN_PY defini: !MAIN_PY!

echo.
echo Test 1: if exist "!MAIN_PY!"
if exist "!MAIN_PY!" (
    echo   RESULTAT: FICHIER TROUVE
) else (
    echo   RESULTAT: FICHIER INTROUVABLE
)

echo.
echo Test 2: dir "!SCRIPT_DIR!"
dir "!SCRIPT_DIR!"

pause
