"""
Contrôle du servomoteur pour la serrure électronique
GPIO setup, PWM, et gestion des angles d'ouverture/fermeture
"""

import RPi.GPIO as GPIO
import time
import logging
from config import (
    SERVO_PIN, OPEN_ANGLE, CLOSED_ANGLE, OPEN_DURATION,
    SERVO_FREQUENCY, LOG_LEVEL
)

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

class ServoControl:
    """
    Contrôleur servomoteur pour porte biométrique
    Gère la rotation et la durée d'ouverture
    """
    
    def __init__(self, servo_pin=SERVO_PIN, frequency=SERVO_FREQUENCY):
        """
        Initialise le contrôleur servo
        
        Args:
            servo_pin: Numéro de la broche GPIO (défaut 18)
            frequency: Fréquence PWM en Hz (défaut 50)
        """
        self.servo_pin = servo_pin
        self.frequency = frequency
        self.pwm = None
        self.is_open = False
        
        logger.info(f"ServoControl initialisé - PIN: {servo_pin}, Fréquence: {frequency}Hz")
    
    def setup(self):
        """
        Configure GPIO pour le servo
        Mode BCM, sortie, PWM
        """
        try:
            # Configuration GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.servo_pin, GPIO.OUT)
            
            # Configuration PWM (50Hz standard pour servo)
            self.pwm = GPIO.PWM(self.servo_pin, self.frequency)
            self.pwm.start(0)
            
            logger.info("GPIO et PWM configurés avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur setup GPIO: {e}")
            return False
    
    def angle_to_duty_cycle(self, angle):
        """
        Convertit un angle en rapport de cycle PWM
        Formule: duty = 2 + (angle / 18)
        
        Args:
            angle: Angle en degrés (0-180)
            
        Returns:
            Rapport de cycle PWM (2-12)
        """
        if angle < 0 or angle > 180:
            angle = max(0, min(180, angle))
        
        # Conversion: 0° = 2%, 90° = 7%, 180° = 12%
        duty_cycle = 2 + (angle / 18)
        return round(duty_cycle, 2)
    
    def set_angle(self, angle):
        """
        Positionne le servo à un angle spécifique
        
        Args:
            angle: Angle en degrés (0-180)
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            if not self.pwm:
                logger.error("PWM non initialisé")
                return False
            
            duty_cycle = self.angle_to_duty_cycle(angle)
            self.pwm.ChangeDutyCycle(duty_cycle)
            time.sleep(0.5)  # Attendre stabilisation
            
            logger.debug(f"Servo positionné à {angle}° (duty={duty_cycle}%)")
            return True
        except Exception as e:
            logger.error(f"Erreur positionnement servo: {e}")
            return False
    
    def open_door(self):
        """
        Ouvre la porte en positionnant le servo à OPEN_ANGLE
        Attend OPEN_DURATION secondes
        Ferme automatiquement
        
        Returns:
            bool: True si succès
        """
        try:
            logger.info(f"Ouverture porte ({OPEN_ANGLE}°)...")
            
            if not self.set_angle(OPEN_ANGLE):
                logger.error("Impossible de positionner le servo")
                return False
            
            self.is_open = True
            logger.info(f"Porte ouverte - Fermeture dans {OPEN_DURATION}s")
            
            # Attendre avant fermeture
            time.sleep(OPEN_DURATION)
            
            # Fermer automatiquement
            self.close_door()
            return True
        
        except Exception as e:
            logger.error(f"Erreur ouverture porte: {e}")
            return False
    
    def close_door(self):
        """
        Ferme la porte en positionnant le servo à CLOSED_ANGLE
        
        Returns:
            bool: True si succès
        """
        try:
            logger.info(f"Fermeture porte ({CLOSED_ANGLE}°)...")
            
            if not self.set_angle(CLOSED_ANGLE):
                logger.error("Impossible de fermer la porte")
                return False
            
            self.is_open = False
            logger.info("Porte fermée")
            return True
        
        except Exception as e:
            logger.error(f"Erreur fermeture porte: {e}")
            return False
    
    def cleanup(self):
        """
        Arrête le PWM et libère les ressources GPIO
        À appeler avant l'arrêt du programme
        """
        try:
            if self.pwm:
                self.pwm.stop()
            
            # Fermer la porte avant cleanup
            self.set_angle(CLOSED_ANGLE)
            time.sleep(0.3)
            
            GPIO.cleanup(self.servo_pin)
            logger.info("GPIO nettoyé et ressources libérées")
        except Exception as e:
            logger.error(f"Erreur cleanup: {e}")
