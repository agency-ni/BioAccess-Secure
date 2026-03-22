# 🏗️ Architecture du Client Desktop

## Vue d'ensemble

```
┌──────────────────────────────────────────────────────────────┐
│                   BioAccess Secure Client                    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐        ┌──────────────────┐           │
│  │  UI Layer        │        │  Biometric Layer │           │
│  ├──────────────────┤        ├──────────────────┤           │
│  │ • LoginScreen    │        │ • FaceRecognizer │           │
│  │ • Camera canvas  │        │ • VoiceRecorder  │           │
│  │ • Status display │        │                  │           │
│  │ • Message log    │        │ OpenCV, SoundDev │           │
│  └────────┬─────────┘        └────────┬─────────┘           │
│           │                           │                      │
│           └─────────────┬─────────────┘                      │
│                         │                                    │
│                ┌────────▼────────┐                          │
│                │ Services Layer  │                          │
│                ├─────────────────┤                          │
│                │ • APIClient     │                          │
│                │ • Threading mgr │                          │
│                └────────┬────────┘                          │
│                         │                                    │
│                ┌────────▼────────────────────┐              │
│                │  HTTP API Server (Flask)   │              │
│                ├────────────────────────────┤              │
│                │ /api/v1/auth/face          │              │
│                │ /api/v1/auth/voice         │              │
│                │ /api/v1/auth/biometric     │              │
│                └────────────────────────────┘              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Architecture en couches

### 1. **UI Layer** (`ui/login_screen.py`)
Responsabilités:
- Affichage de l'interface Tkinter
- Gestion des événements utilisateur (boutons, clic)
- Affichage du flux caméra en temps réel
- Logs utilisateur en direct
- Gestion de l'état (authentifié, tentatives, etc.)

**Threading:**
- Thread principal: Tkinter event loop
- Thread caméra: Affichage ~30 FPS
- Thread traitement: Scans et API calls

### 2. **Biometric Layer** (`biometric/`)

#### **FaceRecognizer** (`biometric/face.py`)
```python
FaceRecognizer
├── start_camera()           # Initialiser cv2.VideoCapture
├── read_frame()             # Lire une frame
├── detect_faces()           # Détecter visages (Haar Cascade)
├── capture_face()           # Capturer et extraire ROI
├── frame_with_detection()   # Ajouter boîtes détection
├── image_to_base64()        # Encoder pour API
└── image_to_opencv()        # Décoder depuis API
```

**Tech Stack:**
- OpenCV 4.5+
- Haar Cascade Classifier (pré-entraîné)
- NumPy pour opérations images
- JPEG encoding/decoding

#### **VoiceRecorder** (`biometric/voice.py`)
```python
VoiceRecorder
├── record_audio()           # Enregistrement bloquant
├── record_with_callback()   # Enregistrement avec feedback
├── audio_to_wav_base64()    # Encoder pour API
├── wav_base64_to_audio()    # Décoder depuis API
├── extract_features()       # Extraire caractéristiques (MFCC, RMS, etc.)
└── play_audio()             # Jouer pour test
```

**Tech Stack:**
- sounddevice pour capture
- soundfile pour WAV
- SciPy pour traitement signal
- Base64 pour transmission

### 3. **Services Layer** (`services/`)

#### **APIClient** (`services/api_client.py`)
```python
APIClient
├── authenticate_face()      # POST /auth/face
├── authenticate_voice()     # POST /auth/voice
├── authenticate_biometric() # POST /auth/biometric
├── health_check()           # GET /health
├── login_password()         # POST /auth/login
├── set_token()              # Gérer JWT
└── _make_request()          # Requête HTTP générique
```

**Gestion:**
- Timeouts (défaut: 10s)
- Retry logic (implicite via requests)
- JSON encoding/decoding
- Error handling robuste
- Headers de sécurité (X-API-Key)

### 4. **Data Flow**

#### Authentification faciale:
```
1. User clicks "📸 Scanner Visage"
   ↓
2. UI Thread starts camera thread
   ↓
3. Camera thread calls FaceRecognizer.capture_face()
   ├─ Read frames ~30 FPS
   ├─ Detect faces via Haar Cascade
   └─ Extract largest face ROI
   ↓
4. Convert to JPEG + Base64
   ↓
5. Processing thread calls APIClient.authenticate_face(base64)
   ├─ HTTP POST /auth/face
   ├─ Wait response (timeout 10s)
   └─ Return result
   ↓
6. UI updates with result
   ├─ Success: Show user name + confidence
   └─ Fail: Suggest voice auth
```

#### Authentification vocale:
```
1. User clicks "🎤 Utiliser la Voix"
   ↓
2. Processing thread calls VoiceRecorder.record_audio(5)
   ├─ sounddevice.rec() for 5 seconds
   ├─ ~220K samples @ 44.1kHz
   └─ NumPy array returned
   ↓
3. Convert to WAV + Base64
   ↓
