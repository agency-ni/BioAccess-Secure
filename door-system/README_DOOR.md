# BioLock Door System — Module Porte Biométrique Raspberry Pi

## Vue d'ensemble

**BioLock Door System** est un système complet d'authentification biométrique multi-facteur pour contrôle d'accès physique sur Raspberry Pi. Le système combine la reconnaissance faciale et vocale pour sécuriser l'accès à une porte électromécanique.

**Caractéristiques principales:**
- ✅ Authentification multi-facteur (face + voix)
- ✅ Seuil de confiance minimum: `0.85` pour chaque facteur
- ✅ Lockout automatique après 3 tentatives échouées (cooldown 60s)
- ✅ Gestion réseau résiliente (timeouts, retry)
- ✅ LED de feedback (verte=prêt, rouge=erreur)
- ✅ Journalisation complète des tentatives
- ✅ Compatible Raspberry Pi OS (Bullseye/Bookworm)

---

## Architecture

```
door-system/
├── main.py                      # Programme principal (orchestration)
├── config.py                    # Variables de configuration
├── api_client.py                # Client API backend (retry/timeout)
├── face_auth.py                 # Pipeline capture vidéo → auth faciale
├── voice_auth.py                # Pipeline enregistrement → auth vocale
├── hardware/
│   ├── __init__.py
│   ├── servo_control.py         # Contrôle servomoteur (PWM/GPIO)
│   ├── camera.py                # Capture vidéo OpenCV (3s)
│   └── microphone.py            # Enregistrement audio sounddevice (3s)
├── biolock-door.service         # Service systemd autostart
├── requirements.txt             # Dépendances Python
├── migration_auth_logs.sql      # Migration BD (source_type)
├── .env.example                 # Template configuration
└── README_DOOR.md              # Cette documentation
```

---

## Flux d'authentification

```
┌─────────────────────────────────────────────────────────────┐
│ 1. DÉMARRAGE                                                  │
│    - GPIO setup (bouton, LEDs, servo)                        │
│    - Vérif connexion backend                                 │
│    - LED verte allumée = système prêt                        │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. ATTENTE DÉCLENCHEMENT                                      │
│    - Bouton GPIO 23 appuyé OU mouvement détecté              │
│    - Vérif pas en cooldown (3 tentatives)                    │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. CAPTURE FACIALE (3 secondes)                               │
│    - Caméra active (OpenCV)                                  │
│    - Détection visage (Haar Cascade)                         │
│    - Image encodée base64                                    │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. AUTH FACIALE (backend)                                     │
│    - POST /auth/face/verify { user_id, image_b64, source }   │
│    - Timeout 5s, retry x2 si réseau instable                │
│    - Résultat: success, confidence                           │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. CAPTURE VOCALE (3 secondes)                                │
│    - Microphone actif (sounddevice)                              │
│    - Enregistrement WAV                                      │
│    - Audio encodé base64                                     │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. AUTH VOCALE (backend)                                      │
│    - POST /auth/voice/verify { user_id, audio_b64, source }  │
│    - Timeout 5s, retry x2 si réseau instable                │
│    - Résultat: success, confidence                           │
└─────────────────────────────────────────────────────────────┘
                             ↓
         ┌─────────────────┴──────────────────┐
         ↓                                     ↓
    ✅ SUCCÈS                            ❌ ÉCHEC
    (face >= 0.85 ET voix >= 0.85)  (confiance insuffisante)
         ↓                                     ↓
    LED verte clignote                 `attempt_count++`
    Ouverture porte (5s)                LED rouge (2 clig)
    Fermeture auto                      
    Logs "SOURCE_TYPE=DOOR"             Si attempt >= 3:
                                          → Lockout 60s
                                          → LED rouge fixe
```

---

## Installation Raspberry Pi

### 1. Prérequis matériel

```
Composants:
□ Raspberry Pi 4B ou 5 (min 2GB RAM)
□ Caméra USB ou CSI pour Pi Camera Module
□ Microphone USB (ou ligne audio en 3.5mm)
□ Servomoteur 5V (SG90 ou similaire)
□ Relais 5V pour alimentation servo
□ Bouton poussoir (avec pull-up GPIO)
□ 2x LED 5mm (verte + rouge) + résistances 220Ω
□ Carte microSD 32GB+ avec Raspberry Pi OS Bullseye/Bookworm
□ Alimentation 5V 2.5A minimum

Brochage GPIO:
Pin 18 (GPIO18) → PWM servo
Pin 23 (GPIO23) → Bouton (pull-up)
Pin 24 (GPIO24) → LED verte
Pin 25 (GPIO25) → LED rouge
Pin 27 (GPIO27) → Capteur mouvement (optionnel)
+ GND/5V pour alimentation capteurs
```

