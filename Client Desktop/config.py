"""
Configuration du client desktop BioAccess Secure
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# ============ CONFIGURATION API ============
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000/api/v1')
API_TIMEOUT = int(os.getenv('API_TIMEOUT', 10))
API_KEY = os.getenv('API_KEY', 'your-api-key-here')

# ============ CONFIGURATION CAMÉRA ============
CAMERA_ID = int(os.getenv('CAMERA_ID', 0))
CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', 640))
CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', 480))
CAMERA_FPS = int(os.getenv('CAMERA_FPS', 30))

# ============ CONFIGURATION AUDIO ============
AUDIO_DURATION = int(os.getenv('AUDIO_DURATION', 5))  # secondes
AUDIO_SAMPLE_RATE = int(os.getenv('AUDIO_SAMPLE_RATE', 44100))

# ============ CONFIGURATION UI ============
WINDOW_WIDTH = int(os.getenv('WINDOW_WIDTH', 900))
WINDOW_HEIGHT = int(os.getenv('WINDOW_HEIGHT', 700))
THEME_COLOR = os.getenv('THEME_COLOR', '#2C3E50')
ACCENT_COLOR = os.getenv('ACCENT_COLOR', '#27AE60')
ERROR_COLOR = os.getenv('ERROR_COLOR', '#E74C3C')

# ============ TIMEOUTS ============
MAX_ATTEMPTS = int(os.getenv('MAX_ATTEMPTS', 3))
ATTEMPT_TIMEOUT = int(os.getenv('ATTEMPT_TIMEOUT', 300))  # 5 minutes en secondes
FACE_SCAN_TIMEOUT = int(os.getenv('FACE_SCAN_TIMEOUT', 30))  # secondes
VOICE_RECORD_TIMEOUT = int(os.getenv('VOICE_RECORD_TIMEOUT', 10))  # secondes

# ============ SEUILS BIOMÉTRIQUES ============
FACE_CONFIDENCE_THRESHOLD = float(os.getenv('FACE_CONFIDENCE_THRESHOLD', 0.7))
VOICE_CONFIDENCE_THRESHOLD = float(os.getenv('VOICE_CONFIDENCE_THRESHOLD', 0.7))

# ============ CHEMINS ============
LOGS_DIR = os.path.join(os.path.dirname(__file__), 'logs')
TEMP_DIR = os.path.join(os.path.dirname(__file__), 'temp')

# Créer les répertoires s'ils n'existent pas
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# ============ DEBUG ============
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
