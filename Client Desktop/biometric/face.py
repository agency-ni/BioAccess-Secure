"""
Module de reconnaissance faciale
Capture et traitement avec OpenCV
"""

import cv2
import numpy as np
import base64
import io
import logging
from typing import Optional, Tuple, Dict
from config import CAMERA_ID, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS

logger = logging.getLogger(__name__)


class CameraAccessError(Exception):
    """Exception levée quand l'accès à la caméra est refusé"""
    pass


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

    def start_camera(self, camera_id: int = CAMERA_ID) -> Optional[cv2.VideoCapture]:
        """
        Démarrer la capture vidéo
        
        Args:
            camera_id: ID de la caméra (défaut: config.CAMERA_ID)
        
        Returns:
            cv2.VideoCapture ou None si erreur
            
        Raises:
            CameraAccessError: Si l'accès est refusé
        """
        try:
            logger.info(f"Tentative d'accès à la caméra ID {camera_id}...")
            
            cap = cv2.VideoCapture(camera_id)
            
            # Vérifier si capture est ouverte
            if not cap.isOpened():
                logger.error(f"Impossible d'ouvrir la caméra ID {camera_id}")
                raise CameraAccessError(f"Caméra ID {camera_id} non accessible")
            
            # Configurer la caméra
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer minimal pour images en direct
            
            # Vérifier si on peut lire une frame
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.error("Impossible de lire une frame de la caméra")
                cap.release()
                raise CameraAccessError("Impossible de lire depuis la caméra - vérifier les permissions")
            
            logger.info(f"✓ Caméra démarrée (ID: {camera_id})")
            return cap
        
        except CameraAccessError as e:
            logger.error(f"Erreur d'accès caméra: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de la caméra: {e}")
            raise CameraAccessError(f"Erreur système: {e}")
    
    def try_alternative_cameras(self, max_attempts: int = 5) -> Optional[cv2.VideoCapture]:
        """
        Essayer différentes caméras en cas d'échec
        
        Args:
            max_attempts: Nombre max de caméras à tester
            
        Returns:
            cv2.VideoCapture si trouvée, None sinon
        """
        logger.info(f"Recherche de caméra alternative...")
        
        for camera_id in range(max_attempts):
            try:
                logger.debug(f"Test caméra ID {camera_id}...")
                cap = self.start_camera(camera_id)
                if cap:
                    logger.info(f"✓ Caméra alternative trouvée: ID {camera_id}")
                    return cap
            except CameraAccessError:
                continue
            except Exception as e:
                logger.debug(f"Erreur avec caméra {camera_id}: {e}")
                continue
        
        logger.error("Aucune caméra alternative trouvée")
        return None
    
    def get_camera_info(self, camera_id: int = CAMERA_ID) -> Dict:
        """
        Obtenir les informations sur une caméra
        
        Returns:
            Dict avec les informations de la caméra
        """
        info = {
            'camera_id': camera_id,
            'available': False,
            'width': 0,
            'height': 0,
            'fps': 0,
            'error': None
        }
        
        try:
            cap = cv2.VideoCapture(camera_id)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    info['available'] = True
                    info['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    info['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    info['fps'] = int(cap.get(cv2.CAP_PROP_FPS))
                else:
                    info['error'] = "Impossible de lire une frame"
            else:
                info['error'] = "Caméra non accessible"
            cap.release()
        except Exception as e:
            info['error'] = str(e)
        
        return info

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
