@echo off
echo Test de %%~dp0
echo.
echo %%~dp0 retourne : %~dp0
echo.
echo Fichier actuellement : %0
echo.
echo Repertoire courant : %CD%
echo.
echo Test 1 : Chercher maindesktop.py avec %%~dp0
if exist "%~dp0maindesktop.py" (
    echo   TROUVE
) else (
    echo   INTROUVABLE
)
echo.
echo Test 2 : Chercher maindesktop.py dans le repertoire courant
if exist "maindesktop.py" (
    echo   TROUVE
) else (
    echo   INTROUVABLE
)
echo.
echo Test 3 : Chercher avec chemin absolu
if exist "c:\Users\Charbelus\Desktop\BioAccess-Secure\Client Desktop\maindesktop.py" (
    echo   TROUVE
) else (
    echo   INTROUVABLE
)
echo.
dir "%~dp0" | find "maindesktop"
pause
