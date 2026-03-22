"""
Module de reconnaissance faciale
Capture et traitement avec OpenCV
"""

import cv2
import numpy as np
import base64
import io
import logging
from typing import Optional, Tuple
from config import CAMERA_ID, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS

logger = logging.getLogger(__name__)


class FaceRecognizer:
    """Gestionnaire de reconnaissance faciale avec OpenCV"""

    # Cascade classifier pour détection de visages (pré-entraîné dans OpenCV)
    CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

    def __init__(self):
        """Initialiser le classificateur"""
        try:
            self.face_cascade = cv2.CascadeClassifier(self.CASCADE_PATH)
            if self.face_cascade.empty():
                logger.error("Impossible de charger le cascade classifier")
                self.face_cascade = None
            logger.info("✓ Face recognizer initialisé")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation: {e}")
            self.face_cascade = None

    def is_available(self) -> bool:
        """Vérifier si le module est disponible"""
        return self.face_cascade is not None

    def start_camera(self) -> Optional[cv2.VideoCapture]:
        """
        Démarrer la capture vidéo
        
        Returns:
            cv2.VideoCapture ou None si erreur
        """
        try:
            cap = cv2.VideoCapture(CAMERA_ID)
            
            # Configurer la caméra
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer minimal pour images en direct
            
            # Vérifier si la caméra est accessible
            ret, frame = cap.read()
            if not ret:
                logger.error("Impossible d'accéder à la caméra")
                cap.release()
                return None
            
            logger.info(f"✓ Caméra démarrée (ID: {CAMERA_ID})")
            return cap
        
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la caméra: {e}")
            return None

    def read_frame(self, cap: cv2.VideoCapture) -> Optional[np.ndarray]:
        """
        Lire une frame de la caméra
        
        Args:
            cap: cv2.VideoCapture
            
        Returns:
            Image BGR ou None
        """
        if not cap or not cap.isOpened():
            return None
        
        ret, frame = cap.read()
        return frame if ret else None

    def detect_faces(self, frame: np.ndarray) -> list:
        """
        Détecter les visages dans une frame
        
        Args:
            frame: Image BGR
            
        Returns:
            Liste de tuples (x, y, w, h) pour chaque visage détecté
        """
        if self.face_cascade is None or frame is None:
            return []
        
        try:
            # Convertir en échelle de gris pour la détection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Détecter les visages
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                maxSize=(500, 500),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            return list(faces)
        
        except Exception as e:
            logger.error(f"Erreur lors de la détection: {e}")
            return []

    def capture_face(self, cap: cv2.VideoCapture, max_attempts: int = 30) -> Optional[np.ndarray]:
        """
        Capturer un visage clair
        
        Args:
            cap: cv2.VideoCapture
            max_attempts: Nombre maximum de frames à traiter
            
        Returns:
            Image du visage détecté (crop) ou None
        """
        if not cap or not cap.isOpened():
            logger.error("Caméra non disponible")
            return None
        
        logger.info("Capture de visage...")
        
        for attempt in range(max_attempts):
            frame = self.read_frame(cap)
            if frame is None:
                continue
            
            faces = self.detect_faces(frame)
            
            if len(faces) > 0:
                # Prendre le plus grand visage (probablement le principal)
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                
                # Extraire la région du visage avec du padding
                padding = 10
                x1 = max(0, x - padding)
                y1 = max(0, y - padding)
                x2 = min(frame.shape[1], x + w + padding)
                y2 = min(frame.shape[0], y + h + padding)
                
                face_roi = frame[y1:y2, x1:x2].copy()
                
                if face_roi.size > 0:
                    logger.info(f"✓ Visage capturé (tentative {attempt + 1})")
                    return face_roi
        
        logger.warning("Aucun visage détecté après plusieurs tentatives")
        return None

    def frame_with_detection(self, frame: np.ndarray, draw_boxes: bool = True) -> np.ndarray:
        """
        Ajouter des boîtes de détection sur la frame
        
        Args:
            frame: Image BGR
            draw_boxes: Si True, dessiner les boîtes
            
        Returns:
            Image annotée
        """
        if not draw_boxes or self.face_cascade is None:
            return frame.copy()
        
        try:
            frame_copy = frame.copy()
            faces = self.detect_faces(frame)
            
            for (x, y, w, h) in faces:
                # Dessiner un rectangle autour du visage
                cv2.rectangle(frame_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # Petit texte
                cv2.putText(frame_copy, 'Face', (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            return frame_copy
        
        except Exception as e:
            logger.error(f"Erreur lors de l'annotation: {e}")
            return frame.copy()

    @staticmethod
    def image_to_base64(image: np.ndarray) -> str:
        """
        Encoder une image OpenCV en base64
        
        Args:
            image: Image BGR (numpy array)
            
        Returns:
            Chaîne base64
        """
        try:
            # Encoder en JPEG
            success, buffer = cv2.imencode('.jpg', image, 
                                          [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            if not success:
                logger.error("Erreur lors de l'encodage JPEG")
                return ""
            
            # Convertir en base64
            img_base64 = base64.b64encode(buffer).decode('utf-8')
            return img_base64
        
        except Exception as e:
            logger.error(f"Erreur lors de la conversion base64: {e}")
            return ""

    @staticmethod
    def base64_to_image(data: str) -> Optional[np.ndarray]:
        """
        Décoder une image depuis base64
        
        Args:
            data: Chaîne base64
            
        Returns:
            Image BGR ou None
        """
        try:
            # Décoder depuis base64
            img_array = np.frombuffer(base64.b64decode(data), np.uint8)
            # Décoder depuis JPEG
            image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return image
        
        except Exception as e:
            logger.error(f"Erreur lors du décodage: {e}")
            return None

    @staticmethod
    def resize_frame(frame: np.ndarray, width: int = 640, height: int = 480) -> np.ndarray:
        """
        Redimensionner une frame
        
        Args:
            frame: Image BGR
            width: Largeur cible
            height: Hauteur cible
            
        Returns:
            Image redimensionnée
        """
        return cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)

    @staticmethod
    def stop_camera(cap: cv2.VideoCapture):
        """Fermer la caméra proprement"""
        if cap:
            cap.release()
            logger.info("✓ Caméra fermée")


# Instance globale
face_recognizer = FaceRecognizer()
