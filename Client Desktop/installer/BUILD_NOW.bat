@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

color 0A
cls

REM Configuration
set PYTHON_CMD=python
REM Déterminer le répertoire courant
cd /d "%~dp0"

REM Banner
echo.
echo ╔════════════════════════════════════════════════════════════════════════╗
echo ║                                                                        ║
echo ║  🏗️  BIOACCESS SECURE - CONSTRUCTION EN COURS                         ║
echo ║  Construction + Packaging automatique                                 ║
echo ║                                                                        ║
echo ╚════════════════════════════════════════════════════════════════════════╝
echo.

REM Vérifier Python
echo 1️⃣  Vérification de l'environnement...
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo.
    echo ❌ ERREUR: Python n'est pas installé ou pas accessible
    echo.
    echo Solution:
    echo   1. Installer Python depuis: https://www.python.org
    echo   2. Cocher "Add Python to PATH" lors de l'installation
    echo   3. Relancer ce fichier
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do set PYTHON_VERSION=%%i
echo   ✅ %PYTHON_VERSION%

REM Vérifier les fichiers nécessaires
echo.
echo 2️⃣  Vérification des fichiers...

if not exist "quickstart_build.py" (
    color 0C
    echo   ❌ Fichier manquant: quickstart_build.py
    echo.
    pause
    exit /b 1
)
echo   ✅ quickstart_build.py trouvé

if not exist "..\device_diagnostic.py" (
    color 0C
    echo   ❌ Fichier manquant: device_diagnostic.py
    echo.
    pause
    exit /b 1
)
echo   ✅ device_diagnostic.py trouvé

if not exist "..\device_setup.py" (
    color 0C
    echo   ❌ Fichier manquant: device_setup.py
    echo.
    pause
    exit /b 1
)
echo   ✅ device_setup.py trouvé

if not exist "..\..\setup.py" (
    color 0C
    echo   ❌ Fichier manquant: setup.py
    echo.
    pause
    exit /b 1
)
echo   ✅ setup.py trouvé

REM Vérifier PyInstaller
echo.
echo 3️⃣  Vérification de PyInstaller...

%PYTHON_CMD% -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo   ⚠️  PyInstaller non installé
    echo   📥 Installation en cours...
    
    %PYTHON_CMD% -m pip install pyinstaller -q
    if errorlevel 1 (
        color 0C
        echo.
        echo   ❌ Impossible d'installer PyInstaller
        echo.
        pause
        exit /b 1
    )
    echo   ✅ PyInstaller installé
) else (
    echo   ✅ PyInstaller disponible
)

REM Lancer la compilation
echo.
echo ════════════════════════════════════════════════════════════════════════
echo  🚀 DÉMARRAGE DE LA CONSTRUCTION
echo ════════════════════════════════════════════════════════════════════════
echo.
echo Cela peut prendre 15-25 minutes selon votre système...
echo Veuillez patienter, traitement en cours...
echo.

REM Lancer quickstart_build.py avec affichage direct
%PYTHON_CMD% quickstart_build.py
set BUILD_STATUS=%errorlevel%

echo.
echo ════════════════════════════════════════════════════════════════════════

if %BUILD_STATUS% equ 0 (
    color 0B
    echo.
    echo ╔════════════════════════════════════════════════════════════════════════╗
    echo ║                                                                        ║
    echo ║  ✅ SUCCÈS! APPLICATION CONSTRUITE ET EMBALLÉE                        ║
    echo ║                                                                        ║
    echo ╚════════════════════════════════════════════════════════════════════════╝
    echo.
    echo 📁 FICHIERS CRÉÉS:
    echo.
    echo   Exécutables:
    if exist "..\..\dist\BioAccessSetup.exe" (
        echo   ✓ dist\BioAccessSetup.exe
    )
    if exist "..\..\dist\BioAccessDiagnostic.exe" (
        echo   ✓ dist\BioAccessDiagnostic.exe
    )
    if exist "..\..\dist\BioAccessConfig.exe" (
        echo   ✓ dist\BioAccessConfig.exe
    )
    echo.
    echo   Paquets Distribution:
    if exist "..\..\release" (
        for /F "tokens=*" %%A in ('dir ..\..\release /b /s /a-d 2^>nul ^| findstr /E "\.zip$ \.7z$"') do (
            echo   ✓ %%~nxA
        )
    )
    echo.
    echo ════════════════════════════════════════════════════════════════════════
    echo.
    echo 🚀 PROCHAINES ÉTAPES:
    echo.
    echo   1. Ouvrir le dossier: release\
    echo   2. Télécharger l'archive ZIP ou 7Z
    echo   3. Partager avec les utilisateurs
    echo   4. Les utilisateurs lancent: BioAccessSetup.exe
    echo.
    echo 💡 CONSEIL:
    echo   • Utilisez le fichier .7z ^(plus petit^)
    echo   • Ou le fichier .zip ^(plus compatible^)
    echo.
    set /p OPEN_FOLDER="Ouvrir le dossier release maintenant? (o/n): "
    if /i "!OPEN_FOLDER!"=="o" (
        start explorer "..\..\release"
    )
) else (
    color 0C
    echo.
    echo ╔════════════════════════════════════════════════════════════════════════╗
    echo ║                                                                        ║
    echo ║  ❌ ERREUR LORS DE LA CONSTRUCTION                                    ║
    echo ║                                                                        ║
    echo ╚════════════════════════════════════════════════════════════════════════╝
    echo.
    echo 📋 DÉPANNAGE:
    echo.
    echo   1. Vérifiez que Python est correctement installé
    echo   2. Tentez manuelle:
    echo      python quickstart_build.py
    echo   3. Si erreur persiste, essayez:
    echo      python build_executables_advanced.py --verbose
    echo.
)

echo.
echo Appuyez sur une touche pour terminer...
pause >nul
exit /b %BUILD_STATUS%
