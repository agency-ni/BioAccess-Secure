"""
Client API pour communiquer avec le serveur BioAccess Secure
"""

import requests
import json
import logging
import time
from typing import Dict, Optional, Tuple, Callable
from config import API_BASE_URL, API_TIMEOUT, API_KEY

# Configuration du logger
logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, backoff_factor: float = 1.0):
    """
    Décorateur pour réessayer en cas d'erreur réseau
    
    Args:
        max_retries: Nombre maximum de tentatives
        backoff_factor: Facteur d'attente entre les tentatives
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.Timeout, requests.ConnectionError) as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor * (2 ** attempt)
                        logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée. "
                                     f"Nouvelle tentative dans {wait_time}s...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Tous les retries ont échoué après {max_retries} tentatives")
            
            if last_error:
                raise last_error
        return wrapper
    return decorator


class APIClient:
    """Client HTTP pour les requêtes API"""

    def __init__(self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'BioAccessSecureDesktopClient/1.0',
            'X-API-Key': API_KEY
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None,
                      files: Optional[Dict] = None) -> Tuple[bool, Dict]:
        """
        Effectue une requête HTTP générique
        
        Args:
            method: 'GET', 'POST', 'PUT', 'DELETE'
            endpoint: Endpoint relatif (ex: '/auth/face')
            data: Données JSON
            files: Données multipart
            
        Returns:
            Tuple (success, response_data)
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"[API] {method} {endpoint}")
            
            if method == 'GET':
                response = self.session.get(url, timeout=self.timeout)
            elif method == 'POST':
                if files:
                    # Pour multipart, ne pas utiliser les headers par défaut
                    headers = {'User-Agent': 'BioAccessSecureDesktopClient/1.0',
                              'X-API-Key': API_KEY}
                    response = requests.post(url, files=files, headers=headers, 
                                           timeout=self.timeout)
                else:
                    response = self.session.post(url, json=data, timeout=self.timeout)
            elif method == 'PUT':
                response = self.session.put(url, json=data, timeout=self.timeout)
            elif method == 'DELETE':
                response = self.session.delete(url, timeout=self.timeout)
            else:
                return False, {'error': 'Méthode HTTP non supportée'}
            
            # Vérifier le statut
            if response.status_code >= 400:
                logger.error(f"[API ERROR] {response.status_code}: {response.text}")
                try:
                    error_data = response.json()
                    return False, error_data
                except:
                    return False, {'error': f'Erreur serveur {response.status_code}'}
            
            # Retourner la réponse JSON
            try:
                return True, response.json()
            except:
                return True, {}
        
        except requests.Timeout:
            logger.error(f"[API TIMEOUT] {endpoint} (timeout: {self.timeout}s)")
            return False, {'error': f'Timeout ({self.timeout}s) - Serveur pas accessible'}
        
        except requests.ConnectionError:
            logger.error(f"[API CONNECTION ERROR] Impossible de se connecter à {self.base_url}")
            return False, {'error': 'Erreur de connexion - Serveur pas accessible'}
        
        except Exception as e:
            logger.error(f"[API EXCEPTION] {str(e)}")
            return False, {'error': str(e)}

    # ============ AUTHENTIFICATION ============

    @retry_on_failure(max_retries=3, backoff_factor=1.0)
    def authenticate_face(self, face_data: str, user_id: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Envoyer une image faciale encodée en base64
        
        Args:
            face_data: Image en base64
            user_id: ID utilisateur (optionnel)
            
        Returns:
            Tuple (success, response)
                - success: True si authentification réussie
                - response: {status, user, confidence, message}
        """
        data = {
            'face_image': face_data,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
        if user_id:
            data['user_id'] = user_id
        
        success, response = self._make_request('POST', '/auth/face', data=data)
        
        # Valider la réponse si succès
        if success and response:
            required_fields = ['status', 'user', 'confidence']
            missing_fields = [f for f in required_fields if f not in response]
            if missing_fields:
                logger.warning(f"[VALIDATION WARNING] Champs manquants en réponse: {missing_fields}")
                response['_validation_warning'] = f"Champs manquants: {', '.join(missing_fields)}"
        
        return success, response

    @retry_on_failure(max_retries=3, backoff_factor=1.0)
    def authenticate_voice(self, voice_data: str, user_id: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Envoyer un audio vocale encodé en base64
        
        Args:
            voice_data: Audio en base64
            user_id: ID utilisateur (optionnel)
            
        Returns:
            Tuple (success, response)
                - success: True si authentification réussie
                - response: {status, user, confidence, message}
        """
        data = {
            'voice_audio': voice_data,
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
        if user_id:
            data['user_id'] = user_id
        
        success, response = self._make_request('POST', '/auth/voice', data=data)
        
        # Valider la réponse si succès
        if success and response:
            required_fields = ['status', 'user', 'confidence']
            missing_fields = [f for f in required_fields if f not in response]
            if missing_fields:
                logger.warning(f"[VALIDATION WARNING] Champs manquants en réponse: {missing_fields}")
                response['_validation_warning'] = f"Champs manquants: {', '.join(missing_fields)}"
        
        return success, response

    def authenticate_biometric(self, face_data: Optional[str] = None,
                              voice_data: Optional[str] = None) -> Tuple[bool, Dict]:
        """
        Authentification combinée (face + voix)
        
        Args:
            face_data: Image faciale en base64 (optionnel)
            voice_data: Audio vocale en base64 (optionnel)
            
        Returns:
            Tuple (success, response)
        """
        data = {
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
        if face_data:
            data['face_image'] = face_data
        if voice_data:
            data['voice_audio'] = voice_data
        
        success, response = self._make_request('POST', '/auth/biometric', data=data)
        return success, response

    # ============ UTILISATEURS ============

    def get_user_info(self, user_id: str) -> Tuple[bool, Dict]:
        """Récupérer les informations d'un utilisateur"""
        success, response = self._make_request('GET', f'/users/{user_id}')
        return success, response

    def update_user_biometric(self, user_id: str, face_data: Optional[str] = None,
                             voice_data: Optional[str] = None) -> Tuple[bool, Dict]:
        """Mettre à jour les données biométriques d'un utilisateur"""
        data = {}
        if face_data:
            data['face_template'] = face_data
        if voice_data:
            data['voice_template'] = voice_data
        
        success, response = self._make_request('PUT', f'/users/{user_id}/biometric', data=data)
        return success, response

    # ============ SANTÉ DE L'API ============

    @retry_on_failure(max_retries=3, backoff_factor=0.5)
    def health_check(self) -> Tuple[bool, Dict]:
        """Vérifier si l'API est accessible avec retry automatique"""
        try:
            response = requests.get(f"{self.base_url}/health", 
                                  timeout=self.timeout)
            is_healthy = response.status_code == 200
            data = response.json() if is_healthy else {'status': 'error'}
            logger.debug(f"[HEALTH CHECK] {'✓ UP' if is_healthy else '✗ DOWN'}")
            return is_healthy, data
        except Exception as e:
            logger.warning(f"[HEALTH CHECK] Erreur: {str(e)}")
            return False, {'status': 'down', 'error': str(e)}

    # ============ AUTHENTIFICATION TOKEN ============

    def login_password(self, email: str, password: str) -> Tuple[bool, Dict]:
        """
        Authentification avec email/password
        
        Returns:
            Tuple (success, {user, token, ...})
        """
        data = {
            'email': email,
            'password': password,
            'remember': True
        }
        success, response = self._make_request('POST', '/auth/login', data=data)
        return success, response

    def set_token(self, token: str):
        """Définir le token JWT pour les requêtes futures"""
        self.headers['Authorization'] = f'Bearer {token}'
        self.session.headers.update(self.headers)

    def logout(self) -> Tuple[bool, Dict]:
        """Déconnexion"""
        success, response = self._make_request('POST', '/auth/logout', data={})
        return success, response


# Instance globale
api_client = APIClient()
