# Biometric Module - Index des fichiers

**Date:** 27 Mars 2026  
**Version:** 2.0.0  
**Status:** ✅ Complet

---

## 📋 Guide de navigation

### 🚀 Par où commencer?

1. **Lire d'abord:** [USAGE.md](USAGE.md) - Guide complet d'utilisation
2. **Tester:** `python examples_quickstart.py` - Demo interactive
3. **Intégrer:** Copier code des exemples dans votre application
4. **Déboguer:** Consulter [USAGE.md - Troubleshooting](USAGE.md#troubleshooting)

---

## 📁 Structure des fichiers

### Core Services

| Fichier | Purpose | Lignes |
|---------|---------|--------|
| [face_capture_service.py](face_capture_service.py) | Capture vidéo + encodage MUSE | 450+ |
| [biometric_api_client.py](biometric_api_client.py) | Client API backend | 520+ |
| [__init__.py](__init__.py) | Package initialization | 40+ |

### Documentation

| Fichier | Purpose | Public |
|---------|---------|--------|
| [USAGE.md](USAGE.md) | **← Commencer ici** | 📖 |
| [CREDITS.md](CREDITS.md) | Attribution MUSE & tiers | 📖 |
| [LICENSE.md](LICENSE.md) | Informations légales | 📖 |
| [README.md](muse/README.md) | MUSE original doc | 📖 |

### Configuration & Dépendances

| Fichier | Purpose |
|---------|---------|
| [requirements.txt](requirements.txt) | Dépendances Python |
| [.env.example](.env.example) | Variables d'environnement (template) |

### Tests & Examples

| Fichier | Purpose | Type |
|---------|---------|------|
| [test_biometric.py](test_biometric.py) | Tests unitaires | 🧪 |
| [examples_quickstart.py](examples_quickstart.py) | Demo interactive | 🎯 |

### Ressources MUSE

| Fichier | Purpose |
|---------|---------|
| [muse/easy_facial_recognition.py](muse/easy_facial_recognition.py) | Code MUSE principal |
| [muse/pretrained_model/](muse/pretrained_model/) | Modèles dlib |
| [muse/known_faces/](muse/known_faces/) | Référence visages (optionnel) |

---

## 🎯 Cas d'usage courants

### Cas 1: Je veux juste tester

```bash
# Lancer la demo
python examples_quickstart.py

# Ou directement en Python
from biometric import BiometricAPI, get_capture_service
service = get_capture_service()
service.start_camera()
# ... voir USAGE.md pour complet
```

### Cas 2: Je veux l'utiliser dans mon app

```python
# Copier depuis examples_quickstart.py
# Ou lire section "Utilisation de base" in USAGE.md
from biometric import BiometricAPI

BiometricAPI.set_base_url("http://your-backend:5000/api/v1")
# ...
```

### Cas 3: Je veux contribuer/modifier

```
1. Lire [USAGE.md - Architecture](USAGE.md#architecture)
2. Modifier les services (.py)
3. Lancer tests: `python test_biometric.py`
4. Updater docs si changements API
```

### Cas 4: J'ai une erreur

```
1. Consulter [USAGE.md - Troubleshooting](USAGE.md#troubleshooting)
2. Vérifier logs dans ./logs/biometric.log
3. Lancer examples_quickstart.py pour déboguer
```

---

## 📚 Sections dans USAGE.md

Le fichier [USAGE.md](USAGE.md) contient:

```
1. Installation (dependencies, setup, config)
2. Architecture (structure, flux données)
3. Utilisation de base (exemples simples)
4. Services disponibles (API complète)
5. Exemples complets (scripts prêts à utiliser)
6. Configuration avancée (env vars, personnalisation)
7. Troubleshooting (problèmes & solutions)
```

**Longueur:** 600+ lignes, très détaillé

---

## 🔑 Classes principales

### LocalFaceCaptureService

```python
from biometric import get_capture_service

service = get_capture_service()
service.start_camera()
frame = service.capture_frame()
result = service.detect_and_encode_face(frame)
# result.success, result.face_encoding, result.quality_score, etc
service.stop_camera()
```

### BioAccessAPIClient

```python
from biometric import get_api_client

client = get_api_client()
client.set_auth_token("jwt_token")
response = client.face_verify("user@example.com", image_b64)
# response.success, response.data, response.error_message, etc
```

### BiometricAPI (Simplifié)

```python
from biometric import BiometricAPI

BiometricAPI.set_base_url("http://localhost:5000/api/v1")
BiometricAPI.set_token("jwt_token")
response = BiometricAPI.face_verify("user@example.com", image_b64)
```

### BiometricCacheManager

```python
from biometric import get_cache_manager

cache = get_cache_manager()
cache.save_encoding("user123", encoding, "primary")
loaded = cache.load_encoding("user123")
```

---

## 🧪 Tests

### Lancer tous les tests

```bash
# Option 1
python test_biometric.py

# Option 2: avec pytest
pytest test_biometric.py -v

# Option 3: avec coverage
pytest test_biometric.py --cov=biometric
```

### Tests content

- ✅ FaceDetectionResult dataclass
- ✅ BiometricCacheManager (save/load)
- ✅ APIResponse dataclass
- ✅ BioAccessAPIClient config
- ✅ Singletons pattern
- ✅ BiometricAPI namespace

---

## 🔍 Debug

### Activer debug logging

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Voir les logs

```bash
# Fichier log (si configuré)
tail -f ./logs/biometric.log

# Ou en Python
import logging
logger = logging.getLogger('biometric')
logger.debug("Message de debug")
```

---

## 📊 Dépendances

Installer depuis `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Versions clés

```
opencv-python==4.8.1.78  # Capture vidéo
dlib==19.24.2            # Modèles reconnaissance
numpy>=1.24.0            # Calculs
requests>=2.31.0         # API HTTP
```

Autres: imutils, pillow, python-dotenv

---

## ⚙️ Configuration

### Fichier .env

Créer `Client Desktop/.env`:

```env
API_BASE_URL=http://localhost:5000/api/v1
API_TIMEOUT=10
VERIFY_SSL=false
CAMERA_INDEX=0
LOG_LEVEL=INFO
```

Voir [USAGE.md - Configuration avancée](USAGE.md#configuration-avancée) pour toutes les options.

---

## 🆘 FAQ Rapide

**Q: Comment j'utilise juste la capture, sans API?**
```python
from biometric import get_capture_service
service = get_capture_service()
# Utiliser service sans appeler BiometricAPI
```

**Q: Est-ce que je dois modifier le code MUSE?**
```
Non, il est wrapped par nos classes. Pas besoin de toucher muse/
```

**Q: Où sont stockés les encodages en cache?**
```
./cache/biometric/
Fichiers .npy + index.txt
```

**Q: Comment j'ajoute des tests?**
```
Ajouter au test_biometric.py ou créer test_*_custom.py
Heriter de unittest.TestCase
Lancer: python -m pytest
```

**Q: Comment je débogue une erreur de détection?**
```
# Voir USAGE.md - Troubleshooting
# Ou lancer examples_quickstart.py avec demo "Capture"
```

---

## 📞 Support

Pour chaque problème:

1. **Consulter:** USAGE.md
2. **Vérifier:** tests & examples
3. **Déboguer:** logs & console output
4. **Contribuer:** improvements bienvenues

Attribution & crédits:
- **MUSE:** Anis Ayari (Defend Intelligence)
- **Wrapper:** BioAccess-Secure Team

---

## 📦 Version & Release

**Module Version:** 2.0.0  
**Date Release:** 27 Mars 2026  
**Status:** ✅ Production-Ready  
**Breaking Changes:** Aucun prévu

---

## 🚀 Démarrage en 30 secondes

```bash
# 1. Installer
cd Client\ Desktop
pip install -r biometric/requirements.txt

# 2. Tester
python biometric/examples_quickstart.py

# 3. Utiliser dans votre code
from biometric import BiometricAPI, get_capture_service
# ... (voir USAGE.md)
```

---

**Fichier créé:** 27 Mars 2026  
**Dernière mise à jour:** 27 Mars 2026  
**Mainteneur:** BioAccess-Secure Team
