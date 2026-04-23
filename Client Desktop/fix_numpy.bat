@echo off
REM Fix numpy/opencv compatibility issue
REM This script downgrades numpy to 1.26.4 for opencv compatibility

echo Correction de l'incompatibilite NumPy/OpenCV...
echo.

python -m pip uninstall numpy -y
echo.

python -m pip install numpy==1.26.4
echo.

echo Verification...
python -c "import numpy; print('NumPy version:', numpy.__version__)"
echo.

echo Done! Vous pouvez maintenant relancer maindesktop.py
pause
