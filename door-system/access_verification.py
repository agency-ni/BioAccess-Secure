"""
Module de vérification d'accès pour Door-System Raspberry Pi
Vérifie après authentification si l'utilisateur peut ouvrir la porte
(en fonction des alertes de sécurité)

Intégration avec alerts.py du backend
Endpoints:
  - GET /api/v1/alerts/access/check/{user_id}
  - GET /api/v1/alerts/access/status/{user_id}
"""

import logging
import requests
from typing import Dict, Tuple, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class DoorAccessVerifier:
    """
    Vérifie l'accès à la porte après authentification biométrique
    Appelle le backend pour vérifier les alertes de sécurité actives
    """
    
    def __init__(self, backend_url: str, timeout: int = 5, max_retries: int = 2):
        """
        Initialise le vérificateur d'accès pour porte
        
        Args:
            backend_url: URL base API (ex: http://192.168.1.100:5000)
            timeout: Timeout requêtes en secondes (recommandé: 5)
            max_retries: Nombre de retries en cas d'erreur réseau (défaut: 2)
        """
        self.backend_url = backend_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger(__name__)
    
    def check_door_access(self, user_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Vérifie si un utilisateur peut ouvrir la porte
        APPEL CRITIQUE après authentification biométrique réussie (facial + vocal)
        
        Résistance réseau:
          - Timeout: 5 secondes par requête
          - Retry: 2 tentatives si timeout/erreur réseau
          - Fail-closed: Porte reste fermée en cas d'erreur
        
        Args:
            user_id: UUID de l'utilisateur (retourné par /auth/face)
        
        Returns:
            Tuple (allowed: bool, reason: str, alert_details: dict|None)
            - allowed: True = porte peut ouvrir, False = porte bloquée
            - reason: Message d'explication
            - alert_details: Détails de l'alerte si bloquée
        
        Exemple:
            allowed, reason, alert = verifier.check_door_access(user_id)
            if allowed:
                servo.open_door()  # Ouvrir la porte
                led_green.blink()
            else:
                led_red.on()  # LED rouge = refusé
                logger.warning(f"Porte bloquée: {reason}")
        """
        
        # Retry logic avec délai
        last_error = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # Construire l'URL
                endpoint = f"/api/v1/alerts/access/check/{user_id}"
                url = f"{self.backend_url}{endpoint}"
                
                self.logger.debug(f"Vérification accès porte [tentative {attempt}/{self.max_retries}]: {url}")
                
                # Appeler le backend
                response = requests.get(
                    url,
                    headers={'Content-Type': 'application/json'},
                    timeout=self.timeout,
                    verify=False  # Accepter certificats auto-signés (porte locale)
                )
                
                # Traiter réponse
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('success') is False:
                        self.logger.warning(f"API returned success=false for user {user_id}")
                        return False, data.get('message', 'Erreur serveur'), None
                    
                    api_data = data.get('data', {})
                    allowed = api_data.get('allowed', False)
                    reason = api_data.get('reason', '')
                    
                    if allowed:
                        self.logger.info(f"Accès PORTE AUTORISÉ pour {user_id}")
                        return True, reason, None
                    else:
                        # Accès BLOQUÉ
                        alert_details = {
                            'alert_id': api_data.get('alert_id'),
                            'alert_title': api_data.get('alert_title', 'Alerte de sécurité'),
                            'resource_blocked': api_data.get('resource_blocked', 'porte'),
                        }
                        self.logger.warning(f"Accès PORTE BLOQUÉ pour {user_id}: {reason}")
                        return False, reason, alert_details
                
                else:
                    self.logger.error(f"Erreur API {response.status_code} tentative {attempt}")
                    last_error = f"HTTP {response.status_code}"
                    
                    if attempt < self.max_retries:
                        time.sleep(1)  # Attendre 1s avant retry
                        continue
            
            except requests.Timeout as e:
                self.logger.warning(f"Timeout vérification porte [tentative {attempt}]: {e}")
                last_error = f"Timeout ({self.timeout}s)"
                
                if attempt < self.max_retries:
                    time.sleep(1)
                    continue
            
            except requests.ConnectionError as e:
                self.logger.warning(f"Erreur connexion [tentative {attempt}]: {e}")
                last_error = "Erreur connexion"
                
                if attempt < self.max_retries:
                    time.sleep(1)
                    continue
            
            except Exception as e:
                self.logger.error(f"Exception vérification porte [tentative {attempt}]: {e}")
                last_error = str(e)
                
                if attempt < self.max_retries:
                    time.sleep(1)
                    continue
        
        # Tous les retries échoués -> Fail-closed
        error_msg = f"Erreur serveur après {self.max_retries} tentatives: {last_error}"
        self.logger.error(error_msg)
        return False, error_msg, None
    
    def log_door_attempt(self, 
                        user_id: str, 
                        access_allowed: bool, 
                        facial_confidence: float,
                        voice_confidence: float,
                        reason: str):
        """
        Enregistre une tentative d'ouverture de porte
        (utile pour debugging)
        
        Args:
            user_id: ID utilisateur
            access_allowed: Résultat (True/False)
            facial_confidence: Score facial
            voice_confidence: Score vocal
            reason: Raison du résultat
        """
        status = "✅ AUTORISÉ" if access_allowed else "❌ BLOQUÉ"
        log_msg = (
            f"[{datetime.now().isoformat()}] Tentative porte:\n"
            f"  User: {user_id}\n"
            f"  Facial: {facial_confidence:.2%}\n"
            f"  Vocal: {voice_confidence:.2%}\n"
            f"  Statut: {status}\n"
            f"  Raison: {reason}"
        )
        self.logger.info(log_msg)


# ============================================================
# INTÉGRATION AVEC MAIN.PY DU DOOR-SYSTEM
# ============================================================

def example_door_system_integration():
    """
    Exemple d'utilisation dans main.py du door-system
    Montre la séquence complète: capture → auth → vérification accès → ouvrir/bloquer
    """
    from api_client import DoorSystemAPIClient
    
    # Initialiser API client et access verifier
    api_client = DoorSystemAPIClient(
        backend_url="http://192.168.1.100:5000",
        timeout=5
    )
    
    access_verifier = DoorAccessVerifier(
        backend_url="http://192.168.1.100:5000",
        timeout=5,
        max_retries=2
    )
    
    # Simuler une tentative d'ouverture de porte
    print("[Door-System] Détection mouvement → démarrage capture...")
    
    # Étape 1: Capturer facial
    facial_image_b64 = capture_facial()  # À implémenter
    
    # Étape 2: Capturer vocal
    voice_audio_b64 = capture_voice()  # À implémenter
    
    # Étape 3: Authentification faciale
    print("[1/4] Authentification faciale...")
    face_response = api_client.auth_face(
        user_id="",  # Vide au départ
        image_b64=facial_image_b64,
        source="DOOR"
    )
    
    if not face_response.get('success'):
        print(f"❌ Facial échoué: {face_response.get('error')}")
        led_red.on()  # LED rouge
        return
    
    user_id = face_response.get('data', {}).get('user_id')
    facial_confidence = face_response.get('data', {}).get('confidence', 0)
    print(f"✅ Facial OK (confidence: {facial_confidence:.2%})")
    
    # Étape 4: Authentification vocale
    print("[2/4] Authentification vocale...")
    voice_response = api_client.auth_voice(
        user_id=user_id,
        audio_b64=voice_audio_b64,
        source="DOOR"
    )
    
    if not voice_response.get('success'):
        print(f"❌ Vocal échoué: {voice_response.get('error')}")
        led_red.on()
        return
    
    voice_confidence = voice_response.get('data', {}).get('confidence', 0)
    print(f"✅ Vocal OK (confidence: {voice_confidence:.2%})")
    
    # Étape 5: VÉRIFICATION ACCÈS (NOUVEAU - CRITIQUE)
    print("[3/4] Vérification d'accès (alertes)...")
    access_allowed, reason, alert_details = access_verifier.check_door_access(user_id)
    
    # Log la tentative
    access_verifier.log_door_attempt(
        user_id=user_id,
        access_allowed=access_allowed,
        facial_confidence=facial_confidence,
        voice_confidence=voice_confidence,
        reason=reason
    )
    
    if not access_allowed:
        # ❌ ACCÈS REFUSÉ
        print(f"❌ ACCÈS PORTE REFUSÉ: {reason}")
        if alert_details:
            print(f"   Alerte: {alert_details.get('alert_title')}")
        
        # Affichage LED rouge
        led_red.on()
        speaker.play_tone(frequency=500, duration=2)  # Son d'erreur
        
        # Attendre 5 secondes avant réinitialisation
        time.sleep(5)
        led_red.off()
        return
    
    # ✅ ACCÈS AUTORISÉ
    print(f"✅ ACCÈS PORTE AUTORISÉ: {reason}")
    
    # Étape 6: Ouvrir la porte
    print("[4/4] Ouverture de la porte...")
    
    # LED verte clignotante
    led_green.blink(interval=0.5, count=3)
    
    # Son de succès
    speaker.play_tone(frequency=1000, duration=1)
    
    # Ouvrir la porte
    servo.open_door()
    
    # Rester ouvert 5 secondes
    time.sleep(5)
    
    # Fermer la porte
    servo.close_door()
    
    print("✅ Porte fermée - Séquence terminée")
    
    # LED vert fixe (prêt)
    led_green.on()
    time.sleep(2)
    led_green.off()


# ============================================================
# STRUCTURE MAIN.PY SIMPLIFIÉ
# ============================================================

def main_door_system():
    """
    Boucle principale du door-system
    """
    import GPIO
    from hardware.servo_control import ServoControl
    from hardware.camera import Camera
    from hardware.microphone import Microphone
    from hardware.leds import LEDControl
    
    # Initialiser le matériel
    print("[Boot] Initialisation door-system...")
    
    servo = ServoControl()
    camera = Camera()
    microphone = Microphone()
    led_green = LEDControl(pin=24)  # GPIO 24
    led_red = LEDControl(pin=25)    # GPIO 25
    button = GPIO.Button(pin=23)    # GPIO 23
    
    # LED verte = système prêt
    led_green.on()
    print("✅ Door-System prêt")
    
    # Boucle principale
    while True:
        # Attendre déclenchement (bouton ou mouvement)
        if button.is_pressed():
            print("\n🔔 Déclenchement détecté")
            
            # Appeler la séquence d'authentification avec accès
            example_door_system_integration()
        
        time.sleep(0.5)
