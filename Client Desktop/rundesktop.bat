@echo off
REM ============================================================================
REM  BioAccess Secure - Lanceur Application
REM  rundesktop.bat - Lance maindesktop.py
REM ============================================================================

setlocal enabledelayedexpansion
chcp 65001 >nul
color 0B
cls

echo.
echo ============================================================================
echo.
echo          BioAccess Secure - Client Desktop
echo                Lancement de l'application
echo.
echo ============================================================================
echo.

REM Verifier Python
echo Verification de Python...
python --version >nul 2>&1

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ERREUR : Python n'est pas installe
    echo.
    echo Veuillez d'abord lancer: installerdesktop.bat
    echo.
    pause
    exit /b 1
)

echo OK  Python disponible
echo.

REM Lancer maindesktop.py
echo Lancement de l'application...
echo.

python maindesktop.py

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ERREUR : Erreur lors du lancement
    pause
    exit /b 1
)