### 2. Installation système Raspberry Pi OS

```bash
# 1. Flasher Raspberry Pi OS via Imager ou dd
# 2. Démarrer Pi et accéder en SSH

# 3. Mise à jour système
sudo apt update
sudo apt upgrade -y

# 4. Installer dépendances système
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    libopenjp2-7 \
    libtiff5 \
    libjasper-dev \
    libharfbuzz0b \
    libwebp6 \
    libtk8.6 \
    libatlas-base-dev \
    libjasper-dev \
    libhdf5-dev \
    libharfbuzz0b \
    libwebp6 \
    libtiff5 \
    libjasper1 \
    libatlas3-base \
    libopenexr23 \
    libqtgui4 \
    python3-sounddevice \
    alsa-utils \
    git

# 5. Cloner le projet
cd /home/pi
git clone https://github.com/agency-ni/BioAccess-Secure.git
cd BioAccess-Secure/door-system
```

### 3. Configuration Python et dépendances

```bash
# 1. Créer virtualenv
python3 -m venv venv
source venv/bin/activate

# 2. Installer dépendances Python
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 3. Configurer les variables d'environnement
cp .env.example .env
nano .env  # Éditer avec les valeurs réelles
```

**Points critiques dans `.env`:**
```
BACKEND_URL=http://192.168.1.100:5000    # IP du backend
ADMIN_TOKEN=votre_token_admin              # Token de la part d'un admin
USER_ID=uuid-xxxxxxxx-xxxx-xxxx-xxxx      # UUID créé par POST /admin/users
```

### 4. Installation comme service systemd

```bash
# 1. Copier le fichier service
sudo cp biolock-door.service /etc/systemd/system/

# 2. Ajuster les chemins si nécessaire
sudo nano /etc/systemd/system/biolock-door.service
# Vérifier: ExecStart=/usr/bin/python3 /home/pi/BioAccess-Secure/door-system/main.py

# 3. Activer le service (autostart au démarrage)
sudo systemctl daemon-reload
sudo systemctl enable biolock-door.service
sudo systemctl start biolock-door.service

# 4. Vérifier statut
sudo systemctl status biolock-door.service
sudo journalctl -u biolock-door -f  # Logs en temps réel
```

### 5. Test et débogage

```bash
# Test connexion backend
python3 -c "from api_client import BioAccessAPIClient; \
            api = BioAccessAPIClient(); \
            print('Connexion OK' if api.test_connection() else 'Erreur')"

# Test caméra
python3 -c "import cv2; cap = cv2.VideoCapture(0); \
            ret, frame = cap.read(); \
            cap.release(); \
            print('Caméra OK' if ret else 'Caméra KO')"

# Test microphone
python3 -c "from hardware.microphone import MicrophoneService; \
            m = MicrophoneService(); \
            devices = m.list_audio_devices(); \
            for idx, info in devices.items(): \
                print(f'{idx}: {info}')"

# Test GPIO
python3 -c "import RPi.GPIO as GPIO; \
            GPIO.setmode(GPIO.BCM); \
            GPIO.setup(24, GPIO.OUT); \
            GPIO.output(24, GPIO.HIGH); \
            print('GPIO OK'); \
            GPIO.cleanup()"

# Exécuter en foreground pour logs
python3 main.py
```

---

## Configuration backend requise

### Migration SQL

Exécuter sur le serveur PostgreSQL:

```bash
sudo -u postgres psql bioaccess_db < migration_auth_logs.sql
```

### Créer utilisateur pour la porte

Via l'API ou interface admin, créer un `POST /admin/users`:

```bash
curl -X POST http://192.168.1.100:5000/api/v1/admin/users \
  -H "X-Admin-Token: YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "nom": "Porte",
    "prenom": "Bureau",
    "email": "porte.bureau@example.com",
    "role": "employe",
    "departement": "Sécurité"
  }'

# Réponse: { "user_id": "uuid-xxxxxxxx-...", "statut": "PENDING", ... }
# → Stocker cet UUID dans config.py USER_ID
```

---

## Opération quotidienne

### Démarrage normal

```bash
# Service systemd - démarrage auto
sudo systemctl start biolock-door.service

# Ou manuel
cd /home/pi/BioAccess-Secure/door-system
source venv/bin/activate
python3 main.py
```

### Feedback utilisateur

