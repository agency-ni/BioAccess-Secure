# 🔐 BioAccess Secure - Client Desktop

Application desktop d'authentification biométrique multi-modale (visage + voix) pour le système BioAccess Secure.

## 📋 Caractéristiques

✅ **Reconnaissance faciale** - Détection et capture via OpenCV  
✅ **Reconnaissance vocale** - Enregistrement et traitement audio  
✅ **Interface Tkinter fluide** - Threading pour éviter blocages UI  
✅ **Affichage caméra temps réel** - Prévisualisation directe  
✅ **Gestion des tentatives** - Limite de 3 tentatives avec cooldown  
✅ **Logs complets** - Traçabilité complète des opérations  
✅ **Sécurité minimale** - Validation serveur, timeouts, clé API  

## 🚀 Installation

### Prérequis

- **Python 3.8+**
- **Caméra USB** disponible
- **Microphone** disponible
- **Connexion réseau** vers le serveur API

### 1. Cloner le projet

```bash
cd "Client Desktop"
```

### 2. Créer un environnement virtuel (optionnel mais recommandé)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

#### Dépendances principales:

| Package | Utilité |
|---------|---------|
| `opencv-python` | Capture caméra et traitement d'image |
| `sounddevice` + `soundfile` | Enregistrement et traitement audio |
| `requests` | Communication HTTP avec l'API |
| `Pillow` | Traitement d'image pour l'affichage UI |
| `numpy` | Opérations numériques |
| `python-dotenv` | Gestion des variables d'environnement |

### 4. Configurer l'application

Créer un fichier `.env`:

```bash
cp .env.example .env
```

Éditer `.env` et configurer:

```env
API_BASE_URL=http://localhost:5000/api/v1
API_KEY=your-api-key-here
CAMERA_ID=0
AUDIO_SAMPLE_RATE=44100
```

## ▶️ Utilisation

### Lancer l'application

```bash
python main.py
```

### Flux d'utilisation

1. **Authentification par visage** (par défaut):
   - Cliquer sur "📸 Scanner Visage"
   - Se positionner devant la caméra
   - L'app capture le visage automatiquement
   - Envoi au serveur pour vérification

2. **Fallback vocal**:
   - Si le visage échoue, cliquer "🎤 Utiliser la Voix"
   - Enregistrement pendant 5 secondes
   - Envoi de l'audio au serveur

3. **Gestion des tentatives**:
   - Maximum 3 tentatives
   - Après 3 échecs → blocage de 5 minutes
   - Affichage du statut en temps réel

## 📁 Structure du projet

```
Client Desktop/
├── main.py                    # Point d'entrée
├── config.py                  # Configuration centralisée
├── requirements.txt           # Dépendances
├── .env.example               # Exemple de configuration
├── README.md                  # Cette documentation
│
├── ui/
│   ├── __init__.py
│   └── login_screen.py        # Interface Tkinter principale
│
├── biometric/
│   ├── __init__.py
│   ├── face.py                # Module reconnaissance faciale (OpenCV)
│   └── voice.py               # Module reconnaissance vocale (audio)
│
├── services/
│   ├── __init__.py
│   └── api_client.py          # Client HTTP pour communiquer avec l'API
│
└── logs/
    └── app.log                # Fichier de log généré à l'exécution
```

## 🔌 Endpoints API attendus

L'application communique avec le serveur via ces endpoints:

### Authentification

**Face:**
```
POST /api/v1/auth/face
Content-Type: application/json

{
    "face_image": "base64_encoded_image",
    "timestamp": "2024-03-21T15:30:00"
}
```

**Réponse:**
```json
{
    "status": "success" | "fail",
    "user": "john.doe",
    "confidence": 0.95,
    "message": "Authentification réussie"
}
```

**Voice:**
```
POST /api/v1/auth/voice
Content-Type: application/json

{
    "voice_audio": "base64_encoded_wav",
    "timestamp": "2024-03-21T15:30:00"
}
```

### Health Check

```
GET /api/v1/health
```

## 🎨 Personnalisation

### Modifier les couleurs

Dans `config.py`:

```python
THEME_COLOR = '#2C3E50'      # Couleur principale
ACCENT_COLOR = '#27AE60'     # Couleur d'accentuation
ERROR_COLOR = '#E74C3C'      # Couleur d'erreur
```

### Modifier les timeouts

```python
FACE_SCAN_TIMEOUT = 30        # Durée max scan visage (sec)
AUDIO_DURATION = 5            # Durée enregistrement (sec)
MAX_ATTEMPTS = 3              # Tentatives max
ATTEMPT_TIMEOUT = 300         # Cooldown après échecs (sec)
```

### Modifier la caméra

