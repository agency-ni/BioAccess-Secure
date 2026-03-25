# Configuration des Périphériques Biométriques - BioAccess Secure

Guide complet pour configurer et tester l'accès à la caméra et au microphone.

## 📋 Sommaire

1. [Vue d'ensemble](#vue-densemble)
2. [Démarrage rapide](#démarrage-rapide)
3. [Scripts disponibles](#scripts-disponibles)
4. [Configuration par système d'exploitation](#configuration-par-système-dexploitation)
5. [Troubleshooting](#troubleshooting)
6. [Structure des fichiers](#structure-des-fichiers)

---

## 🎯 Vue d'ensemble

L'application BioAccess Secure utilise:
- **Caméra**: Pour la reconnaissance faciale via OpenCV
- **Microphone**: Pour la reconnaissance vocale via SoundDevice

Ces scripts vous aident à:
- ✅ Diagnostiquer les problèmes de périphériques
- ✅ Gérer les permissions d'accès
- ✅ Tester la connectivité
- ✅ Configurer les périphériques alternatifs

---

## ⚡ Démarrage rapide

### 1. Configuration complète (Recommandé)

```bash
python device_setup.py
```

Cela lancera une interface interactive qui:
- Vérifiera le système
- Testera les permissions
- Testera la caméra
- Testera le microphone
- Créera un rapport détaillé

### 2. Diagnostic uniquement

```bash
python device_diagnostic.py
```

Génère un rapport complet dans `logs/device_diagnostic_results.json`

### 3. Gestionnaire de permissions

```bash
python permissions_manager.py
```

Menu interactif pour gérer les permissions par système d'exploitation.

---

## 🛠️ Scripts disponibles

### device_setup.py
**Interface de configuration interactive**
- Configuration complète du système
- Tests de tous les périphériques
- Gestion automatique des erreurs
- Création de rapports

```bash
python device_setup.py
```

### device_diagnostic.py
**Diagnostic détaillé des périphériques**
- Détecte toutes les caméras/mics disponibles
- Teste l'enregistrement
- Vérifie les permissions Windows
- Génère un JSON de résultats

```bash
python device_diagnostic.py
```

### permissions_manager.py
**Gestionnaire de permissions cross-platform**
- Vérifie les permissions actuelles
- Demande les permissions
- Fournit les instructions par OS
- Support Windows/Linux/macOS

```bash
python permissions_manager.py
```

### DEVICE_SETUP_GUIDE.py
**Guide interactif avec instructions**
- Guide spécifique par système
- Instructions de troubleshooting
- Lien vers tous les scripts

```bash
python DEVICE_SETUP_GUIDE.py
```

---

## 🖥️ Configuration par système d'exploitation

### Windows 10/11

#### Activer la caméra

1. **Paramètres > Confidentialité et sécurité > Caméra**
2. Activer "Accès à la caméra"
3. Activer "Autoriser les applications à accéder à votre caméra"
4. S'assurer que BioAccess Secure est autorisée dans la liste

#### Activer le microphone

1. **Paramètres > Confidentialité et sécurité > Microphone**
2. Activer "Accès au microphone"
3. Activer "Autoriser les applications à accéder à votre microphone"
4. S'assurer que BioAccess Secure est autorisée dans la liste

#### Test rapide

```bash
# Tester caméra
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'ERREUR')"

# Tester microphone
python -c "import sounddevice as sd; print('OK' if len(sd.query_devices()) > 0 else 'ERREUR')"
```

---

### Linux

#### Ajouter les permissions utilisateur

```bash
# Caméra
sudo usermod -a -G video $USER

# Microphone
sudo usermod -a -G audio $USER

# Appliquer (option 1)
newgrp video && newgrp audio

# Appliquer (option 2)
# Déconnectez-vous puis reconnectez-vous
```

#### Vérifier

```bash
groups  # Doit contenir 'video' et 'audio'
```

#### Dépendances (Ubuntu/Debian)

```bash
sudo apt-get install python3-opencv python3-sounddevice
sudo apt-get install libopencv-dev pulseaudio
```

---

### macOS

#### Permissions

macOS demande les permissions automatiquement au premier accès.

Si refusées précédemment:
1. **Préférences Système > Sécurité et confidentialité > Caméra**
2. Retirer l'application et la rajouter

#### Installation

```bash
# Via Homebrew
brew install opencv

# Via pip
pip install opencv-python sounddevice soundfile
```

---

## 🔧 Troubleshooting

### Problème: Aucune caméra détectée

**Étape 1: Vérifier le matériel**
```bash
# Linux/macOS
ls /dev/video*

# Windows: Gestionnaire de périphériques > Caméras
```

**Étape 2: Permissions**
- Vérifier les paramètres de confidentialité (voir plus haut)
- Redémarrer l'application

**Étape 3: Pilotes**
- Mettre à jour les pilotes de la caméra
- Redémarrer l'ordinateur

**Étape 4: Test**
```bash
python device_diagnostic.py
```

---

### Problème: Permission refusée

**Windows:**
1. Paramètres > Confidentialité > Caméra/Microphone
2. Assurez-vous que l'option "Permettre aux applications d'accéder" est ON
3. L'app doit être dans la liste blanche
4. Redémarrer Windows si nécessaire

**Linux:**
```bash
# Vérifier les groupes
groups | grep video    # Doit contenir 'video'
groups | grep audio    # Doit contenir 'audio'

# Si absent, exécuter:
sudo usermod -a -G video $USER
sudo usermod -a -G audio $USER
newgrp video && newgrp audio
```

**macOS:**
```bash
# Réinitialiser les permissions
tccutil reset All com.yourapp
```

---

### Problème: Microphone silencieux

1. Vérifier le volume du microphone
   - Zone système > Volume > Paramètres de volume avancés
   - Régler le niveau d'entrée du microphone

2. Tester avec l'enregistreur natif
   - Windows: Accessoires > Enregistreur de bruit
   - Linux: `rec test.wav`
   - macOS: GarageBand ou Enregistreur

3. Redémarrer le service audio
   - Windows: Redémarrer "Windows Audio" dans services.msc
   - Linux: `systemctl restart pulseaudio`

---

### Problème: L'application plante en accédant caméra/micro

1. Vérifier les logs:
   ```bash
   cat logs/device_setup.log
   cat logs/device_diagnostic_results.json
   ```

2. Mettre à jour les packages:
   ```bash
   pip install --upgrade opencv-python sounddevice soundfile scipy
   ```

3. Exécuter le diagnostic:
   ```bash
   python device_diagnostic.py
   ```

---

## 📁 Structure des fichiers

```
Client Desktop/
├── device_setup.py              ← Configuration complète (RECOMMANDÉ)
├── device_diagnostic.py         ← Diagnostic détaillé
├── permissions_manager.py       ← Gestionnaire de permissions
├── DEVICE_SETUP_GUIDE.py       ← Guide interactif
├── DEVICE_CONFIGURATION.md      ← Cet fichier
├── biometric/
│   ├── face.py                  ← Amélioré: meilleure gestion d'erreurs
│   ├── voice.py                 ← Amélioré: support micro alternatifs
│   └── __init__.py
└── logs/                        ← Rapports de diagnostic
    ├── device_diagnostic_results.json
    ├── setup_*.json
    └── device_setup.log
```

---

## 📊 Résultats des tests

### Format du rapport diagnostic

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "os": "Windows",
  "camera": {
    "status": "OK",
    "cameras_found": [0],
    "default_id": 0
  },
  "microphone": {
    "status": "OK",
    "devices": [
      {
        "id": 1,
        "name": "Microphone intégré",
        "channels": 2,
        "sample_rate": 44100
      }
    ],
    "recording_test": "OK"
  },
  "issues": [],
  "recommendations": []
}
```

---

## 🚀 Intégration avec l'application

### Code de démarrage amélioré

```python
from biometric.face import FaceRecognizer, CameraAccessError
from biometric.voice import VoiceRecorder, MicrophoneAccessError

try:
    # Initialiser le reconnaisseur facial
    face = FaceRecognizer()
    cap = face.start_camera()
    
except CameraAccessError:
    # Essayer une caméra alternative
    cap = face.try_alternative_cameras()
    if not cap:
        print("Aucune caméra disponible")

try:
    # Initialiser l'enregistreur vocal
    voice = VoiceRecorder()
    
    # Changer le microphone si besoin
    devices = voice.get_input_devices()
    if devices:
        voice.set_device(devices[0]['id'])
    
    # Enregistrer
    audio = voice.record_audio(duration=5)
    
except MicrophoneAccessError:
    # Essayer un microphone alternatif
    audio = voice.try_alternative_devices()
    if audio is None:
        print("Aucun microphone disponible")
```

---

## 💡 Tips et astuces

### Test rapide des permissions

```bash
# Tout en une ligne
python -c "
from permissions_manager import PermissionsManager
pm = PermissionsManager()
perms = pm.check_all_permissions()
print(f\"Caméra: {perms['camera']}\")
print(f\"Microphone: {perms['microphone']}\")
"
```

### Sauvegarder la configuration

Les rapports sont automatiquement sauvegardés dans `logs/`:
- `device_diagnostic_results.json` - Résultats techniques
- `setup_YYYYMMDD_HHMMSS.json` - Historique des configurations
- `device_setup.log` - Logs détaillés

### Réexécuter la configuration

```bash
# Relancer à tout moment
python device_setup.py

# Ou juste faire le diagnostic
python device_diagnostic.py
```

---

## 📞 Support

Si les problèmes persistent:

1. **Collecter les logs:**
   ```bash
   python device_diagnostic.py
   # Envoyer: logs/device_diagnostic_results.json
   ```

2. **Exécuter la config complète:**
   ```bash
   python device_setup.py
   # Envoyer: logs/setup_*.json
   ```

3. **Consulter la documentation:**
   - [ARCHITECTURE.md](./ARCHITECTURE.md)
   - [DEBUG.md](./DEBUG.md)
   - [README.md](./README.md)

---

**Dernière mise à jour:** 2024  
**Compatibilité:** Python 3.7+, Windows/Linux/macOS
