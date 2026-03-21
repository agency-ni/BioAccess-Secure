@echo off
REM Point d'entrée unique pour tous les utilisateurs
REM BioAccess Secure - Écran de bienvenue

color 0A
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║         🔐 BioAccess Secure - Installation             ║
echo ║         Authentification Biométrique v1.0              ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo 👋 Bienvenue! Qui êtes-vous?
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo   1️⃣   JE SUIS UN UTILISATEUR FINAL
echo        (Je veux installer et utiliser l'application)
echo        ➜ Installation automatique complète (recommandé)
echo.
echo   2️⃣   JE SUIS UN DÉVELOPPEUR
echo        (Je veux développer et modifier le code)
echo        ➜ Installation mode développement
echo.
echo   3️⃣   JE VEUX COMPILER EN .EXE AUTONOME
echo        (Créer un fichier exécutable à distribuer)
echo        ➜ Compilation avec PyInstaller
echo.
echo   4️⃣   LIRE LA DOCUMENTATION
echo        (Guide d'installation détaillé)
echo        ➜ Ouvrir INSTALLATION.txt
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
set /p CHOIX="Votre choix (1-4): "

if "%CHOIX%"=="1" (
    echo.
    echo ✅ Lancement de l'installation pour utilisateurs finaux...
    echo.
    call setup_wizard.bat
) else if "%CHOIX%"=="2" (
    echo.
    echo ✅ Lancement de l'installation développeur...
    echo.
    call install.bat
) else if "%CHOIX%"=="3" (
    echo.
    echo ✅ Lancement de la compilation...
    echo.
    call build.bat
) else if "%CHOIX%"=="4" (
    echo.
    echo ✅ Ouverture de la documentation...
    echo.
    start INSTALLATION.txt
    echo.
    echo 📖 Documentation ouverte dans le bloc-notes
    echo.
    pause
) else (
    echo.
    echo ❌ Choix invalide
    echo.
    pause
    goto :start
)

:end