```python
CAMERA_ID = 0                 # ID caméra (0=par défaut)
CAMERA_WIDTH = 640            # Résolution
CAMERA_HEIGHT = 480
CAMERA_FPS = 30
```

## 📊 Logging

Les logs sont stockés dans `logs/app.log` avec:
- **Timestamp** - Horodatage précis
- **Module** - Composant concerné
- **Niveau** - DEBUG, INFO, WARNING, ERROR
- **Message** - Description détaillée

Exemple:
```
2024-03-21 15:30:45,123 - biometric.face - INFO - ✓ Face recognizer initialisé
2024-03-21 15:30:46,456 - ui.login_screen - INFO - 📸 Lancement du scan facial...
```

## 🔒 Sécurité

L'application implémente:

✅ **Clé API** - Authentification auprès du serveur (header `X-API-Key`)  
✅ **Timeouts** - Prévention des requêtes traînantes (défaut: 10s)  
✅ **Validation** - Vérification des réponses serveur avant utilisation  
✅ **Logs audit** - Traçabilité de toutes les opérations  
✅ **Blocage après tentatives** - Protection contre bruteforce  

## 🐛 Dépannage

### "Impossible d'accéder à la caméra"

**Solutions:**
- Vérifier que la caméra est connectée
- Vérifier les permissions d'accès
- Modifier `CAMERA_ID` dans `.env` si plusieurs caméras
- Redémarrer l'application

### "Aucun périphérique audio"

**Solutions:**
- Vérifier que le microphone est connecté
- Vérifier les permissions audio du système
- Sur Linux: `sudo usermod -a -G audio $USER`

### "API non accessible"

**Solutions:**
- Vérifier que le serveur Flask est en cours d'exécution
- Vérifier l'URL dans `API_BASE_URL`
- Vérifier la connectivité réseau
- Vérifier la clé API dans `.env`

### "ImportError: No module named..."

**Solution:**
```bash
pip install -r requirements.txt
```

## 💡 Cas d'usage avancés

### Utiliser une webcam réseau

Modifier `config.py`:
```python
CAMERA_ID = "rtsp://camera_ip:554/stream"
```

### Enregistrement automatique des tentatives

Les logs complets sont dans `logs/app.log` pour audit.

### Intégration LDAP/AD

Modifier `services/api_client.py` pour ajouter des endpoints custom.

## 📝 API de développement

### Module FaceRecognizer

```python
from biometric.face import face_recognizer

# Démarrer caméra
cap = face_recognizer.start_camera()

# Lire une frame
frame = face_recognizer.read_frame(cap)

# Détecter visages
faces = face_recognizer.detect_faces(frame)

# Capturer un visage
face_image = face_recognizer.capture_face(cap)

# Convertir en base64
face_b64 = face_recognizer.image_to_base64(face_image)

# Fermer caméra
face_recognizer.stop_camera(cap)
```

### Module VoiceRecorder

```python
from biometric.voice import voice_recorder

# Enregistrer audio
audio = voice_recorder.record_audio(duration=5)

# Convertir en base64 WAV
audio_b64 = voice_recorder.audio_to_wav_base64(audio)

# Extraire caractéristiques
features = voice_recorder.extract_features(audio)
# Returns: {energy, zcr, spectral_centroid, mfcc_mean, duration}
```

### Module APIClient

```python
from services.api_client import api_client

# Authentification faciale
success, response = api_client.authenticate_face(face_base64)

# Authentification vocale
success, response = api_client.authenticate_voice(voice_base64)

# Health check
success, data = api_client.health_check()

# Définir token JWT
api_client.set_token("eyJ0eXAi...")
```

## 📌 Notes importantes

- **Threading**: Les opérations longues (caméra, API) s'exécutent dans des threads séparés
- **UI responsif**: La caméra s'affiche à ~30 FPS sans bloquer l'interface
- **Fallback**: En cas d'échec facial, proposition automatique du voix
- **Stateful**: L'interface maintient l'état de l'authentification

## 🚀 Prochaines améliorations

- [ ] Reconnaissance faciale avancée (DeepFace, FaceNet)
- [ ] Liveness detection (anti-spoof)
- [ ] Authentification combinée (face + voix simultanément)
- [ ] Mode inscriptions pour nouveaux utilisateurs
- [ ] Export des rapports d'authentification
- [ ] Intégration SSO
- [ ] Mode offline avec cache local

## 📄 Licence

BioAccess Secure © 2024. Tous droits réservés.

## 👨‍💼 Support

Pour toute question ou problème:
- Consulter les logs: `logs/app.log`
- Vérifier la configuration: `.env`
- Tester la connexion API avec cURL:
  ```bash
  curl http://localhost:5000/api/v1/health
  ```

---

**Version:** 1.0  
**Dernière mise à jour:** 21 Mars 2024  
**État:** ✅ Prêt pour production
