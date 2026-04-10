"""
Service de capture faciale intégrant MUSE
Wrapper pour intégration de la reconnaissance faciale locale avec le backend BioAccess-Secure

Architecture:
    - Capture vidéo temps réel
    - Encodage facial via MUSE
    - Communication avec API backend
    - Gestion cache et persistance locale
"""

import cv2
import os
import numpy as np
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import threading
import queue
import base64
import io

# Imports MUSE
try:
    from muse.easy_facial_recognition import encode_face, easy_face_reco
    MUSE_AVAILABLE = True
except ImportError:
    MUSE_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class FaceDetectionResult:
    """Résultat d'une détection faciale"""
    success: bool
    face_encoding: Optional[np.ndarray] = None
    face_location: Optional[Tuple] = None
    quality_score: Optional[float] = None
    landmarks: Optional[np.ndarray] = None
    timestamp: datetime = None
    error_message: str = None


class LocalFaceCaptureService:
    """
    Service de capture et encodage facial local
    Utilise MUSE pour traitement optimisé local avant envoi backend
    """
    
    def __init__(self, camera_index: int = 0, model_path: str = None):
        """
        Initialise le service de capture faciale
        
        Args:
            camera_index: Index de la caméra (0 = défaut)
            model_path: Chemin vers les modèles dlib (utilise ./muse/pretrained_model par défaut)
        """
        if not MUSE_AVAILABLE:
            raise RuntimeError("MUSE not available. Install required dependencies.")
        
        self.camera_index = camera_index
        self.model_path = model_path or self._get_model_path()
        
        # Vérifier modèles disponibles
        if not self._validate_models():
            raise FileNotFoundError(f"Modèles dlib non trouvés à {self.model_path}")
        
        # État capture
        self.capture = None
        self.is_capturing = False
        self.frame_buffer = queue.Queue(maxsize=10)
        self.capture_thread = None
        
        # Cache encodages
        self.cached_encodings = {}
        self.last_detection_time = None
        
        logger.info(f"FaceCaptureService initialized with camera {camera_index}")
    
    def _get_model_path(self) -> str:
        """Retourne le chemin par défaut vers les modèles dlib"""
        current_dir = Path(__file__).parent
        muse_models = current_dir / "muse" / "pretrained_model"
        return str(muse_models)
    
    def _validate_models(self) -> bool:
        """Valide la présence des modèles dlib requis"""
        required_models = [
            "dlib_face_recognition_resnet_model_v1.dat",
            "shape_predictor_68_face_landmarks.dat",
            "shape_predictor_5_face_landmarks.dat"
        ]
        
        model_dir = Path(self.model_path)
        for model in required_models:
            if not (model_dir / model).exists():
                logger.error(f"Modèle manquant: {model}")
                return False
        return True
    
    def start_camera(self) -> bool:
        """
        Démarre la capture vidéo et le thread de traitement
        
        Returns:
            bool: True si succès, False sinon
        """
        try:
            self.capture = cv2.VideoCapture(self.camera_index)
            
            if not self.capture.isOpened():
                logger.error(f"Impossible d'ouvrir la caméra {self.camera_index}")
                return False
            
            # Configurer propriétés caméra
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.capture.set(cv2.CAP_PROP_FPS, 30)
            
            # Démarrer thread capture
            self.is_capturing = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.capture_thread.start()
            
            logger.info("Capture vidéo démarrée")
            return True
            
        except Exception as e:
            logger.error(f"Erreur démarrage caméra: {e}")
            return False
    
    def stop_camera(self):
        """Arrête la capture vidéo"""
        self.is_capturing = False
        
        if self.capture:
            self.capture.release()
            self.capture = None
        
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        
        logger.info("Capture vidéo arrêtée")
    
    def _capture_loop(self):
        """Boucle de capture vidéo (exécutée dans un thread)"""
        while self.is_capturing and self.capture:
            ret, frame = self.capture.read()
            
            if not ret:
                logger.warning("Erreur lecture frame")
                continue
            
            try:
                # Ajouter au buffer (descarte les anciens frames si plein)
                self.frame_buffer.put_nowait(frame)
            except queue.Full:
                pass
    
    def capture_frame(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """
        Capture le dernier frame disponible
        
        Args:
            timeout: Timeout en secondes
            
        Returns:
            Frame (np.ndarray) ou None
        """
        try:
            frame = self.frame_buffer.get(timeout=timeout)
            return frame
        except queue.Empty:
            logger.warning("Aucun frame disponible")
            return None
    
    def detect_and_encode_face(self, frame: np.ndarray) -> FaceDetectionResult:
        """
        Détecte et encode les visages dans un frame
        
        Args:
            frame: Frame OpenCV (BGR)
            
        Returns:
            FaceDetectionResult avec encodage et métadonnées
        """
        try:
            if frame is None or frame.size == 0:
                return FaceDetectionResult(
                    success=False,
                    error_message="Frame invalide"
                )
            
            # Convertir BGR → RGB pour MUSE
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Encodage via MUSE
            face_encodings, face_locations, landmarks = encode_face(rgb_frame)
            
            if not face_encodings:
                return FaceDetectionResult(
                    success=False,
                    error_message="Aucun visage détecté"
                )
            
            # Utiliser le premier visage détecté
            encoding = face_encodings[0]
            location = face_locations[0] if face_locations else None
            landmark = landmarks[0] if landmarks else None
            
            # Calculer score de qualité basé sur landmarks
            quality = self._estimate_face_quality(landmark) if landmark is not None else 0.5
            
            self.last_detection_time = datetime.now()
            
            return FaceDetectionResult(
                success=True,
                face_encoding=encoding,
                face_location=location,
                landmarks=landmark,
                quality_score=quality,
                timestamp=self.last_detection_time
            )
            
        except Exception as e:
            logger.error(f"Erreur détection faciale: {e}")
            return FaceDetectionResult(
                success=False,
                error_message=str(e)
            )
    
    def _estimate_face_quality(self, landmarks: np.ndarray) -> float:
        """
        Estime la qualité du visage basée sur les landmarks
        
        Args:
            landmarks: Array 68 landmarks points
            
        Returns:
            Score qualité 0-1
        """
        try:
            if landmarks is None or len(landmarks) < 68:
                return 0.3
            
            # Calculer écart vertical (yeux-menton)
            eye_y_mean = np.mean([landmarks[i][1] for i in [36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47]])
            chin_y = landmarks[8][1]
            vertical_span = chin_y - eye_y_mean
            
            # Calculer écart horizontal (coins bouche)
            mouth_x_left = landmarks[48][0]
            mouth_x_right = landmarks[54][0]
            horizontal_span = mouth_x_right - mouth_x_left
            
            # Ratio d'aspect (idéalement entre 1.5-2.5)
            aspect_ratio = vertical_span / (horizontal_span + 1e-6)
            
            # Score basé sur ratio (plus proche de 2.0 = mieux)
            quality = 1.0 - abs(aspect_ratio - 2.0) / 2.0
            quality = max(0.0, min(1.0, quality))
            
            return round(quality, 3)
            
        except Exception as e:
            logger.warning(f"Erreur calcul qualité: {e}")
            return 0.5
    
    def encode_to_base64(self, frame: np.ndarray) -> str:
        """
        Encode un frame en base64 pour transmission API
        
        Args:
            frame: Frame OpenCV
            
        Returns:
            String base64
        """
        try:
            _, buffer = cv2.imencode('.jpg', frame)
            image_bytes = buffer.tobytes()
            base64_str = base64.b64encode(image_bytes).decode('utf-8')
            return base64_str
        except Exception as e:
            logger.error(f"Erreur encodage base64: {e}")
            return None
    
    def encode_numpy_to_bytes(self, encoding: np.ndarray) -> bytes:
        """
        Sérialise un encodage numpy en bytes
        
        Args:
            encoding: Array numpy 128D
            
        Returns:
            Bytes sérialisés
        """
        try:
            return encoding.tobytes()
        except Exception as e:
            logger.error(f"Erreur sérialisation encodage: {e}")
            return None


class BiometricCacheManager:
    """
    Gère le cache local des données biométriques
    Permet la persistance et la réutilisation des encodages
    """
    
    def __init__(self, cache_dir: str = "./cache/biometric"):
        """
        Initialise le manager de cache
        
        Args:
            cache_dir: Répertoire de cache
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_index = {}
        
        self._load_index()
        logger.info(f"Cache manager initialized at {cache_dir}")
    
    def _load_index(self):
        """Charge l'index du cache"""
        try:
            index_file = self.cache_dir / "index.txt"
            if index_file.exists():
                with open(index_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split(',')
                        if len(parts) >= 2:
                            self.cache_index[parts[0]] = parts[1]
        except Exception as e:
            logger.warning(f"Erreur chargement index cache: {e}")
    
    def save_encoding(self, user_id: str, face_encoding: np.ndarray, label: str = None) -> str:
        """
        Sauvegarde un encodage facial en cache
        
        Args:
            user_id: ID utilisateur
            face_encoding: Array encodage
            label: Label optionnel
            
        Returns:
            Path fichier cache
        """
        try:
            filename = f"{user_id}_{label or 'default'}.npy"
            filepath = self.cache_dir / filename
            
            np.save(filepath, face_encoding)
            self.cache_index[user_id] = filename
            
            # Mettre à jour index
            self._save_index()
            
            logger.info(f"Encodage sauvegardé: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde encodage: {e}")
            return None
    
    def load_encoding(self, user_id: str) -> Optional[np.ndarray]:
        """
        Charge un encodage depuis cache
        
        Args:
            user_id: ID utilisateur
            
        Returns:
            Array encodage ou None
        """
        try:
            if user_id not in self.cache_index:
                return None
            
            filepath = self.cache_dir / self.cache_index[user_id]
            if not filepath.exists():
                return None
            
            return np.load(filepath)
            
        except Exception as e:
            logger.error(f"Erreur chargement encodage: {e}")
            return None
    
    def _save_index(self):
        """Sauvegarde l'index du cache"""
        try:
            index_file = self.cache_dir / "index.txt"
            with open(index_file, 'w') as f:
                for user_id, filename in self.cache_index.items():
                    f.write(f"{user_id},{filename}\n")
        except Exception as e:
            logger.warning(f"Erreur sauvegarde index: {e}")


# Singleton instance
_capture_service: Optional[LocalFaceCaptureService] = None
_cache_manager: Optional[BiometricCacheManager] = None


def get_capture_service(camera_index: int = 0) -> LocalFaceCaptureService:
    """Retourne l'instance unique du service de capture"""
    global _capture_service
    if _capture_service is None:
        _capture_service = LocalFaceCaptureService(camera_index=camera_index)
    return _capture_service


def get_cache_manager() -> BiometricCacheManager:
    """Retourne l'instance unique du manager de cache"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = BiometricCacheManager()
    return _cache_manager
