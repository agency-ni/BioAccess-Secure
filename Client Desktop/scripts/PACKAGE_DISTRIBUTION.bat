::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: PACKAGING SCRIPT - BioAccess Secure Distribution
:: Crée un paquet prêt à distribuer aux utilisateurs finaux
:: Fonctionne sur Windows uniquement
::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul

REM Configuration
set DIST_DIR=dist
set PACKAGE_DIR=release
set PACKAGE_NAME=BioAccess-Secure
set TIMESTAMP=%date:~6,4%-%date:~3,2%-%date:~0,2%_%time:~0,2%-%time:~3,2%

REM Nettoyage des espaces dans timestamp
set TIMESTAMP=%TIMESTAMP: =0%

title === BioAccess Secure - Packaging Distribution ===

cls
echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                  📦 PACKAGING DISTRIBUTION                         ║
echo ║              BioAccess Secure Executables                          ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.

REM Vérifier si dist/ existe
if not exist "%DIST_DIR%" (
    echo ❌ Erreur: Le dossier 'dist' n'existe pas
    echo.
    echo Vous devez d'abord compiler les exécutables:
    echo    python build_executables.py
    echo.
    pause
    exit /b 1
)

REM Vérifier les exécutables
echo Vérification des exécutables...
set EXE_COUNT=0

for %%F in (%DIST_DIR%\*.exe) do (
    echo   ✓ %%~nxF
    set /a EXE_COUNT+=1
)

if %EXE_COUNT% equ 0 (
    echo.
    echo ❌ Aucun exécutable trouvé dans '%DIST_DIR%'
    echo.
    pause
    exit /b 1
)

echo.
echo   Trouvés: %EXE_COUNT% exécutables
echo.

REM Créer le dossier release
if not exist "%PACKAGE_DIR%" mkdir "%PACKAGE_DIR%"

REM Créer les sous-dossiers
set RELEASE_VERSION=%PACKAGE_NAME%-%TIMESTAMP%
set RELEASE_PATH=%PACKAGE_DIR%\%RELEASE_VERSION%

echo Création du paquet...
echo   📁 %RELEASE_PATH%

if not exist "%RELEASE_PATH%" (
    mkdir "%RELEASE_PATH%"
)

REM Copier les exécutables
echo.
echo Copie des exécutables...
for %%F in (%DIST_DIR%\*.exe) do (
    echo   → %%~nxF
    copy "%%F" "%RELEASE_PATH%\" > nul
)

REM Créer fichier README
echo.
echo Création du fichier README...
(
    echo # BioAccess Secure
    echo.
    echo ## Installation
    echo.
    echo Double-cliquez sur **BioAccessSetup.exe** pour commencer.
    echo.
    echo ## Contenu
    echo.
    echo - **BioAccessSetup.exe** - Installation et configuration initiale
    echo - **BioAccessDiagnostic.exe** - Diagnostic des caméras et microphones
    echo - **BioAccessConfig.exe** - Configuration avancée des permissions
    echo.
    echo ## Système requis
    echo.
    echo - Windows 7 ou supérieur ^(ou Linux/macOS avec exécutables correspondants^)
    echo - Caméra web compatible
    echo - Microphone compatible
    echo - 500 MB d'espace disque libre
    echo.
    echo ## Support
    echo.
    echo Pour toute question, consultez la documentation fournie.
    echo Date de compilation: %date% %time%
) > "%RELEASE_PATH%\README.txt"

REM Créer fichier LISEZMOI version française
(
    echo # BioAccess Secure
    echo.
    echo ## Installation
    echo.
    echo Double-cliquez sur **BioAccessSetup.exe** pour commencer.
    echo.
    echo ## Contenu de ce paquet
    echo.
    echo - **BioAccessSetup.exe** - Assistant d'installation et configuration
    echo - **BioAccessDiagnostic.exe** - Diagnostic des caméras et microphones
    echo - **BioAccessConfig.exe** - Configuration avancée des permissions
    echo.
    echo ## Configuration système nécessaire
    echo.
    echo - Windows 7 ou supérieur
    echo - Une caméra web compatible
    echo - Un microphone compatible
    echo - Au minimum 500 MB d'espace disque libre
    echo.
    echo ## Support et aide
    echo.
    echo Pour toute question concernant l'installation, veuillez consulter
    echo la documentation fournie avec le logiciel.
    echo.
    echo Date de compilation: %date% %time%
) > "%RELEASE_PATH%\LISEZMOI.txt"

