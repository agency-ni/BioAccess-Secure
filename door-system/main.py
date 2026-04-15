"""
Programme principal BioLock Door System
Orchestration complète: GPIO setup → attente → auth → porte
"""

import signal
import sys
import logging
import time
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
from config import (
    USER_ID, BUTTON_PIN, LED_GREEN_PIN, LED_RED_PIN, MOTION_SENSOR_PIN,
    MAX_ATTEMPTS, COOLDOWN_SEC, CONFIDENCE_THRESHOLD, LOG_LEVEL, LOG_FILE, LOG_DIR
)
from hardware.servo_control import ServoControl
from api_client import BioAccessAPIClient
from face_auth import FaceAuthenticationFlow
from voice_auth import VoiceAuthenticationFlow
import os

# ============================================================
# CONFIGURATION LOGGING
# ============================================================

# Créer répertoire logs s'il n'existe pas
os.makedirs(LOG_DIR, exist_ok=True)

# Configuration logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ============================================================
# CLASSE PRINCIPALE APPLICATON
# ============================================================

class BioLockDoorSystem:
    """
    Système complet de porte biométrique pour Raspberry Pi
    """
    
    def __init__(self):
        """Initialise tous les composants"""
        logger.info("=" * 60)
        logger.info("BioLock Door System démarrage")
        logger.info("=" * 60)
        
        # Vérifier user_id
        if USER_ID == 'uuid-de-l-utilisateur' or not USER_ID:
            logger.error("USER_ID non configuré dans config.py")
            sys.exit(1)
        
        # Composants matériel
        self.servo = ServoControl()
        self.api_client = BioAccessAPIClient()
        self.face_auth = FaceAuthenticationFlow(self.api_client)
        self.voice_auth = VoiceAuthenticationFlow(self.api_client)
        
        # État application
        self.running = True
        self.attempt_count = 0
        self.lockout_until = None
        self.is_initialization_complete = False
        
        logger.info(f"USER_ID: {USER_ID}")
    
    def setup_gpio(self):
        """
        Configure tous les GPIO
        - Bouton d'activation (GPIO 23)
        - LED verte prêt (GPIO 24)
        - LED rouge erreur (GPIO 25)
        - Détecteur mouvement (GPIO 27)
        """
        try:
            logger.info("Configuration GPIO...")
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Bouton input (pull-up)
            GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # LEDs output
            GPIO.setup(LED_GREEN_PIN, GPIO.OUT)
            GPIO.setup(LED_RED_PIN, GPIO.OUT)
            
            # Détecteur mouvement input
            GPIO.setup(MOTION_SENSOR_PIN, GPIO.IN)
            
            # Initialiser le servo
            if not self.servo.setup():
                logger.error("Impossible d'initialiser le servo")
                return False
            
            # Ajouter détecteur de bouton
            GPIO.add_event_detect(
                BUTTON_PIN,
                GPIO.FALLING,
                callback=self._on_button_press,
                bouncetime=300
            )
            
            logger.info("GPIO configuré avec succès")
            return True
        
        except Exception as e:
            logger.error(f"Erreur setup GPIO: {e}")
            return False
    
    def led_green_on(self):
        """Allume LED verte (système prêt)"""
        GPIO.output(LED_GREEN_PIN, GPIO.HIGH)
    
    def led_green_off(self):
        """Éteint LED verte"""
        GPIO.output(LED_GREEN_PIN, GPIO.LOW)
    
    def led_red_on(self):
        """Allume LED rouge (erreur)"""
        GPIO.output(LED_RED_PIN, GPIO.HIGH)
    
    def led_red_off(self):
        """Éteint LED rouge"""
        GPIO.output(LED_RED_PIN, GPIO.LOW)
    
    def led_red_blink(self, count=5, duration=0.5):
        """
        Fait clignoter LED rouge
        
        Args:
            count: Nombre de clignotements
            duration: Durée chaque cycle (on+off)
        """
        for _ in range(count):
            if not self.running:
                break
            
            self.led_red_on()
            time.sleep(duration / 2)
            self.led_red_off()
            time.sleep(duration / 2)
    
    def led_green_blink(self, count=3):
        """
        Fait clignoter LED verte (succès d'authentification)
        """
        for _ in range(count):
            if not self.running:
                break
            
            self.led_green_on()
            time.sleep(0.3)
            self.led_green_off()
            time.sleep(0.3)
        
        self.led_green_on()
    
    def check_lockout(self):
        """
        Vérifie si le système est en cooldown après 3 tentatives échouées
        
        Returns:
            bool: True si verrouillé, False sinon
        """
        if self.lockout_until and datetime.now() < self.lockout_until:
            remaining = (self.lockout_until - datetime.now()).total_seconds()
            minutes = int(remaining // 60)
            seconds = int(remaining % 60)
            
            logger.warning(f"Système verrouillé - {minutes}m{seconds}s restantes")
            self.led_red_on()
            
            return True
        
        if self.lockout_until:
            logger.info("Cooldown terminé, système réactivé")
            self.attempt_count = 0
            self.lockout_until = None
            self.led_red_off()
        
        return False
    
    def _on_button_press(self, channel):
        """Callback quand le bouton est appuyé"""
        logger.info("Bouton appuyé")
        
        if not self.running:
            return
        
        if self.check_lockout():
            return
        
        self.trigger_authentication()
    
    def motion_detected(self):
        """
        Vérifie si le détecteur de mouvement détecte une personne
        
        Returns:
            bool: True si mouvement détecté
        """
        return GPIO.input(MOTION_SENSOR_PIN) == GPIO.HIGH
    
    def trigger_authentication(self):
        """
        Déclenche le pipeline complet d'authentification
        Capture face + voix → auth → ouverture porte si succès
        """
        logger.info("=" * 60)
        logger.info("Déclenchement authentification...")
        logger.info("=" * 60)
        
        if self.check_lockout():
            logger.warning("Système verrouillé - tentative rejetée")
            self.led_red_blink(count=3)
            return
        
        # Affordance utilisateur
        self.led_green_off()
        self.led_red_off()
        
        face_result = None
        voice_result = None
        
        try:
            # ============================================================
            # ÉTAPE 1: Authentification faciale
            # ============================================================
            logger.info("ÉTAPE 1: Authentification faciale (3s)")
            self.led_green_on()
            
            face_result = self.face_auth.authenticate(USER_ID)
            
            logger.info(f"Résultat facial: success={face_result.success}, "
                       f"confiance={face_result.confidence:.2%}")
            
            # ============================================================
            # ÉTAPE 2: Authentification vocale
            # ============================================================
            logger.info("ÉTAPE 2: Authentification vocale (3s)")
            
            voice_result = self.voice_auth.authenticate(USER_ID)
            
            logger.info(f"Résultat vocal: success={voice_result.success}, "
                       f"confiance={voice_result.confidence:.2%}")
            
            # ============================================================
            # ÉTAPE 3: Vérification seuils ET logique biométrique multi-facteur
            # ============================================================
            face_ok = face_result.success and face_result.confidence >= CONFIDENCE_THRESHOLD
            voice_ok = voice_result.success and voice_result.confidence >= CONFIDENCE_THRESHOLD
            
            logger.info(f"Analyse: Face OK={face_ok} ({face_result.confidence:.2%}), "
                       f"Voice OK={voice_ok} ({voice_result.confidence:.2%})")
            
            # SUCCÈS: Les deux facteurs doivent être >= 0.85
            if face_ok and voice_ok:
                logger.info("✓ AUTHENTIFICATION RÉUSSIE")
                
                self.attempt_count = 0
                self.lockout_until = None
                
                # Feedback utilisateur
                self.led_red_off()
                logger.info("LED verte clignotante - Ouverture porte...")
                self.led_green_blink(count=3)
                
                # Ouvrir porte
                logger.info("Ouverture porte (5s)...")
                if self.servo.open_door():
                    logger.info("✓ Porte ouverte et fermée avec succès")
                else:
                    logger.error("✗ Erreur ouverture porte")
                
                self.led_green_on()
            
            # ÉCHEC
            else:
                self.attempt_count += 1
                reason_list = []
                
                if not face_ok:
                    reason = f"visage (confiance: {face_result.confidence:.2%})"
                    reason_list.append(reason)
                
                if not voice_ok:
                    reason = f"voix (confiance: {voice_result.confidence:.2%})"
                    reason_list.append(reason)
                
                reason_str = ", ".join(reason_list)
                logger.warning(f"✗ Authentification échouée: {reason_str} "
                              f"({self.attempt_count}/{MAX_ATTEMPTS} tentatives)")
                
                # Feedback utilisateur
                self.led_green_off()
                self.led_red_blink(count=2)
                
                # Vérifier lockout
                if self.attempt_count >= MAX_ATTEMPTS:
                    self.lockout_until = datetime.now() + timedelta(seconds=COOLDOWN_SEC)
                    logger.error(f"✗ LOCKOUT ACTIVÉ - Cooldown {COOLDOWN_SEC}s")
                    self.led_red_on()
                else:
                    remaining = MAX_ATTEMPTS - self.attempt_count
                    logger.info(f"Tentatives restantes: {remaining}")
                    self.led_red_off()
                    self.led_green_on()
        
        except KeyboardInterrupt:
            logger.info("Interruption utilisateur")
            raise
        
        except Exception as e:
            logger.error(f"Erreur pipeline authentification: {e}")
            self.led_red_blink(count=5, duration=0.2)
            self.led_green_on()
        
        finally:
            # Nettoyer ressources
            try:
                self.face_auth.cleanup()
            except:
                pass
    
    def run(self):
        """
        Boucle principale d'exécution
        Attente bouton → authentification → boucle
        """
        logger.info("Test connexion backend...")
        
        if not self.api_client.test_connection():
            logger.error("Backend inaccessible - vérifier BACKEND_URL et réseau")
            self.led_red_on()
            return
        
        logger.info("✓ Connexion backend OK")
        
        # Initialisation GPIO
        if not self.setup_gpio():
            logger.error("Impossible d'initialiser GPIO")
            return
        
        # Afficher prêt
        self.led_green_on()
        self.is_initialization_complete = True
        
        logger.info("✓ Système prêt - En attente...")
        logger.info(f"Bouton: GPIO {BUTTON_PIN} | Servo: GPIO {SERVO_PIN}")
        logger.info("Appuyez sur le bouton pour déclencher l'authentification")
        
        try:
            # Boucle attente
            while self.running:
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            logger.info("Arrêt demandé (Ctrl+C)")
        
        except Exception as e:
            logger.error(f"Erreur boucle principale: {e}")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Nettoie toutes les ressources avant arrêt"""
        logger.info("Nettoyage ressources...")
        
        self.running = False
        
        try:
            self.led_green_off()
            self.led_red_off()
            self.servo.cleanup()
            GPIO.cleanup()
        except Exception as e:
            logger.error(f"Erreur cleanup: {e}")
        
        logger.info("=" * 60)
        logger.info("BioLock Door System arrêté")
        logger.info("=" * 60)
    
    def signal_handler(self, sig, frame):
        """Gère les signaux système (SIGINT, SIGTERM)"""
        logger.info(f"Signal reçu: {sig}")
        self.cleanup()
        sys.exit(0)

# ============================================================
# POINT D'ENTRÉE
# ============================================================

if __name__ == '__main__':
    system = BioLockDoorSystem()
    
    # Gérer signaux système
    signal.signal(signal.SIGINT, system.signal_handler)
    signal.signal(signal.SIGTERM, system.signal_handler)
    
    # Démarrer
    system.run()
