# 📱 Guide de Configuration des Périphériques Biométriques - BioAccess Secure

## 🎯 Vue d'ensemble

Ce guide vous aidera à configurer votre caméra et microphone pour utiliser les fonctionnalités biométriques de **BioAccess Secure**.

## 🚀 Démarrage rapide

### Windows (Recommandé)

```bash
cd "Client Desktop"
install_permissions.bat
```

Cela installera automatiquement toutes les dépendances et lancera le diagnostic.

### Linux

```bash
cd Client\ Desktop
chmod +x install_permissions.sh
./install_permissions.sh
```

### macOS

```bash
cd Client\ Desktop
python3 device_setup.py
```

---

## 📋 Configuration manuelle

### Étape 1: Installer les dépendances

#### Windows
```bash
python -m pip install opencv-python sounddevice soundfile scipy numpy
```

#### Linux
```bash
# Ubuntu/Debian
sudo apt-get install python3-pip python3-dev libopencv-dev python3-opencv
sudo apt-get install libasound2-dev portaudio19-dev
pip install opencv-python sounddevice soundfile scipy numpy

# Fedora
sudo dnf install opencv-devel python3-devel alsa-lib-devel portaudio-devel
pip install opencv-python sounddevice soundfile scipy numpy

# Arch
sudo pacman -S opencv portaudio alsa-lib
pip install opencv-python sounddevice soundfile scipy numpy
```

#### macOS
```bash
brew install opencv
pip install opencv-python sounddevice soundfile scipy numpy
```

### Étape 2: Exécuter le diagnostic

```bash
python device_diagnostic.py
```

Ce script:
- ✅ Détecte toutes les caméras disponibles
- ✅ Détecte tous les microphones disponibles
- ✅ Teste la capture vidéo
- ✅ Teste l'enregistrement audio
- ✅ Génère un rapport détaillé en JSON

### Étape 3: Configurer les permissions

```bash
python device_setup.py
```

Suivez le menu interactif.

---

## 🔐 Configuration des Permissions par OS

### Windows

#### 📷 Permission Caméra

1. **Ouvrir Paramètres**
   - Appuyez sur `Win + I`
   - Ou allez dans le menu Démarrer > Paramètres

2. **Accèder à Confidentialité**
   - Confidentialité et sécurité > Caméra

3. **Activer l'accès**
   - S'assurer que "Accès à la caméra" est **ON**
   - Vérifier que "BioAccessSecure" (ou votre application) est autorisée

4. **Redémarrer l'application**

#### 🎤 Permission Microphone

1. **Ouvrir Paramètres** (`Win + I`)
2. **Aller à:** Confidentialité et sécurité > Microphone
3. **Activer:** "Accès au microphone" = **ON**
4. **Vérifier:** L'application, elle est autorisée
5. **Redémarrer** l'application

#### ⚠️ Dépannage Windows

**Problème:** "Caméra/Microphone non détecté"
- Vérifier les connexions USB
- Redémarrer l'ordinateur
- Tester avec l'application "Appareil photo" Windows

**Problème:** "Accès refusé même après permission"
- Allez dans Paramètres > Systèmes > Sons
- Vérifier les périphériques d'entrée/sortie
- Mettre à jour les pilotes (gestionnaire de périphériques)

---

### Linux

#### 📷 & 🎤 Configuration des Groupes

L'accès aux périphériques vidéo et audio nécessite d'être dans les groupes `video` et `audio`.

```bash
# Vérifier les groupes actuels
groups

# Ajouter aux groupes
sudo usermod -a -G video $USER
sudo usermod -a -G audio $USER

# Option 1: Se reconnecter à la session
# Option 2: Appliquer les changements maintenant
newgrp video && newgrp audio
```

#### Permissions d'accès aux fichiers

```bash
# Vérifier les permissions
ls -la /dev/video*
ls -la /dev/snd/

# Les périphériques doivent être accessibles par le groupe
# Exemple:
# crw-rw----+ 1 root video 81, 0 Mar 25 10:30 /dev/video0
#            ^^^^^ groupe video
```

#### ⚠️ Dépannage Linux

**Problème:** "Permission denied" even après `usermod`
```bash
# Vous devez vous reconnecter. Essayez:
newgrp video && newgrp audio

# Ou vérifier que la session a été renouvelée:
groups
# Devrait inclure "video audio"
```

**Problème:** ALSA warnings
```bash
# Créer .asoundrc
cat > ~/.asoundrc << 'EOF'
defaults.pcm.card 0
defaults.ctl.card 0
EOF
```

**Problème:** No cameras detected
```bash
# Vérifier les périphériques
v4l2-ctl --list-devices

# Si aucun, les pilotes ne sont pas installés
# Exemple (Ubuntu):
sudo apt-get install v4l-utils linux-modules-extra-$(uname -r)
```

---

### macOS

#### 📷 & 🎤 Permission via Boîte de dialogue

La première fois que vous lancez l'application:
- Une boîte de dialogue vous demande accès à la **caméra**
- Une boîte de dialogue vous demande accès au **microphone**
- Cliquez sur **"OK"** ou **"Autoriser"**

#### Manuel: Sécurité & Confidentialité

1. **Ouvrir Préférences Système**
   - Icône Apple > Préférences Système

2. **Sécurité & Confidentialité**

3. **Onglet Confidentialité**

4. **Caméra** (barre gauche)
   - Vérifier que l'application est coché ✓

5. **Microphone** (barre gauche)
   - Vérifier que l'application est coché ✓