| État | LED Verte | LED Rouge | Signification |
|------|-----------|-----------|--------------|
| Prêt | ✓ Fixe | ✗ | Système actif, attente bouton |
| Capture | Fixe | ✗ | Face/voix en cours |
| Succès | Clignotante | ✗ | Auth réussie, porte s'ouvre |
| Échec | ✗ | Clignotante 2x | Auth échouée, tentative++ |
| Lockout | ✗ | ✓ Fixe | 3 tentatives, cooldown 60s |

### Logs

```bash
# Format: /var/log/biolock-door/biolock-door.log

# Exemple:
tail -f /var/log/biolock-door/biolock-door.log

# Via systemd
sudo journalctl -u biolock-door -f -n 50
sudo journalctl -u biolock-door --since "2025-01-01"
```

---

## Troubleshooting

### "Caméra non disponible"
```bash
# Vérifier caméra
ls -la /dev/video*

# Test OpenCV
python3 -c "import cv2; \
            cap = cv2.VideoCapture(0); \
            print('OK' if cap.isOpened() else 'ERREUR')"

# Relancer avec index différent
CAMERA_INDEX=1 python3 main.py
```

### "Backend inaccessible"
```bash
# Tester connexion
ping 192.168.1.100
curl http://192.168.1.100:5000/health

# Vérifier BACKEND_URL dans .env
# Vérifier pare-feu: sudo ufw allow 5000/tcp
```

### "Erreur GPIO"
```bash
# Vérifier GPIO en utilisation
gpio readall

# Libérer GPIO bloqués
sudo pkill -f "python3 main.py"
python3 -c "import RPi.GPIO; RPi.GPIO.cleanup()"
```

### "Microphone muet"
```bash
# Lister périphériques audio
arecord -l

# Test avec arecord
arecord -f cd -r 16000 -d 3 test.wav
aplay test.wav

# Vérifier volume
alsamixer
```

---

## Sécurité

### Variables sensibles

⚠️ **CRITIQUES à sécuriser:**
- `ADMIN_TOKEN` → Changer de la valeur par défaut
- `USER_ID` → Unique par porte
- `BACKEND_URL` → Accès restreint au réseau interne

```bash
# Permissions chmod
chmod 600 .env
chmod 700 *.py
sudo chown pi:pi -R /home/pi/door-system
```

### Réseau

- Backend et Pi sur même **sous-réseau local** (WiFi/Ethernet)
- Pas d'exposition internet directe
- Certificat SSL pour HTTPS (optionnel, mais recommandé)

### Logs

- Les tentatives échouées/réussies sont enregistrées
- Avec `source_type=DOOR` pour traçabilité
- Accessible via admin dashboard

---

## Performance et limites

| Métrique | Valeur |
|----------|--------|
| Temps capture face | ~3s |
| Temps capture voix | ~3s |
| Temps auth backend | ~1-2s |
| Temps total | ~6-8s |
| Tentatives avant lockout | 3 |
| Cooldown lockout | 60s |
| Résilience réseau | Retry x2, timeout 5s |
| Taille image base64 | ~50-100 KB |
| Taille audio base64 | ~30-50 KB |

---

## Fichiers de configuration détaillés

### config.py

| Variable | Défaut | Notes |
|----------|--------|-------|
| `BACKEND_URL` | `http://192.168.1.100:5000` | IP:PORT du backend |
| `USER_ID` | `uuid-de-l-utilisateur` | **À CHANGER** - UUID porte |
| `SERVO_PIN` | `18` | GPIO PWM servo (SG90) |
| `BUTTON_PIN` | `23` | GPIO bouton poussoir |
| `LED_GREEN_PIN` | `24` | GPIO LED verte prêt |
| `LED_RED_PIN` | `25` | GPIO LED rouge erreur |
| `CONFIDENCE_THRESHOLD` | `0.85` | Seuil confiance (0-1) |
| `MAX_ATTEMPTS` | `3` | Tentatives avant lockout |
| `COOLDOWN_SEC` | `60` | Durée coolout (secondes) |
| `REQUEST_TIMEOUT` | `5` | Timeout HTTP (s) |
| `FACE_CAPTURE_DURATION` | `3` | Durée capture face (s) |
| `VOICE_CAPTURE_DURATION` | `3` | Durée capture voix (s) |

---

## Support et contribution

Pour signaler des bugs ou contribuer:
- GitHub: https://github.com/agency-ni/BioAccess-Secure/
- Issues: Joindre logs (`journalctl -u biolock-door > logs.txt`)
- Config (masquée): `grep -v "TOKEN\|URL" .env`

---

## Licence

Voir `LICENSE.md` du projet BioAccess-Secure.

---

**Dernière mise à jour:** Avril 2025  
**Version:** 1.0.0  
**Compatibilité:** Raspberry Pi 4B/5, Debian 11/12, Python 3.10+
