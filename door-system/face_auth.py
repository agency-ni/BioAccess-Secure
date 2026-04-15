"""
Orchestration de l'authentification faciale
Capture → encodage → envoi backend → vérification seuil
"""

import logging
from hardware.camera import FaceCaptureService
from api_client import BioAccessAPIClient, AuthResult
from config import LOG_LEVEL

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

class FaceAuthenticationFlow:
    """
    Pipeline d'authentification faciale complète
    """
    
    def __init__(self, api_client: BioAccessAPIClient):
        """
        Initialise le flow d'auth faciale
        
        Args:
            api_client: Instance BioAccessAPIClient
        """
        self.api_client = api_client
        self.face_capture = FaceCaptureService()
        
        logger.info("FaceAuthenticationFlow initialisé")
    
    def authenticate(self, user_id: str) -> AuthResult:
        """
        Exécute le pipeline complet d'authentification faciale
        
        Args:
            user_id: ID utilisateur BioAccess
            
        Returns:
            AuthResult avec succès/échec et détails
        """
        logger.info(f"Démarrage auth faciale pour {user_id}")
        
        try:
            # Démarrer caméra
            if not self.face_capture.start_camera():
                return AuthResult(
                    success=False,
                    confidence=0.0,
                    error="Caméra non disponible",
                    message="Impossible d'initialiser la caméra"
                )
            
            # Capturer visage
            logger.info("Capture en cours...")
            image_base64, frame = self.face_capture.capture_face()
            
            self.face_capture.stop_camera()
            
            if not image_base64:
                return AuthResult(
                    success=False,
                    confidence=0.0,
                    error="Échec capture",
                    message="Impossible de capturer le visage"
                )
            
            # Envoyer au backend
            logger.info("Envoi au backend...")
            result = self.api_client.auth_face(user_id, image_base64, source='DOOR')
            
            logger.info(f"Résultat auth faciale: {result.success} (confiance: {result.confidence})")
            return result
        
        except Exception as e:
            logger.error(f"Erreur pipeline auth faciale: {e}")
            return AuthResult(
                success=False,
                confidence=0.0,
                error=str(e),
                message=f"Erreur interne: {str(e)[:50]}"
            )
    
    def cleanup(self):
        """
        Nettoie les ressources caméra
        """
        try:
            self.face_capture.stop_camera()
        except:
            pass
