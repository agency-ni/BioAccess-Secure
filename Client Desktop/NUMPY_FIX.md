# Solution aux erreurs NumPy/OpenCV

## Statut: RÉSOLU

Le problème d'incompatibilité NumPy/OpenCV a été résolu avec les versions récentes:
- **NumPy 2.4.3** (compatible avec Python 3.14)
- **OpenCV 4.13.0** (fonctionne avec NumPy 2.x)

## Ancien problème (obsolète)

L'erreur suivante s'affichait avec les anciennes versions :
```
AttributeError: _ARRAY_API not found
```

Cela était dû à une incompatibilité entre :
- **NumPy 2.3.5** (version trop récente à l'époque)
- **OpenCV** compilé pour NumPy 1.x

## Solution actuelle

Les versions récentes sont automatiquement compatibles. Si vous rencontrez des problèmes d'installation, assurez-vous d'utiliser Python 3.11+.

## Vérification

Vérifiez que cela fonctionne :

```powershell
python -c "import cv2; import numpy; print('NumPy:', numpy.__version__); print('OpenCV:', cv2.__version__)"
```

Si vous voyez les versions sans erreur, c'est bon !
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
