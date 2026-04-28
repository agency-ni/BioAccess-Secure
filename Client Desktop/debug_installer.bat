@echo off
REM ======================================================================
REM DEBUG - Analyser l'etape 2 de l'installation
REM ======================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
color 0B
cls

echo.
echo ======================================================================
echo DEBUG - Verification des chemins et fichiers
echo ======================================================================
echo.

REM Definir les chemins
set "SCRIPT_DIR=%~dp0"
set "MAIN_PY=%SCRIPT_DIR%maindesktop.py"
set "SPEC_FILE=%SCRIPT_DIR%bioaccess.spec"

echo [DEBUG] Script directory: "%SCRIPT_DIR%"
echo [DEBUG] Script directory (no quotes): %SCRIPT_DIR%
echo.

echo [DEBUG] MAIN_PY set to: "%MAIN_PY%"
echo [DEBUG] MAIN_PY (no quotes): %MAIN_PY%
echo.

echo [DEBUG] Longueur du chemin: 
"%PYTHON_CMD%" -c "print(len(r'%MAIN_PY%'))" 2>nul

echo.
echo ======================================================================
echo Verification des fichiers
echo ======================================================================
echo.

echo [TEST 1] if exist "%MAIN_PY%"
if exist "%MAIN_PY%" (
    echo   RESULTAT: FICHIER TROUVE
    
    REM Afficher les details du fichier
    for %%F in ("%MAIN_PY%") do (
        echo   Nom: %%~nxF
        echo   Taille: %%~zF bytes
        echo   Date: %%~tF
    )
) else (
    echo   RESULTAT: FICHIER INTROUVABLE
)
echo.

echo [TEST 2] if exist "%SPEC_FILE%"
if exist "%SPEC_FILE%" (
    echo   RESULTAT: FICHIER TROUVE
    for %%F in ("%SPEC_FILE%") do (
        echo   Nom: %%~nxF
        echo   Taille: %%~zF bytes
    )
) else (
    echo   RESULTAT: FICHIER INTROUVABLE
)
echo.

echo ======================================================================
echo Listage du contenu du repertoire
echo ======================================================================
echo.

dir "%SCRIPT_DIR%" | find ".py" 
echo.

echo ======================================================================
echo Test de cd dans le repertoire
echo ======================================================================
echo.

cd /d "%SCRIPT_DIR%"
echo [DEBUG] Current directory: %CD%
echo.

if exist "maindesktop.py" (
    echo [TEST 3] FICHIER TROUVE en utilisant chemin relatif "maindesktop.py"
) else (
    echo [TEST 3] FICHIER INTROUVABLE en utilisant chemin relatif
)

if exist maindesktop.py (
    echo [TEST 4] FICHIER TROUVE sans guillemets
) else (
    echo [TEST 4] FICHIER INTROUVABLE sans guillemets
)

echo.
echo ======================================================================
echo Verification Python
echo ======================================================================
echo.

python --version 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python command not found
    py --version 2>&1
)

echo.
echo ======================================================================
echo Appuyez sur une touche pour terminer
echo ======================================================================
pause
