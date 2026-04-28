# Solution aux erreurs NumPy/OpenCV

## Probleme identifie

L'erreur suivante s'affiche lors du lancement :
```
AttributeError: _ARRAY_API not found
```

Cela est du à une incompatibilité entre :
- **NumPy 2.3.5** (version trop recente)
- **OpenCV** compile pour NumPy 1.x

## Solution

Executez le script de correction :

```bash
double-cliquez sur fix_numpy.bat
```

Ou manuellement en PowerShell :

```powershell
python -m pip uninstall numpy -y
python -m pip install numpy==1.26.4
```

## Verification

Verifie que cela fonctionne :

```powershell
python -c "import cv2; import numpy; print('OK!')"
```

Si vous voyez "OK!" sans erreur, c'est bon !

## Pourquoi ca arrive

OpenCV (particulierement `cv2.face` pour LBPH) est compile avec NumPy 1.x.
Quand NumPy 2.x est installe, les modules compilees pour 1.x ne sont pas compatibles.

## Autres solutions

Si le probleme persiste :

1. **Reinstaller opencv-contrib-python** :
```powershell
python -m pip uninstall opencv-contrib-python -y
python -m pip install opencv-contrib-python
```

2. **Sur Windows**, installer les dépendances Visual C++ :
- Telechargez : https://aka.ms/vs/17/release/vc_redist.x64.exe
- Installez-le
- Relancez le script ci-dessus

3. **Derniers recours** - Reinstaller entièrement :
```powershell
python -m venv venv_fresh
venv_fresh\Scripts\activate
pip install -r requirements.txt
python maindesktop.py
```
