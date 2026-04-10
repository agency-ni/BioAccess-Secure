@echo off
REM ========================================
REM Lanceur d'installation - Setup universal
REM BioAccess Secure
REM Double-cliquez sur ce fichier pour installer
REM ========================================

echo.
echo ========================================
echo  Installation - BioAccess Secure
echo ========================================
echo.

REM Verifier que Python est installe
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo.
    echo Solution:
    echo 1. Installez Python depuis: https://www.python.org/downloads/
    echo 2. IMPORTANT: Cochez "Add Python to PATH" lors de l'installation
    echo 3. Redemarrez votre ordinateur
    echo 4. Re-executez ce fichier
    echo.
    pause
    exit /b 1
)

echo [OK] Python detecte
python --version
echo.

REM Creer le dossier logs s'il n'existe pas
if not exist "logs" mkdir logs

REM Lancer le setup
echo Lancement de l'installation...
echo.

python setup.py

pause
