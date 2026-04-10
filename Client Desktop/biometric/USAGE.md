# Biometric Module - Guide d'utilisation

**Version:** 2.0.0  
**Date:** Mars 2026  
**Module:** Client Desktop Biometric Integration

---

## 📋 Table des matières

1. [Installation](#installation)
2. [Architecture](#architecture)
3. [Utilisation de base](#utilisation-de-base)
4. [Services disponibles](#services-disponibles)
5. [Exemples complets](#exemples-complets)
6. [Configuration avancée](#configuration-avancée)
7. [Troubleshooting](#troubleshooting)

---

## Installation

### Prérequis

- Python 3.8+
- Caméra webcam (pour capture locale)
- Windows/Linux/macOS

### Étapes

#### 1. Installer les dépendances

```bash
cd Client\ Desktop/biometric
pip install -r requirements.txt
```

**Note Windows:** Pour compiler `dlib`, vous pouvez avoir besoin:
- Visual Studio C++ Compiler
- CMake

Alternative (utiliser binary wheel):
```bash
pip install dlib --only-binary dlib
```

#### 2. Vérifier l'installation

```python
from biometric import MUSE_AVAILABLE
print(f"MUSE disponible: {MUSE_AVAILABLE}")

# Vérifier API connectivity
from biometric import BiometricAPI
if BiometricAPI.is_healthy():
    print("✅ API BioAccess-Secure accessible")
else:
    print("❌ API unavailable - check configuration")
```

#### 3. Configurer l'API

Créer `.env` dans `Client Desktop/`:

```env
API_BASE_URL=http://localhost:5000/api/v1
API_TIMEOUT=10
VERIFY_SSL=false
```

Ou définir directement en Python:
```python
from biometric import get_api_client
client = get_api_client(api_base="http://your-server:5000/api/v1")
```

---

## Architecture

### Structure modulaire

```
biometric/
├── face_capture_service.py          # Capture locale MUSE
│   ├── LocalFaceCaptureService      # Gestion caméra + encodage
│   ├── BiometricCacheManager        # Cache persistant local
│   └── FaceDetectionResult          # Dataclass résultat
├── biometric_api_client.py          # Communication backend
│   ├── BioAccessAPIClient           # Client HTTP sécurisé
│   ├── BiometricAPI                 # Namespace simplifié
│   └── APIResponse                  # Response wrapper
├── __init__.py                      # Exports publiques
├── requirements.txt                 # Dépendances
├── CREDITS.md                       # Attributions
├── USAGE.md                         # Ce fichier
├── muse/                            # MUSE sources
│   ├── easy_facial_recognition.py
│   ├── pretrained_model/
│   │   ├── dlib_face_recognition_resnet_model_v1.dat
│   │   ├── shape_predictor_68_face_landmarks.dat
│   │   └── shape_predictor_5_face_landmarks.dat
│   └── known_faces/                 # Référence locale (optionnel)
└── cache/                           # Cache local (créé auto)
    └── biometric/
        ├── index.txt                # Index encodages
        └── *.npy                    # Encodages stockés
```

### Flux de données

```
┌─────────────────────────────────────────────────────┐
│         Client Desktop Biometric Module             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Camera → OpenCV → MUSE Encodage → Preprocessing  │
│     ↓                                    ↓         │
│  Frame Buffer               Base64 Encoding        │
│                                    ↓               │
│                    BioAccessAPIClient              │
│                         ↓                          │
│                   (HTTPS/TLS)                      │
│                         ↓                          │
│  ┌──────────────────────────────────────────┐    │
│  │     BACKEND API Routes                   │    │
│  ├──────────────────────────────────────────┤    │
│  │  /auth/face/register                     │    │
│  │  /auth/face/verify                       │    │
│  │  /auth/voice/register                    │    │
│  │  /auth/voice/verify                      │    │
│  │  /auth/liveness/detect                   │    │
│  └──────────────────────────────────────────┘    │
│           ↓                                       │
│    BiometricService (Backend)                     │
│           ↓                                       │
│    PostgreSQL Database                           │
│           ↓                                       │
│    JWT Token → Client Desktop                     │
│                                                   │
└─────────────────────────────────────────────────────┘
```

---

## Utilisation de base

### 1. Capture faciale simple

```python
from biometric import get_capture_service
import time

# Initialiser service
service = get_capture_service(camera_index=0)

# Démarrer caméra
if not service.start_camera():
    print("❌ Impossible d'accéder à la caméra")
    exit(1)

# Laisser quelques frames avant capture
time.sleep(2)

# Capturer et encoder
frame = service.capture_frame(timeout=1.0)
if frame is None:
    print("❌ Pas de frame disponible")
else:
    result = service.detect_and_encode_face(frame)
    
    if result.success:
        print(f"✅ Visage détecté")
        print(f"  - Quality score: {result.quality_score}")
        print(f"  - Landmarks: {len(result.landmarks)} points")
        print(f"  - Encoding dim: {result.face_encoding.shape}")
    else:
        print(f"❌ {result.error_message}")

# Arrêter
service.stop_camera()
```

### 2. Authentification faciale

```python
from biometric import BiometricAPI, get_capture_service
import time

# Configuration
BiometricAPI.set_base_url("http://localhost:5000/api/v1")

# Capturer visage
service = get_capture_service()
service.start_camera()
time.sleep(2)

frame = service.capture_frame()
service.stop_camera()

# Encoder en base64
image_b64 = service.encode_to_base64(frame)

# Vérifier auprès du backend
response = BiometricAPI.face_verify(
    email="user@example.com",
    image_base64=image_b64
)

if response.success:
    print(f"✅ Authentification réussie")
    print(f"  - Token: {response.data.get('token')}")
    print(f"  - Similarité: {response.data.get('similarity')}")
    print(f"  - User: {response.data.get('user')}")
    
    # Sauvegarder token
    BiometricAPI.set_token(response.data['token'])
else:
    print(f"❌ Authentification échouée: {response.error_message}")
```

### 3. Enregistrement facial

```python
from biometric import BiometricAPI, get_capture_service, get_cache_manager
import time

# Configuration
BiometricAPI.set_base_url("http://localhost:5000/api/v1")
BiometricAPI.set_token("your_auth_token")

# Capturer visage
service = get_capture_service()
service.start_camera()

print("📸 Capturez votre visage dans 3 secondes...")
time.sleep(3)

frame = service.capture_frame()
service.stop_camera()

# Encoder en base64
image_b64 = service.encode_to_base64(frame)

# Enregistrer auprès du backend
response = BiometricAPI.face_register(
    image_base64=image_b64,
    label="My Face 2024"
)

if response.success:
    print(f"✅ Visage enregistré")
    print(f"  - Template ID: {response.data.get('template_id')}")
    
    # Sauvegarder en cache local aussi
    cache = get_cache_manager()
    cache.save_encoding(
        user_id="user123",
        face_encoding=service.detect_and_encode_face(frame).face_encoding,
        label="my_face"
    )
else:
    print(f"❌ Enregistrement échoué: {response.error_message}")
```

---

## Services disponibles

### LocalFaceCaptureService

Gère la capture vidéo et l'encodage facial local.

```python
from biometric import get_capture_service

service = get_capture_service(camera_index=0)

# Interface caméra
service.start_camera()          # Démarrer capture
service.stop_camera()           # Arrêter capture
service.capture_frame()         # Récupérer frame

# Traitement
result = service.detect_and_encode_face(frame)
if result.success:
    encoding = result.face_encoding        # np.ndarray 128D
    location = result.face_location        # (top, right, bottom, left)
    landmarks = result.landmarks           # np.ndarray 68 points
    quality = result.quality_score         # 0-1 score

# Conversion
image_b64 = service.encode_to_base64(frame)
encoding_bytes = service.encode_numpy_to_bytes(encoding)
```

### BioAccessAPIClient

Communique avec le backend BioAccess-Secure.

```python
from biometric import get_api_client

client = get_api_client("http://localhost:5000/api/v1")

# Authentification
client.set_auth_token("jwt_token")
print(client.is_token_valid())      # Vérifier validité

# Face operations
response = client.face_register(image_base64, label="My Face")
response = client.face_verify("user@example.com", image_base64)

# Voice operations
response = client.voice_register(audio_base64, label="My Voice")
response = client.voice_verify("user@example.com", audio_base64)

# Liveness
response = client.liveness_detect(image_base64)

# User
response = client.get_user_profile()
response = client.update_user_profile({"first_name": "John"})

# Monitoring
response = client.get_auth_logs(limit=50)
print(client.health_check())        # API status
```

### BiometricCacheManager

Stocke et récupère les encodages en local.

```python
from biometric import get_cache_manager
import numpy as np

cache = get_cache_manager()

# Sauvegarder
cache.save_encoding(
    user_id="user123",
    face_encoding=np.random.rand(128),
    label="office_face"
)

# Charger
encoding = cache.load_encoding("user123")
if encoding is not None:
    print(f"Encoding loaded: shape {encoding.shape}")
```

### BiometricAPI (Namespace simplifié)

Accès rapide sans instanciation.

```python
from biometric import BiometricAPI

# Configuration
BiometricAPI.set_base_url("http://localhost:5000/api/v1")
BiometricAPI.set_token("jwt_token")

# Opérations
BiometricAPI.face_register(image_base64, "My Face")
BiometricAPI.face_verify("user@example.com", image_base64)
BiometricAPI.voice_register(audio_base64)
BiometricAPI.voice_verify("user@example.com", audio_base64)
BiometricAPI.liveness_check(image_base64)

# Status
if BiometricAPI.is_healthy():
    print("API en ligne ✅")
```

---

## Exemples complets

### Exemple 1: Application d'enregistrement

```python
#!/usr/bin/env python3
"""
Application d'enregistrement facial
- Capture 5 images du même utilisateur
- Vérifie qualité de chaque capture
- Enregistre auprès du backend
- Sauvegarde en cache local
"""

from biometric import (
    BiometricAPI, 
    get_capture_service, 
    get_cache_manager
)
import time

def register_user(email: str, name: str, num_captures: int = 5):
    """Enregistre un nouvel utilisateur"""
    
    # Configuration
    BiometricAPI.set_base_url("http://localhost:5000/api/v1")
    service = get_capture_service()
    cache = get_cache_manager()
    
    # Démarrer caméra
    print(f"🎬 Démarrage caméra...")
    if not service.start_camera():
        print("❌ Impossible d'accéder à la caméra")
        return False
    
    time.sleep(1)
    
    captured_encodings = []
    
    for i in range(num_captures):
        print(f"\n📸 Capture {i+1}/{num_captures}")
        print("  Position-vous face à la caméra...")
        
        time.sleep(1)
        
        frame = service.capture_frame(timeout=2)
        if frame is None:
            print("  ❌ Pas de frame disponible")
            continue
        
        result = service.detect_and_encode_face(frame)
        
        if not result.success:
            print(f"  ❌ {result.error_message}")
            continue
        
        quality = result.quality_score
        if quality < 0.4:
            print(f"  ⚠️  Qualité faible ({quality})")
            print("  Essayez avec meilleure luminosité")
            continue
        
        print(f"  ✅ Visage détecté (qualité: {quality})")
        captured_encodings.append((frame, result.face_encoding))
    
    service.stop_camera()
    
    if not captured_encodings:
        print("❌ Aucune capture valide")
        return False
    
    # Utiliser la meilleure capture (première réussie)
    best_frame, best_encoding = captured_encodings[0]
    
    # Enregistrer auprès du backend
    print(f"\n📤 Envoi vers backend...")
    image_b64 = service.encode_to_base64(best_frame)
    
    response = BiometricAPI.face_register(
        image_base64=image_b64,
        label=f"{name} - {time.strftime('%Y-%m-%d')}"
    )
    
    if response.success:
        print(f"✅ Face enregistrée")
        template_id = response.data.get('template_id')
        print(f"  - Template ID: {template_id}")
        
        # Cache local
        cache.save_encoding(
            user_id=email,
            face_encoding=best_encoding,
            label="primary"
        )
        print(f"  - Cache local: OK")
        
        return True
    else:
        print(f"❌ Enregistrement échoué: {response.error_message}")
        return False


if __name__ == "__main__":
    success = register_user(
        email="john.doe@example.com",
        name="John Doe",
        num_captures=5
    )
    
    if success:
        print("\n✅ Enregistrement réussi!")
    else:
        print("\n❌ Enregistrement échoué")
```

### Exemple 2: Application d'authentification

```python
#!/usr/bin/env python3
"""
Application d'authentification par visage
- Capture le visage utilisateur
- Envoie au backend pour vérification
- Recupère JWT token si réussie
"""

from biometric import BiometricAPI, get_capture_service
import time
import sys

def authenticate_user(email: str) -> bool:
    """Authentifie l'utilisateur par reconnaissance faciale"""
    
    BiometricAPI.set_base_url("http://localhost:5000/api/v1")
    service = get_capture_service()
    
    print(f"🔐 Authentification faciale pour: {email}")
    
    # Démarrer caméra
    if not service.start_camera():
        print("❌ Impossible d'accéder à la caméra")
        return False
    
    print("⏳ Préparation caméra (2 secondes)...")
    time.sleep(2)
    
    print("📸 Veuillez regarder vers la caméra...")
    time.sleep(1)
    
    frame = service.capture_frame(timeout=3)
    service.stop_camera()
    
    if frame is None:
        print("❌ Pas de capture disponible")
        return False
    
    # Vérifier qualité
    result = service.detect_and_encode_face(frame)
    if not result.success:
        print(f"❌ Visage non détecté: {result.error_message}")
        return False
    
    print(f"✅ Visage détecté (qualité: {result.quality_score})")
    
    # Encoder et envoyer au backend
    print("🔍 Vérification auprès du serveur...")
    image_b64 = service.encode_to_base64(frame)
    
    response = BiometricAPI.face_verify(
        email=email,
        image_base64=image_b64
    )
    
    if response.success:
        data = response.data
        print(f"✅ AUTHENTIFICATION RÉUSSIE!")
        print(f"  - Utilisateur: {data['user']['first_name']} {data['user']['last_name']}")
        print(f"  - Similarité: {data['similarity']}")
        print(f"  - Session token: {data['token'][:20]}...")
        
        # Sauvegarder token
        BiometricAPI.set_token(data['token'])
        
        return True
    else:
        print(f"❌ AUTHENTIFICATION ÉCHOUÉE")
        print(f"  Raison: {response.error_message}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        email = input("Email: ")
    else:
        email = sys.argv[1]
    
    success = authenticate_user(email)
    sys.exit(0 if success else 1)
```

---

## Configuration avancée

### Variables d'environnement

```bash
# Client Desktop/.env

# API Configuration
API_BASE_URL=http://localhost:5000/api/v1
API_TIMEOUT=10
VERIFY_SSL=true

# Camera Configuration
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=30

# Cache Configuration
CACHE_DIR=./cache/biometric
CACHE_ENCODING_FORMAT=npy

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/biometric.log
```

### Configuration Python

```python
import logging
from biometric import get_capture_service, get_api_client

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('biometric.log'),
        logging.StreamHandler()
    ]
)

# Service personnalisé
service = get_capture_service(camera_index=0)
service.timeout = 5  # Custom timeout

# Client personnalisé
client = get_api_client(
    api_base="http://production.example.com:5000/api/v1",
    timeout=15,
    verify_ssl=True
)
```

### Gestion d'erreurs robuste

```python
from biometric import BiometricAPI, APIResponse
import logging

logger = logging.getLogger(__name__)

def safe_verify(email: str, image_b64: str) -> bool:
    """Vérification faciale avec gestion d'erreurs"""
    
    try:
        # Vérifier API disponible
        if not BiometricAPI.is_healthy():
            logger.error("API server not available")
            return False
        
        # Vérifier token
        from biometric import get_api_client
        if not get_api_client().is_token_valid():
            logger.warning("Token expired, requesting new one")
            # Renouveler token...
        
        # Vérifier image
        if not image_b64 or len(image_b64) < 1000:
            logger.error("Invalid image: too small")
            return False
        
        # Authentifier
        response: APIResponse = BiometricAPI.face_verify(email, image_b64)
        
        if response.success:
            return True
        else:
            logger.warning(f"Verification failed: {response.error_message}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return False
```

---

## Troubleshooting

### Problème: `MUSE not available`

**Cause:** Dépendances non installées ou dlib compilation échoué

**Solutions:**
```bash
# 1. Réinstaller dlib
pip uninstall dlib
pip install dlib --only-binary dlib

# 2. Compiler dlib depuis source
pip install -r requirements.txt --no-cache-dir

# 3. Vérifier MUSE présent
ls Client\ Desktop/biometric/muse/
```

### Problème: Caméra pas accessible

**Cause:** Index caméra invalide ou permissions manquantes

**Solutions:**
```python
# Trouver bonne caméra
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f"✅ Caméra {i} disponible")
        cap.release()

# Linux: vérifier permissions
# sudo usermod -a -G video $USER

# Windows: vérifier paramètres vie privée > Caméra
```

### Problème: API connection refused

**Cause:** Backend non accessible

**Solutions:**
```bash
# 1. Vérifier backend lancé
curl http://localhost:5000/api/v1/health

# 2. Vérifier configuration API
python -c "from biometric import BiometricAPI; print(BiometricAPI.is_healthy())"

# 3. Vérifier firewall/proxy
```

### Problème: Visage non détecté

**Causes possibles:**
- Mauvaise luminosité
- Angle incorrect
- Visage trop petit dans frame
- Modèles dlib corrompus

**Solutions:**
```python
# Déboguer détection
from biometric import get_capture_service
import cv2

service = get_capture_service()
service.start_camera()

import time
time.sleep(2)

frame = service.capture_frame()

# Afficher qualité
result = service.detect_and_encode_face(frame)
print(f"Détecté: {result.success}")
print(f"Qualité: {result.quality_score}")
print(f"Landmarks: {result.landmarks}")

# Afficher visage détecté
if result.success:
    top, right, bottom, left = result.face_location
    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
    cv2.imshow('Face', frame)
    cv2.waitKey(0)

service.stop_camera()
```

### Problème: Performance lente

**Optimisations:**
```python
from biometric import get_capture_service

service = get_capture_service()

# Réduire résolution caméra
service.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 320)  # Au lieu de 640
service.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 240) # Au lieu de 480

# Traiter moins de frames
import time
interval = 0.5  # Traiter chaque 500ms au lieu de chaque frame
```

---

## Support

Pour questions ou problèmes:

1. Vérifier logs dans `./logs/biometric.log`
2. Consulter [Analyse MUSE](../ANALYSE_MUSE_INTEGRATION.md)
3. Voir [CREDITS.md](CREDITS.md) pour attributions
4. Repository MUSE original: https://github.com/anis-ayari/MUSE

---

**Dernière mise à jour:** Mars 2026  
**Maintaineur:** BioAccess-Secure Team
