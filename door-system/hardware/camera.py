"""
Service de capture faciale par caméra
Capture vidéo en temps réel, encodage base64, et envoi aud backend
"""

import cv2
import time
import base64
import logging
from pathlib import Path
from typing import Tuple, Optional
from config import (
    CAMERA_INDEX, FACE_CAPTURE_DURATION, LOG_LEVEL
)

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

class FaceCaptureService:
    """
    Service de capture faciale avec caméra USB/CSI
    Capture vidéo live et encodage base64
    """
    
    def __init__(self, camera_index=CAMERA_INDEX, capture_duration=FACE_CAPTURE_DURATION):
        """
        Initialise le service de capture faciale
        
        Args:
            camera_index: Index caméra (0 = défaut)
            capture_duration: Durée de capture en secondes
        """
        self.camera_index = camera_index
        self.capture_duration = capture_duration
        self.capture = None
        self.is_capturing = False
        self.face_cascade = None
        
        self._load_cascade_classifier()
        logger.info(f"FaceCaptureService initialisé - caméra: {camera_index}")
    
    def _load_cascade_classifier(self):
        """
        Charge le modèle de détection faciale Haar Cascade
        """
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                logger.warning("Haar Cascade non chargé - détection faciale désactivée")
                self.face_cascade = None
        except Exception as e:
            logger.error(f"Erreur chargement Haar Cascade: {e}")
            self.face_cascade = None
    
    def start_camera(self):
        """
        Démarre la caméra
        
        Returns:
            bool: True si succès
        """
        try:
            self.capture = cv2.VideoCapture(self.camera_index)
            
            if not self.capture.isOpened():
                logger.error(f"Impossible d'ouvrir la caméra {self.camera_index}")
                return False
            
            # Configuration caméra
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.capture.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_capturing = True
            logger.info("Caméra démarrée")
            return True
        
        except Exception as e:
            logger.error(f"Erreur démarrage caméra: {e}")
            return False
    
    def capture_face(self) -> Tuple[Optional[str], Optional[cv2.Mat]]:
        """
        Capture un visage pendant FACE_CAPTURE_DURATION secondes
        Détecte les visages et encode l'image base64
        
        Returns:
            (image_base64, frame) ou (None, None) en cas d'erreur
        """
        try:
            if not self.capture or not self.capture.isOpened():
                logger.error("Caméra non initialisée")
                return None, None
            
            frame = None
            face_detected = False
            start_time = time.time()
            
            logger.info(f"Capture en cours ({self.capture_duration}s)...")
            
            while (time.time() - start_time) < self.capture_duration:
                ret, frame = self.capture.read()
                
                if not ret:
                    logger.error("Impossible de lire frame")
                    continue
                
                # Détection faciale
                if self.face_cascade is not None:
                    faces = self.face_cascade.detectMultiScale(
                        frame, 1.3, 5, minSize=(50, 50)
                    )
                    
                    if len(faces) > 0:
                        face_detected = True
                        # Dessiner rectangle autour du visage
                        for (x, y, w, h) in faces:
                            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        logger.debug(f"Visage détecté: {len(faces)}")
                
                # Afficher frame en temps réel (optionnel)
                # cv2.imshow('Capture Faciale', frame)
                # if cv2.waitKey(1) & 0xFF == ord('q'):
                #     break
            
            # Utiliser la dernière frame capturée
            if frame is None:
                logger.error("Aucune frame capturée")
                return None, None
            
            # Encoder en base64
            _, buffer = cv2.imencode('.jpg', frame)
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            if not face_detected and self.face_cascade is not None:
                logger.warning("Aucun visage détecté pendant la capture")
            
            logger.info("Image encodée en base64")
            return image_base64, frame
        
        except Exception as e:
            logger.error(f"Erreur capture faciale: {e}")
            return None, None
    
    def stop_camera(self):
        """
        Arrête la caméra et libère les ressources
        """
        try:
            if self.capture:
                self.capture.release()
                self.capture = None
            
            cv2.destroyAllWindows()
            self.is_capturing = False
            logger.info("Caméra arrêtée")
        except Exception as e:
            logger.error(f"Erreur arrêt caméra: {e}")
    
    def __del__(self):
        """
        Destructeur pour libérer ressources
        """
        self.stop_camera()
