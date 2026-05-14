@echo off
REM ======================================================================
REM BioAccess Secure - Désinstallation avec notification backend
REM ======================================================================
chcp 65001 >nul 2>&1
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%SCRIPT_DIR%venv\Scripts\python.exe"
set "NOTIFY_SCRIPT=%SCRIPT_DIR%uninstall_notify.py"

REM Utiliser le Python du venv si disponible, sinon le Python système
if not exist "%PYTHON_EXE%" (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python introuvable. Désinstallation directe sans notification.
        goto :cleanup
    )
    set "PYTHON_EXE=python"
)

REM Lancer le script de notification (demande le mot de passe)
if exist "%NOTIFY_SCRIPT%" (
    "%PYTHON_EXE%" "%NOTIFY_SCRIPT%"
    if errorlevel 1 (
        echo Désinstallation annulée par l'utilisateur.
        pause
        exit /b 1
    )
)

:cleanup
REM Supprimer le raccourci de démarrage automatique
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "BioAccessSecure" /f >nul 2>&1

echo Désinstallation terminée.
pause
endlocal
