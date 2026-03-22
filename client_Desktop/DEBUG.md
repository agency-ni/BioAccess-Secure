# 🔧 Guide de dépannage

## 📋 Table des matières

1. [Installation](#installation)
2. [Caméra](#caméra)
3. [Audio](#audio)
4. [API](#api)
5. [Interface](#interface)
6. [Performance](#performance)

---

## Installation

### Erreur: "ModuleNotFoundError: No module named 'cv2'"

**Cause:** OpenCV non installé

**Solutions:**
```bash
# Solution 1: Installer les dépendances
pip install -r requirements.txt

# Solution 2: Installer manuellement
pip install opencv-python

# Solution 3: Compiler depuis source (avancé)
pip install --no-binary opencv-python opencv-python
```

### Erreur: "No module named 'sounddevice'"

**Cause:** Bibliothèque audio manquante

**Solutions:**
```bash
# Windows
pip install sounddevice soundfile

# Linux (Debian/Ubuntu)
sudo apt-get install python3-dev portaudio19-dev
pip install sounddevice soundfile

# macOS
brew install portaudio
pip install sounddevice soundfile
```

### Erreur: "No module named 'tkinter'"

**Cause:** Tkinter non inclus dans Python

**Solutions:**

**Windows:**
- Réinstaller Python avec l'option "tcl/tk and IDLE" cochée

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-tk
```

**macOS:**
```bash
brew install python-tk
```

### Erreur lors de "pip install -r requirements.txt"

**Solutions:**

```bash
# 1. Mettre à jour pip
python -m pip install --upgrade pip

# 2. Installer avec cache désactivé
pip install --no-cache-dir -r requirements.txt

# 3. Installer sans dépendances binaires
pip install --only-binary :all: -r requirements.txt

# 4. Installer paquets un par un
pip install pillow
pip install opencv-python
pip install sounddevice
# etc...
```

---

## Caméra

### Erreur: "Impossible d'accéder à la caméra"

**Cause 1:** Caméra non détectée

**Solutions:**
```bash
# Vérifier les caméras disponibles
python test_camera.py

# Ou directement en Python
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"

# Essayer un autre ID
# Dans .env: CAMERA_ID=1
```

**Cause 2:** Permissions insuffisantes

**Linux:**
```bash
# Ajouter l'utilisateur au groupe video
sudo usermod -a -G video $USER

# Logoff/login required
```

**macOS:**
```bash
# Accorder les permissions de caméra à Terminal
# Système → Sécurité et confidentialité → Caméra → Terminal ✓
```

**Windows:**
- Les permissions sont généralement gérées automatiquement
- Vérifier Paramètres → Confidentialité → Caméra

### Erreur: "Camera already in use"

**Cause:** Autre app utilise la caméra

**Solutions:**
```bash
# 1. Fermer les autres apps (Zoom, Teams, etc)

# 2. Redémarrer Python
# Ctrl+C dans la terminal

# 3. Sur Linux, trouver le processus
ps aux | grep camera
kill -9 [PID]
```

### Image caméra figée/slow

**Cause:** Buffer plein ou débit trop lent

**Solutions:**

Dans `config.py`:
```python
# Réduire la résolution
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240

# Augmenter le FPS
CAMERA_FPS = 60

# Réduire la qualité d'affichage
# Dans login_screen.py: ajouter stride au resize
```

Ou en code:
```python
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer minimal
cap.set(cv2.CAP_PROP_FPS, 30)
```

### "Aucun visage détecté"

**Cause:** Haar Cascade trop strict ou mauvaise lighting

**Solutions:**

1. **Améliorer l'éclairage**
   - Caméra = face à la lumière
   - Éviter les contre-jours

2. **Augmenter scale factor** (dans `face.py`):
```python
faces = self.face_cascade.detectMultiScale(
    gray,
    scaleFactor=1.05,  # Plus petit = plus sensible
    minNeighbors=3,    # Plus petit = plus sensible
    minSize=(20, 20)   # Plus petit = détecte les petits visages
)
```

3. **Utiliser autre implémentation**
   Remplacer Haar Cascade par:
   - MediaPipe (plus rapide)
   - MTCNN (plus précis)
   - dlib (très précis mais lent)

---

## Audio

### Erreur: "No audio device found"

**Cause:** Aucun microphone disponible

**Solutions:**

1. **Vérifier les périphériques:**
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

2. **Lister les périphériques dans l'app**
```python
from biometric.voice import voice_recorder
devices = voice_recorder.get_available_devices()
print(devices)
```

3. **Spécifier le device dans code:**
```python
# Dans voice.py
sd.rec(..., device=1)  # device=1 pour le 2e périphérique
```

### "Enregistrement muet / aucun son"

**Cause:** Microphone mal configuré ou muted

**Solutions:**

**Linux:**
```bash
# Vérifier levels
alsamixer

# Relancer le daemon audio
sudo systemctl restart pulseaudio

# Ou utiliser ALSA directement
export ALSA_CARD=0
```

**macOS:**
```bash
# Vérifier les permissions
# Système → Sécurité → Microphone → Terminal ✓

# Tester avec
python -c "import sounddevice as sd; sd.rec(int(44100*1), samplerate=44100); sd.wait(); print('OK')"
```

**Windows:**
- Niveau du microphone dans Paramètres détermine le volume

### Enregistrement très court/long

**Solutions:**

Dans `config.py`:
```python
AUDIO_DURATION = 5  # Éditer ceci

# Ou modifier lors de l'appel
audio = voice_recorder.record_audio(duration=3)
```

### Fichier WAV corrompu

**Cause:** Pointeur buffer non réinitialisé

**Solutions:**
```python
# Recompiler le WAV
import io
import soundfile as sf

# Correct:
buffer = io.BytesIO()
sf.write(buffer, audio, 44100)
buffer.seek(0)  # IMPORTANT!
wav_data = buffer.read()
```

---

## API

### Erreur: "Connection refused" ou "Unreachable"

**Cause:** Serveur backend pas lancé

**Solutions:**

1. **Lancer le serveur:**
```bash
# Terminal séparé
cd BACKEND
python run.py
```

2. **Vérifier l'URL:**
```bash
# Tester manuellement
curl http://localhost:5000/api/v1/health

# Ou en Python
python test_api.py
```

3. **Éditer `.env`:**
```env
# Mettre à jour l'URL si différente
API_BASE_URL=http://your-server:5000/api/v1
```

### Erreur: "Timeout" (>10 secondes)

**Cause:**
- Serveur surchargé
- Réseau lent
- API_TIMEOUT trop court

**Solutions:**

1. **Augmenter timeout dans `.env`:**
```env
API_TIMEOUT=30  # De 10 à 30 secondes
```

2. **Vérifier le réseau:**
```bash
ping localhost
# ou
ping your-server-ip
```

3. **Vérifier les logs du serveur:**
```bash
# Dans BACKEND/
tail -f logs/app.log
```

### Erreur: "401 Unauthorized"

**Cause:** API_KEY invalide

**Solutions:**

1. **Vérifier la clé dans `.env`:**
```env
API_KEY=your-api-key-here

# Comparer avec BACKEND/config.py
```

2. **Générer une nouvelle clé:**
```python
# Dans le serveur
import secrets
new_key = secrets.token_hex(32)
print(new_key)
```

### Erreur: "422 Unprocessable Entity"

**Cause:** Données invalides envoyées

**Solutions:**

1. **Vérifier le format Base64:**
```python
import base64

# Vérifier que c'est du base64 valide
base64.b64decode(your_data)
```

2. **Vérifier les endpoints:**
```bash
# Consulter API docs
curl http://localhost:5000/api/v1/health
```

### Authentification toujours "en attente"

**Cause:** Requête bloquée sur le serveur

**Solutions:**

1. **Vérifier les logs serveur:**
```bash
cd BACKEND
tail -f logs/app.log
```

2. **Redémarrer l'app:**
```bash
Ctrl+C dans client
python main.py
```

---

## Interface

### Fenêtre Tkinter non responsive

**Cause:** Thread principal bloqué

**Solutions:**

1. **Vérifier threading:**
```python
# ❌ Mauvais - bloque l'UI
auth_face()

# ✅ Bon - utilise un thread
threading.Thread(target=auth_face, daemon=True).start()
```

2. **UI update de manière thread-safe:**
```python
# ❌ Mauvais - peut crasher
self.label.config(text="Nouveau texte")

# ✅ Bon
self.root.after(0, lambda: self.label.config(text="Nouveau texte"))
```

### Camera feed figée

**Cause:** Caméra fed thread crashée

**Solutions:**

Vérifier `logs/app.log`:
```bash
tail -f logs/app.log | grep -i "camera\|error"
```

Puis redémarrer:
```bash
Ctrl+C
python main.py
```

### Affichage pixelisé / dégradé

**Cause:** Compression JPEG trop agressif

**Solutions:**

Dans `face.py`:
```python
# Augmenter quality
success, buffer = cv2.imencode('.jpg', image,
                              [cv2.IMWRITE_JPEG_QUALITY, 95])  # De 95 à 100
```

### Boutons ne réagissent pas

**Cause:** État gelé ou variables mal configurées

**Solutions:**

1. **Ajouter debug:**
```python
def _on_face_scan(self):
    print("DEBUG: Bouton cliqué")
    print(f"State: {self.is_recording}, {self.is_camera_running}")
    ...
```

2. **Vérifier flags:**
```python
# Dans _on_quit()
self.is_camera_running = False
self.is_recording = False
```

---

## Performance

### CPU à 100%

**Cause:** Capture caméra trop rapide ou traitement inefficace

**Solutions:**

1. **Réduire FPS:**
```env
CAMERA_FPS=15  # Au lieu de 30
```

2. **Augmenter intervalle refresh:**
Dans `login_screen.py`:
```python
self.root.after(100, self._display_camera_feed)  # Au lieu de 33
```

3. **Utiliser threading approprié:**
```python
# Ne pas rafraîchir plus que nécessaire
if frame_count % 3 == 0:
    self._display_frame(frame)
```

### Mémoire croissante / Leak

**Cause:** Ressources non libérées

**Solutions:**

1. **Fermer caméra proprement:**
```python
def _cleanup(self):
    self.is_camera_running = False
    if self.camera:
        self.camera.release()
        self.camera = None
```

2. **Nettoyer les images PIL:**
```python
# Dans display_camera_feed()
if hasattr(self.camera_canvas, 'image'):
    del self.camera_canvas.image  # Supprimer référence
```

3. **Profiler la mémoire:**
```bash
pip install memory-profiler
python -m memory_profiler main.py
```

---

## Checklist de Debug

À faire dans cet ordre:

- [ ] **Installation**: `pip install -r requirements.txt`
- [ ] **Environnement**: `python -c "import cv2, sounddevice, tkinter"`
- [ ] **Configuration**: Fichier `.env` créé et édité
- [ ] **API**: `python test_api.py` → ✅
- [ ] **Caméra**: `python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"`
- [ ] **Audio**: `python -c "import sounddevice as sd; print(sd.query_devices())"`
- [ ] **App**: `python main.py` → Interface OK?
- [ ] **Caméra live**: Cliquer "Scanner Visage" → Voir flux?
- [ ] **Enregistrement**: Cliquer "Utiliser la voix" → Micro capte?
- [ ] **API call**: Attendre réponse serveur → Logs affichés?

---

## Contact Support

Pour plus d'aide:

1. **Consulter les logs:**
   ```bash
   tail -f logs/app.log
   ```

2. **Chercher l'erreur:**
   - Chercher le message d'erreur dans ce fichier
   - Ou rechercher sur StackOverflow

3. **Tester avec debug:**
   ```env
   DEBUG=True
   LOG_LEVEL=DEBUG
   ```

---

**Dernière mise à jour:** 21 Mars 2024  
**Vous avez besoin d'aide?** Consultez README.md ou ARCHITECTURE.md