REM Créer info de version
(
    echo [VERSION]
    echo Product=BioAccess-Secure
    echo Version=1.0.0
    echo BuildDate=%date% %time%
    echo Executables=%EXE_COUNT%
    echo PackageName=%RELEASE_VERSION%
) > "%RELEASE_PATH%\VERSION.txt"

REM Statistiques de taille
echo.
echo Statistiques du paquet:
echo.

set TOTAL_SIZE=0

for /F "delims== tokens=*" %%A in ('dir "%RELEASE_PATH%" /s /-C ^| find "bytes"') do (
    set TOTAL_SIZE=%%A
)

REM Afficher détails des fichiers
for %%F in ("%RELEASE_PATH%\*.exe") do (
    for /F "tokens=5" %%Z in ('dir "%%F" ^| find ".exe"') do (
        set SIZE_BYTES=%%Z
        REM Convertir en MB (approximatif)
        set /a SIZE_MB=SIZE_BYTES / 1048576
        echo   %%~nxF: !SIZE_MB! MB
    )
)

REM Créer archives compressées
echo.
echo Création des archives compressées...

REM Vérifier si 7-Zip est disponible
where 7z >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo Compression avec 7-Zip...
    set ARCHIVE_7Z=%PACKAGE_DIR%\%RELEASE_VERSION%.7z
    7z a -y "!ARCHIVE_7Z!" "%RELEASE_PATH%" >nul
    if exist "!ARCHIVE_7Z!" (
        for /F "tokens=5" %%Z in ('dir "!ARCHIVE_7Z!" ^| find ".7z"') do (
            set /a SIZE_7Z=%%Z / 1048576
            echo   ✓ Créé: !ARCHIVE_7Z! ^(!SIZE_7Z! MB^)
        )
    )
)

REM Vérifier si WinRAR est disponible
where rar >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo Compression avec WinRAR...
    set ARCHIVE_RAR=%PACKAGE_DIR%\%RELEASE_VERSION%.rar
    rar a -y "!ARCHIVE_RAR!" "%RELEASE_PATH%" >nul
    if exist "!ARCHIVE_RAR!" (
        for /F "tokens=5" %%Z in ('dir "!ARCHIVE_RAR!" ^| find ".rar"') do (
            set /a SIZE_RAR=%%Z / 1048576
            echo   ✓ Créé: !ARCHIVE_RAR! ^(!SIZE_RAR! MB^)
        )
    )
)

REM ZIP avec PowerShell
echo.
echo Compression ZIP...
set ARCHIVE_ZIP=%PACKAGE_DIR%\%RELEASE_VERSION%.zip

powershell -Command "Add-Type -Assembly System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::CreateFromDirectory('%RELEASE_PATH%', '%ARCHIVE_ZIP%')" 2>nul

if exist "%ARCHIVE_ZIP%" (
    for /F "tokens=5" %%Z in ('dir "%ARCHIVE_ZIP%" ^| find ".zip"') do (
        set /a SIZE_ZIP=%%Z / 1048576
        echo   ✓ Créé: %ARCHIVE_ZIP% ^(!SIZE_ZIP! MB^)
    )
)

REM Résumé final
echo.
echo ╔════════════════════════════════════════════════════════════════════╗
echo ║                    ✅ PACKAGING RÉUSSI                            ║
echo ╚════════════════════════════════════════════════════════════════════╝
echo.
echo 📦 Paquet prêt à distribuer:
echo    %RELEASE_PATH%
echo.
echo 📁 Archives disponibles dans: %PACKAGE_DIR%
echo.
echo 📊 Contenu:
echo    • %EXE_COUNT% exécutables
echo    • Documentation (README.txt, LISEZMOI.txt)
echo    • Informations de version (VERSION.txt)
echo.
echo 🚀 Prochaines étapes:
echo    1. Télécharger les archives depuis le dossier '%PACKAGE_DIR%'
echo    2. Distribuer aux utilisateurs
echo    3. Les utilisateurs lancent BioAccessSetup.exe
echo.
echo 💡 Conseils:
echo    • Vérifier les exécutables avant distribution
echo    • Signer les .exe pour Windows ^(optionnel^)
echo    • Créer un point de restauration avant installation
echo.
echo ════════════════════════════════════════════════════════════════════
echo.

REM Demander de voir le dossier
set /p OPEN_FOLDER="Ouvrir le dossier de release? (O/N): "
if /i "%OPEN_FOLDER%"=="O" (
    start explorer "%RELEASE_PATH%"
)

exit /b 0
