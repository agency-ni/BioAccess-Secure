"""
Configuration BioLock Door System pour Raspberry Pi
Variables globales et paramètres d'exécution
"""

import os
from dotenv import load_dotenv

# Charger variables d'environnement depuis .env
load_dotenv()

# ============================================================
# CONFIGURATION BACKEND
# ============================================================

BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:5000')
ADMIN_TOKEN = os.getenv('ADMIN_TOKEN', 'CHANGE_ME')
USER_ID = os.getenv('USER_ID', 'uuid-de-l-utilisateur')

# ============================================================
# CONFIGURATION MATÉRIEL GPIO
# ============================================================

# Broches GPIO
SERVO_PIN = int(os.getenv('SERVO_PIN', 18))
BUTTON_PIN = int(os.getenv('BUTTON_PIN', 23))
LED_GREEN_PIN = int(os.getenv('LED_GREEN_PIN', 24))
LED_RED_PIN = int(os.getenv('LED_RED_PIN', 25))
MOTION_SENSOR_PIN = int(os.getenv('MOTION_SENSOR_PIN', 27))

# ============================================================
# CONFIGURATION SERVO
# ============================================================

OPEN_ANGLE = int(os.getenv('OPEN_ANGLE', 90))
CLOSED_ANGLE = int(os.getenv('CLOSED_ANGLE', 0))
OPEN_DURATION = int(os.getenv('OPEN_DURATION', 5))
SERVO_FREQUENCY = int(os.getenv('SERVO_FREQUENCY', 50))

# ============================================================
# CONFIGURATION AUTHENTIFICATION
# ============================================================

MAX_ATTEMPTS = int(os.getenv('MAX_ATTEMPTS', 3))
COOLDOWN_SEC = int(os.getenv('COOLDOWN_SEC', 60))
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.85))

# ============================================================
# CONFIGURATION RÉSEAU
# ============================================================

REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 5))
RETRY_COUNT = int(os.getenv('RETRY_COUNT', 2))
RETRY_DELAY = int(os.getenv('RETRY_DELAY', 1))

# ============================================================
# CONFIGURATION CAPTURE
# ============================================================

FACE_CAPTURE_DURATION = int(os.getenv('FACE_CAPTURE_DURATION', 3))
VOICE_CAPTURE_DURATION = int(os.getenv('VOICE_CAPTURE_DURATION', 3))
CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
MICROPHONE_INDEX = int(os.getenv('MICROPHONE_INDEX', -1))
SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', 16000))
AUDIO_CHANNELS = int(os.getenv('AUDIO_CHANNELS', 1))

# ============================================================
# CONFIGURATION LOGGING
# ============================================================

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = os.getenv('LOG_DIR', '/var/log/biolock-door')
LOG_FILE = os.path.join(LOG_DIR, 'biolock-door.log')

# ============================================================
# CONSTANTES
# ============================================================

SOURCE_TYPE = 'DOOR'
API_VERSION = 'v1'
APP_NAME = 'BioLock Door System'
APP_VERSION = '1.0.0'
