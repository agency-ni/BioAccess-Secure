@echo off
REM Script d'installation pour développeurs
REM BioAccess Secure Client Desktop

color 0A
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║     BioAccess Secure - Installation Développeur        ║
echo ║     Client Desktop v1.0                                ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo 💡 TIP: Pour une installation COMPLÈTE (utilisateurs finals)
echo    Lancer plutôt: setup_wizard.bat
echo.
pause
echo.

REM Vérifier Python
echo Vérification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé ou non accessible
    echo.
    echo Télécharger Python depuis: https://www.python.org/downloads/
    echo Attention: Cocher "Add Python to PATH" lors de l'installation!
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% trouvé
echo.

REM Créer venv
echo Création de l'environnement virtuel...
if exist venv (
    echo    Environnement existant détecté
    set /p RESPONSE="   Réinitialiser? (y/n) [n]: "
    if /I "%RESPONSE%"=="y" (
        rmdir /s /q venv
        python -m venv venv
    )
) else (
    python -m venv venv
)
echo ✅ Environnement virtuel créé
echo.

REM Activer venv
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo ✅ Environnement activé
echo.

REM Mettre à jour pip
echo Mise à jour de pip...
python -m pip install --upgrade pip >nul 2>&1
echo ✅ Pip mis à jour
echo.

REM Installer requirements
echo Installation des dépendances essentielles...
echo (cela peut prendre 2-3 minutes...)
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Erreur lors de l'installation des dépendances essentielles
    pause
    exit /b 1
)
echo.
echo ✅ Dépendances essentielles installées
echo.

REM Installer dépendances optionnelles
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║   Installation des dépendances optionnelles?           ║
echo ║   (reconnaissance faciale avancée, ML)                 ║
echo ╚════════════════════════════════════════════════════════╝
echo.
set /p INSTALL_OPTIONAL="Installer les dépendances optionnelles? (y/n) [n]: "
if /I "%INSTALL_OPTIONAL%"=="y" (
    echo.
    echo Installation des packages optionnels...
    pip install -r requirements-optional.txt
    if errorlevel 1 (
        echo ⚠️  Avertissement: Installation des dépendances optionnelles échouée
        echo    L'application fonctionnera normalement sans ces packages
        echo.
    ) else (
        echo ✅ Dépendances optionnelles installées
        echo.
    )
) else (
    echo ⏭️  Dépendances optionnelles ignorées
    echo    (L'application fonctionnera sans ces packages)
    echo.
)

REM Créer .env
if not exist .env (
    if exist .env.example (
        copy .env.example .env
        echo ✅ Fichier .env créé
    )
)
echo.

REM Créer répertoires
if not exist logs mkdir logs
if not exist temp mkdir temp
echo ✅ Répertoires créés
echo.

echo ╔════════════════════════════════════════════════════════╗
echo ║              ✅ Installation réussie!                 ║
echo ╚════════════════════════════════════════════════════════╝
echo.
echo 📝 Prochaines étapes:
echo.
echo 1️⃣  Éditer la configuration:
echo    • Ouvrir le fichier .env
echo    • Vérifier API_BASE_URL pour votre serveur
echo.
echo 2️⃣  Démarrer le serveur backend (PowerShell/CMD séparé):
echo    cd ..\BACKEND
echo    python run.py
echo.
echo 3️⃣  Lancer l'application:
echo    python main.py
echo.
echo 🎯 Options avancées:
echo    • Compiler en .exe: build.bat
echo    • Installation complète: setup_wizard.bat
echo.
echo 📚 Documentation:
echo    • INSTALLATION.txt: Guide d'installation complet
echo    • README.md: Documentation complète
echo    • DEBUG.md: Dépannage des problèmes
echo.
echo 🚀 Appuyez sur une touche pour terminer...
pause