4. Processing thread calls APIClient.authenticate_voice(base64)
   ├─ HTTP POST /auth/voice
   ├─ Wait response
   └─ Return result
   ↓
5. UI updates with result
```

## Flux d'authentification multi-modale

```
START
  │
  ├─→ Facial Auth
  │   ├─ Success → AUTHENTICATED ✅
  │   └─ Fail → Decrease attempts
  │
  ├─→ If attempts > 0
  │   └─ Offer Voice Auth
  │       ├─ Success → AUTHENTICATED ✅
  │       └─ Fail → Decrease attempts
  │
  ├─→ If attempts ≤ 0
  │   └─ BLOCKED (5 min timeout)
  │
  └─ Display result
```

## Configuration centralisée

Tous les paramètres sont dans `config.py`:

```python
# API
API_BASE_URL = os.getenv(...)
API_TIMEOUT = 10

# Caméra
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# Audio
AUDIO_DURATION = 5
AUDIO_SAMPLE_RATE = 44100

# UI
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 700

# Seuils
FACE_CONFIDENCE_THRESHOLD = 0.7
VOICE_CONFIDENCE_THRESHOLD = 0.7

# Limites
MAX_ATTEMPTS = 3
ATTEMPT_TIMEOUT = 300
```

## Threading Model

### Thread 1: UI (Main)
- Tkinter event loop
- Button callbacks (non-bloquant)
- Canvas updates
- Text widget updates

### Thread 2: Camera
- Continuous frame capture
- Frame display (~30 FPS)
- Detection drawing
- Runs while is_camera_running = True

### Thread 3: Processing
- Biometric processing
- API calls
- Result updating
- One at a time (queue-like)

**Synchronization:**
- Flags: `is_camera_running`, `is_recording`
- State: `authenticated`, `current_user`
- Thread-safe via tkinter.after()

## Security measures

### 1. API Communication
```
Client → Server:
  • HTTPS (production)
  • X-API-Key header
  • Base64 encoded biometric data
  • Timestamp validation
```

### 2. Rate Limiting
```
• Max 3 auth attempts
• 5 minute cooldown after failure
• Display countdown
```

### 3. Data Handling
```
• Biometric data never stored locally
  (sent immediately to server)
• Temp files cleaned up
• Logs don't contain sensitive data
```

### 4. Error Handling
```
• Network errors caught
• Timeouts enforced
• Invalid responses filtered
• User-friendly error messages
```

## Performance Characteristics

### Camera Feed
```
- Resolution: 640x480
- FPS: ~30 (max)
- Latency: ~33ms per frame
- CPU: ~10-15% (one core)
```

### Audio Processing
```
- Sample rate: 44.1kHz
- Duration: 5 seconds
- File size: ~440KB (WAV)
- Base64 encoded: ~590KB
- Processing: ~100ms
```

### API Communication
```
- Request: ~600KB (Base64 image)
- Response: ~1KB (JSON)
- Network latency: ~50-200ms
- Server processing: ~2-5 seconds
- Total: ~3-10 seconds per auth
```

### Memory Usage
```
- Base app: ~50MB
- With camera running: ~120MB
- With audio recording: +50MB
- Peak: ~200MB
```

## Module Dependencies

```
main.py
├── config.py         (Configuration)
├── ui/
│   └── login_screen.py
│       ├── tkinter
│       ├── threading
│       ├── PIL (Pillow)
│       ├── cv2 (OpenCV)
│       │   └── numpy
│       ├── services.api_client
│       ├── biometric.face
│       └── biometric.voice
├── biometric/
│   ├── face.py
│   │   ├── cv2
│   │   ├── numpy
│   │   └── base64
│   └── voice.py
│       ├── sounddevice
│       ├── soundfile
│       ├── numpy
│       └── base64
└── services/
    └── api_client.py
        ├── requests
        ├── json
        └── logging
```

## Extension Points

### Ajouter un nouveau mode biométrique:

```python
# 1. Créer biometric/iris.py
class IrisRecognizer:
    def capture_iris(self, cap):
        ...
    
    def iris_to_base64(self, image):
        ...

# 2. Ajouter à services/api_client.py
def authenticate_iris(self, iris_data):
    success, response = self._make_request('POST', '/auth/iris', 
                                          data={'iris_image': iris_data})
    return success, response

# 3. Ajouter bouton à ui/login_screen.py
self.btn_iris = tk.Button(..., command=self._on_iris_scan)

# 4. Implémenter handler
def _on_iris_scan(self):
    iris_image = iris_recognizer.capture_iris(self.camera)
    ...
```

### Ajouter connexion avec password:

```python
# Dans ui/login_screen.py
def _on_login_with_password(self):
    dialog = PasswordDialog()
    email, password = dialog.get_credentials()
    
    success, response = api_client.login_password(email, password)
    if success:
        api_client.set_token(response['token'])
        self._on_auth_success(...)
```

---

**Dernier update:** 21 Mars 2024  
**Version:** 1.0  
**État:** Production-ready
