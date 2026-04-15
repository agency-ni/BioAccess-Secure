"""
Orchestration de l'authentification vocale
Enregistrement → encodage → envoi backend → vérification seuil
"""

import logging
from hardware.microphone import MicrophoneService
from api_client import BioAccessAPIClient, AuthResult
from config import LOG_LEVEL

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

class VoiceAuthenticationFlow:
    """
    Pipeline d'authentification vocale complète
    """
    
    def __init__(self, api_client: BioAccessAPIClient):
        """
        Initialise le flow d'auth vocale
        
        Args:
            api_client: Instance BioAccessAPIClient
        """
        self.api_client = api_client
        self.microphone = MicrophoneService()
        
        logger.info("VoiceAuthenticationFlow initialisé")
    
    def authenticate(self, user_id: str) -> AuthResult:
        """
        Exécute le pipeline complet d'authentification vocale
        
        Args:
            user_id: ID utilisateur BioAccess
            
        Returns:
            AuthResult avec succès/échec et détails
        """
        logger.info(f"Démarrage auth vocale pour {user_id}")
        
        try:
            # Enregistrer voix
            logger.info("Enregistrement en cours...")
            audio_base64 = self.microphone.capture_voice()
            
            if not audio_base64:
                return AuthResult(
                    success=False,
                    confidence=0.0,
                    error="Échec enregistrement",
                    message="Impossible d'enregistrer la voix"
                )
            
            # Mesurer niveau audio
            audio_level = self.microphone.get_audio_level()
            logger.debug(f"Niveau audio: {audio_level}dB")
            
            if audio_level < -20:
                logger.warning("Niveau audio très faible - qualité compromised")
            
            # Nettoyer ressources
            self.microphone.cleanup()
            
            # Envoyer au backend
            logger.info("Envoi au backend...")
            result = self.api_client.auth_voice(user_id, audio_base64, source='DOOR')
            
            logger.info(f"Résultat auth vocale: {result.success} (confiance: {result.confidence})")
            return result
        
        except Exception as e:
            logger.error(f"Erreur pipeline auth vocale: {e}")
            self.microphone.cleanup()
            return AuthResult(
                success=False,
                confidence=0.0,
                error=str(e),
                message=f"Erreur interne: {str(e)[:50]}"
            )