#### ⚠️ Dépannage macOS

**Problème:** "Not permitted to open"
```bash
# Parfois, il faut réinitialiser les permissions
sudo tccutil reset Camera
sudo tccutil reset Microphone

# Puis relancer l'application
```

---

## 🧪 Tester votre Configuration

### Méthode 1: Via le script

```bash
python device_setup.py
# Choisir option 4: "Test des périphériques"
```

### Méthode 2: Test manuel

#### 🎥 Tester la caméra

```bash
# Windows/macOS/Linux
python -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    ret, frame = cap.read()
    cap.release()
    print('✅ Caméra OK' if ret else '❌ Caméra KO')
else:
    print('❌ Caméra introuvable')
"
```

#### 🎙️ Tester le microphone

```bash
# Windows/macOS/Linux
python -c "
import sounddevice as sd
import numpy as np

print('Enregistrement 2 secondes...')
recording = sd.rec(int(2 * 44100), samplerate=44100, channels=1)
sd.wait()

if np.max(np.abs(recording)) > 0.01:
    print('✅ Microphone OK')
else:
    print('❌ Microphone KO ou trop faible')
"
```

---

## 📊 Génération de Rapport

Le diagnostic génère automatiquement un fichier JSON:

```
logs/device_diagnostic_YYYYMMDD_HHMMSS.json
```

Contenu du rapport:
```json
{
  "timestamp": "2026-03-25T10:30:00",
  "os": "Windows",
  "python_version": "3.10.5",
  "cameras": [
    {
      "index": 0,
      "resolution": "1920x1080",
      "fps": 30,
      "accessible": true,
      "capture_test": "Réussi"
    }
  ],
  "microphones": [
    {
      "index": 0,
      "name": "Microphone (Microphone Array)",
      "channels": 2,
      "sample_rate": 44100,
      "accessible": true
    }
  ],
  "permissions": {
    "os": "Windows",
    "camera": "À vérifier dans Paramètres",
    "microphone": "À vérifier dans Paramètres"
  },
  "recommendations": []
}
```

---

## 🔗 Intégration dans votre Application

### Client Python

```python
from device_diagnostic import DeviceDiagnostic
from permissions_manager import PermissionsManager

# Diagnostic
diagnostic = DeviceDiagnostic()
results = diagnostic.run_full_diagnostic()

# Utiliser la caméra principale
camera_idx = diagnostic.get_primary_camera()
microphone_idx = diagnostic.get_primary_microphone()

# Vérifier les permissions
pm = PermissionsManager()
perms = pm.check_all_permissions()
```

### Backend API

```python
from core.biometric_permissions import biometric_permissions, BiometricPermission

# Vérifier une permission
check = biometric_permissions.check_permission(
    user_id='user123',
    role='employee',
    permission=BiometricPermission.USE_CAMERA
)

if check['allowed']:
    # Procéder avec l'accès caméra
    pass
```

---

## 📞 Dépannage Avancé

### Logs détaillés

Les logs sont sauvegardés dans: `logs/device_diagnostic.log`

```bash
# Voir les dernières erreurs
tail -f logs/device_diagnostic.log
```

### Vérifier les pilotes

#### Windows
```powershell
# Gestionnaire de périphériques
devmgmt.msc

# Chercher:
# - Appareils photo (Camera)
# - Enregistreurs audio (Microphone)
```

#### Linux
```bash
# Lister les périphériques vidéo
ls -la /dev/video*

# Lister les périphériques audio
arecord -l

# Infor OS
lsb_release -a
cat /proc/cpuinfo
```

#### macOS
```bash
# Lister les caméras
system_profiler SPCameraDataType

# Vérifier les permissions
sqlite3 ~/Library/Application\ Support/CrashReporter/DiagnosticMessagesHistory.db
```

### Variables d'environnement

```bash
# Windows - Forcer en debug
set CV_CAP_V4L=1

# Linux - Forcer V4L2
export CV_CAP_V4L2=1

# Puis relancer
python device_diagnostic.py
```

---

## ❓ FAQ

**Q: Dois-je relancer l'application après avoir changé les permissions?**
A: Oui, particulièrement sur Windows. Fermez complètement l'application et relancez-la.

**Q: Pourquoi plusieurs caméras sont détectées?**
A: Certains pilotes créent plusieurs interfaces pour une même caméra physique.

**Q: Comment changer la caméra/microphone utilisé?**
A: Modifiez l'index dans la config: `logs/device_config.json`

**Q: Le microphone est détecté mais le volume est très faible?**
A: Vérifiez les paramètres de volume du système.

**Q: Les permissions refusées sur Linux même après `usermod`?**
A: Vous devez vous reconnecter. Utilisez: `newgrp video && newgrp audio`

---

## 🔗 Liens Utiles

- [OpenCV Documentation](https://docs.opencv.org/)
- [sounddevice Documentation](https://python-sounddevice.readthedocs.io/)
- [Windows Privacy Settings](https://support.microsoft.com/windows/manage-app-permissions)
- [Linux Audio](https://wiki.archlinux.org/title/PulseAudio)
- [macOS Privacy](https://support.apple.com/HT210602)

---

## 💡 Support

Pour des problèmes spécifiques, consultez:
1. Les logs dans `logs/device_diagnostic.log`
2. Le rapport JSON dans `logs/device_diagnostic_*.json`
3. Les recommandations du diagnostic
4. Ce guide de dépannage

---

**Version:** 1.0  
**Dernière mise à jour:** Mars 2026  
**Support:** BioAccess Secure Team
