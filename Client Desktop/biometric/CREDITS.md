# Credits et Attributions

Ce projet utilise les ressources suivantes:

## MUSE (Easy Facial Recognition)

**Auteur:** Anis Ayari  
**Organisation:** Defend Intelligence  
**Repository:** MUSE (inclus dans ce projet)  
**Licence:** MIT License  
**YouTube:** https://www.youtube.com/watch?v=54WmrwVWu1w (Explication en Français)

### Composants MUSE intégrés:
- `easy_facial_recognition.py` - Script de base pour capture et reconnaissance
- Modèles dlib préentraînés:
  - `dlib_face_recognition_resnet_model_v1.dat`
  - `shape_predictor_68_face_landmarks.dat`
  - `shape_predictor_5_face_landmarks.dat`

### Utilisation:
Le module MUSE a été adapté et intégré dans le système BioAccess-Secure comme service de capture locale performant.

---

## Autres ressources

### Bibliothèques Python:

- **OpenCV** - https://opencv.org/
- **dlib** - http://dlib.net/
- **numpy** - https://numpy.org/
- **imutils** - https://github.com/jrosebr1/imutils
- **Pillow** - https://python-pillow.org/

### Modèles de détection faciale:

Les modèles dlib utilisés sont basés sur:
- ResNet pour la reconnaissance faciale
- Shape Predictor pour la détection de landmarks

---

## BioAccess-Secure

**Projet:** BioAccess-Secure - Système de contrôle d'accès biométrique  
**Version:** 2.0.0  
**Licence:** À définir par l'organisation

### Architecture:

Le wrapper biométrique intègre:
- **Services locaux** (capture, encodage) via MUSE
- **API backend** pour persistance et sécurité
- **Cache local** pour performance
- **Gestion de tokens** pour authentification

---

## Conformité Légale

Tous les composants utilisent des licences compatibles avec l'usage commercial et la modification.

✅ MIT License - MUSE
✅ Apache/BSD - OpenCV, dlib
✅ proprietary - BioAccess-Secure

Les fichiers sources incluent les en-têtes de licence appropriés.
