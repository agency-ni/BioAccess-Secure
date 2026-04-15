"""
Client API pour communiquer avec le backend BioAccess-Secure
Gère authentification biométrique faciale et vocale avec retry et timeout
"""

import requests
import logging
import time
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from config import (
    BACKEND_URL, ADMIN_TOKEN, REQUEST_TIMEOUT, RETRY_COUNT,
    RETRY_DELAY, CONFIDENCE_THRESHOLD, LOG_LEVEL
)

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

@dataclass
class AuthResult:
    """Résultat d'une tentative d'authentification"""
    success: bool
    confidence: float = 0.0
    message: str = ""
    error: str = None
    user_id: str = None
    token: str = None

class BioAccessAPIClient:
    """
    Client pour communiquer avec l'API BioAccess-Secure
    Gère face/verify et voice/verify avec gestion erreurs réseau
    """
    
    def __init__(self, backend_url=BACKEND_URL, admin_token=ADMIN_TOKEN,
                 timeout=REQUEST_TIMEOUT, retry_count=RETRY_COUNT):
        """
        Initialise le client API
        
        Args:
            backend_url: URL du backend (http://IP:PORT)
            admin_token: Token d'authentification admin
            timeout: Timeout requêtes en secondes
            retry_count: Nombre de tentatives en cas d'erreur réseau
        """
        self.backend_url = backend_url.rstrip('/')
        self.admin_token = admin_token
        self.timeout = timeout
        self.retry_count = retry_count
        self.api_version = 'v1'
        
        # Construire base URL
        if not self.backend_url.endswith('/api'):
            self.base_url = f"{self.backend_url}/api/{self.api_version}"
        else:
            self.base_url = f"{self.backend_url}/{self.api_version}"
        
        self.session = requests.Session()
        self._setup_session()
        
        logger.info(f"BioAccessAPIClient initialisé - Backend: {self.base_url}")
    
    def _setup_session(self):
        """
        Configure la session requests avec headers par défaut
        """
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BioLock-Door-System/1.0',
            'X-Admin-Token': self.admin_token
        })
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None,
                     authenticated: bool = False) -> Tuple[Optional[Dict], int, Optional[str]]:
        """
        Effectue une requête HTTP avec retry automatique en cas de timeout
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: Chemin endpoint (/auth/face)
            data: Données JSON à envoyer
            authenticated: (non utilisé - pour compatibilité future)
            
        Returns:
            (data, status_code, error_message)
        """
        url = f"{self.base_url}{endpoint}"
        attempt = 0
        last_error = None
        
        while attempt < self.retry_count:
            try:
                attempt += 1
                
                logger.debug(f"{method} {url} (tentative {attempt}/{self.retry_count})")
                
                response = self.session.request(
                    method=method.upper(),
                    url=url,
                    json=data,
                    timeout=self.timeout
                )
                
                if response.status_code in [200, 201]:
                    try:
                        return response.json(), response.status_code, None
                    except ValueError:
                        return {}, response.status_code, "Réponse JSON invalide"
                elif response.status_code == 401:
                    return None, 401, "Authentification échouée"
                elif response.status_code == 400:
                    try:
                        error_msg = response.json().get('error', 'Erreur requête')
                    except:
                        error_msg = "Erreur requête (400)"
                    return None, 400, error_msg
                elif response.status_code >= 500:
                    last_error = f"Erreur serveur {response.status_code}"
                else:
                    return None, response.status_code, f"HTTP {response.status_code}"
            
            except requests.Timeout:
                last_error = f"Timeout ({self.timeout}s)"
                logger.warning(f"Timeout - tentative {attempt}/{self.retry_count}")
                
                if attempt < self.retry_count:
                    time.sleep(RETRY_DELAY)
            
            except requests.ConnectionError as e:
                last_error = f"Erreur connexion: {str(e)[:50]}"
                logger.warning(f"Erreur connexion - tentative {attempt}/{self.retry_count}")
                
                if attempt < self.retry_count:
                    time.sleep(RETRY_DELAY)
            
            except Exception as e:
                last_error = f"Erreur: {str(e)[:50]}"
                logger.error(f"Erreur requête: {e}")
                break
        
        return None, 0, last_error
    
    def auth_face(self, user_id: str, image_base64: str,
                 source: str = 'DOOR') -> AuthResult:
        """
        Authentifier un utilisateur par visage
        
        Args:
            user_id: ID utilisateur BioAccess
            image_base64: Image encodée en base64
            source: Source d'authentification (DOOR ou DESKTOP)
            
        Returns:
            AuthResult avec success, confidence, message, error
        """
        logger.info(f"Authentification faciale pour user {user_id[:8]}...")
        
        try:
            data = {
                'user_id': user_id,
                'image_data': image_base64,
                'source': source
            }
            
            response_data, status_code, error = self._make_request(
                'POST', '/auth/face/verify', data=data
            )
            
            if error:
                logger.error(f"Erreur auth faciale: {error}")
                return AuthResult(
                    success=False,
                    confidence=0.0,
                    error=error,
                    message=f"Erreur réseau: {error}"
                )
            
            if not response_data:
                return AuthResult(
                    success=False,
                    confidence=0.0,
                    error="Réponse vide",
                    message="Réponse du serveur invalide"
                )
            
            # Parser réponse
            success = response_data.get('success', False)
            similarity = response_data.get('similarity', 0.0)
            
            if success and similarity >= CONFIDENCE_THRESHOLD:
                logger.info(f"Auth facial réussie (confiance: {similarity})")
                return AuthResult(
                    success=True,
                    confidence=similarity,
                    message=f"Authentification réussie ({similarity:.2%})",
                    user_id=user_id,
                    token=response_data.get('token')
                )
            else:
                reason = "Visage non reconnu" if not success else f"Confiance insuffisante ({similarity:.2%})"
                logger.warning(f"Auth facial échouée: {reason}")
                return AuthResult(
                    success=False,
                    confidence=similarity,
                    error=reason,
                    message=reason
                )
        
        except Exception as e:
            logger.error(f"Erreur authentification faciale: {e}")
            return AuthResult(
                success=False,
                confidence=0.0,
                error=str(e),
                message=f"Erreur: {str(e)[:50]}"
            )
    
    def auth_voice(self, user_id: str, audio_base64: str,
                  source: str = 'DOOR') -> AuthResult:
        """
        Authentifier un utilisateur par voix
        
        Args:
            user_id: ID utilisateur BioAccess
            audio_base64: Audio WAV encodé en base64
            source: Source d'authentification (DOOR ou DESKTOP)
            
        Returns:
            AuthResult avec success, confidence, message, error
        """
        logger.info(f"Authentification vocale pour user {user_id[:8]}...")
        
        try:
            data = {
                'user_id': user_id,
                'audio_data': audio_base64,
                'source': source
            }
            
            response_data, status_code, error = self._make_request(
                'POST', '/auth/voice/verify', data=data
            )
            
            if error:
                logger.error(f"Erreur auth vocale: {error}")
                return AuthResult(
                    success=False,
                    confidence=0.0,
                    error=error,
                    message=f"Erreur réseau: {error}"
                )
            
            if not response_data:
                return AuthResult(
                    success=False,
                    confidence=0.0,
                    error="Réponse vide",
                    message="Réponse du serveur invalide"
                )
            
            # Parser réponse
            success = response_data.get('success', False)
            similarity = response_data.get('similarity', 0.0)
            
            if success and similarity >= CONFIDENCE_THRESHOLD:
                logger.info(f"Auth vocale réussie (confiance: {similarity})")
                return AuthResult(
                    success=True,
                    confidence=similarity,
                    message=f"Authentification réussie ({similarity:.2%})",
                    user_id=user_id,
                    token=response_data.get('token')
                )
            else:
                reason = "Voix non reconnue" if not success else f"Confiance insuffisante ({similarity:.2%})"
                logger.warning(f"Auth vocale échouée: {reason}")
                return AuthResult(
                    success=False,
                    confidence=similarity,
                    error=reason,
                    message=reason
                )
        
        except Exception as e:
            logger.error(f"Erreur authentification vocale: {e}")
            return AuthResult(
                success=False,
                confidence=0.0,
                error=str(e),
                message=f"Erreur: {str(e)[:50]}"
            )
    
    def test_connection(self) -> bool:
        """
        Teste la connexion au backend
        
        Returns:
            bool: True si backend accessible
        """
        try:
            response = self.session.get(
                f"{self.backend_url}/health",
                timeout=self.timeout
            )
            is_ok = response.status_code in [200, 404]
            
            if is_ok:
                logger.info("Connexion backend OK")
            else:
                logger.warning(f"Backend retourne {response.status_code}")
            
            return is_ok
        except Exception as e:
            logger.error(f"Backend inaccessible: {e}")
            return False
