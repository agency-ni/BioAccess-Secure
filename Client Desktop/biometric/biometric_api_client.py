"""
Service d'intégration avec l'API BioAccess-Secure backend
Gère la communication avec les endpoints d'authentification faciale et vocale
"""

import requests
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Réponse structurée de l'API"""
    success: bool
    status_code: int
    data: Dict = None
    error_message: str = None
    timestamp: datetime = None


class BioAccessAPIClient:
    """
    Client pour communiquer avec l'API BioAccess-Secure
    Gère authentification, tokens, et endpoints biométriques
    """
    
    def __init__(self, 
                 api_base: str = None,
                 timeout: int = 10,
                 verify_ssl: bool = True):
        """
        Initialise le client API
        
        Args:
            api_base: URL de base API (ex: http://localhost:5000/api/v1)
            timeout: Timeout requêtes en secondes
            verify_ssl: Vérifier certificats SSL
        """
        self.api_base = api_base or self._load_config()
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.session = requests.Session()
        
        # Authentification
        self.auth_token = None
        self.token_expires_at = None
        
        # Headers sécurité
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'BioAccess-Client/2.0'
        })
        
        logger.info(f"BioAccessAPIClient initialized with base URL: {self.api_base}")
    
    def _load_config(self) -> str:
        """Charge la configuration depuis fichier .env ou config"""
        try:
            # Chercher .env
            env_file = Path('.env')
            if env_file.exists():
                with open(env_file) as f:
                    for line in f:
                        if line.startswith('API_BASE_URL='):
                            return line.split('=')[1].strip()
            
            # Chercher variable environnement
            api_url = os.getenv('API_BASE_URL')
            if api_url:
                return api_url
            
            # Défaut localhost
            logger.warning("Configuration API non trouvée, utilisant localhost")
            return "http://localhost:5000/api/v1"
            
        except Exception as e:
            logger.error(f"Erreur chargement config: {e}")
            return "http://localhost:5000/api/v1"
    
    def set_auth_token(self, token: str, expires_in: int = 86400):
        """
        Définit le token d'authentification
        
        Args:
            token: JWT token
            expires_in: Durée validité en secondes (défaut 24h)
        """
        self.auth_token = token
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
        
        # Ajouter aux headers
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })
        
        logger.info("Auth token défini")
    
    def is_token_valid(self) -> bool:
        """Vérifie si le token est toujours valide"""
        if not self.auth_token or not self.token_expires_at:
            return False
        
        return datetime.now() < self.token_expires_at
    
    def _make_request(self,
                      method: str,
                      endpoint: str,
                      data: Dict = None,
                      params: Dict = None,
                      authenticated: bool = False) -> APIResponse:
        """
        Effectue une requête HTTP
        
        Args:
            method: GET, POST, PUT, DELETE
            endpoint: Chemin endpoint (/auth/face/register)
            data: Données JSON
            params: Query parameters
            authenticated: Requiert authentification
            
        Returns:
            APIResponse
        """
        try:
            url = urljoin(self.api_base, endpoint.lstrip('/'))
            
            if authenticated and not self.is_token_valid():
                logger.error("Token d'authentification expiré ou invalide")
                return APIResponse(
                    success=False,
                    status_code=401,
                    error_message="Token d'authentification expiré"
                )
            
            logger.debug(f"{method} {url}")
            
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout,
                verify=self.verify_ssl
            )
            
            # Parser réponse
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            success = response.status_code in [200, 201]
            
            return APIResponse(
                success=success,
                status_code=response.status_code,
                data=response_data if success else None,
                error_message=response_data.get('error') if isinstance(response_data, dict) else str(response_data),
                timestamp=datetime.now()
            )
            
        except requests.exceptions.Timeout:
            logger.error("Timeout requête API")
            return APIResponse(
                success=False,
                status_code=0,
                error_message="Timeout requête API"
            )
        except requests.exceptions.ConnectionError:
            logger.error("Erreur connexion API")
            return APIResponse(
                success=False,
                status_code=0,
                error_message="Erreur connexion API"
            )
        except Exception as e:
            logger.error(f"Erreur requête API: {e}")
            return APIResponse(
                success=False,
                status_code=0,
                error_message=str(e)
            )
    
    # ====== ENDPOINTS AUTHENTIFICATION ======
    
    def face_register(self, 
                      image_base64: str,
                      label: str = None) -> APIResponse:
        """
        Enregistre un nouveau visage
        
        POST /auth/face/register
        
        Args:
            image_base64: Image en base64
            label: Label optionnel
            
        Returns:
            APIResponse avec template_id et encoding
        """
        data = {
            'image_data': image_base64,
            'label': label or 'Face enregistrée'
        }
        
        return self._make_request(
            method='POST',
            endpoint='/auth/face/register',
            data=data,
            authenticated=True
        )
    
    def face_verify(self, email: str, image_base64: str) -> APIResponse:
        """
        Authentifie via reconnaissance faciale
        
        POST /auth/face/verify
        
        Args:
            email: Email utilisateur
            image_base64: Image en base64
            
        Returns:
            APIResponse avec token si succès
        """
        data = {
            'email': email,
            'image_data': image_base64
        }
        
        return self._make_request(
            method='POST',
            endpoint='/auth/face/verify',
            data=data,
            authenticated=False
        )
    
    def voice_register(self,
                       audio_base64: str,
                       label: str = None) -> APIResponse:
        """
        Enregistre un modèle vocal
        
        POST /auth/voice/register
        
        Args:
            audio_base64: Audio en base64
            label: Label optionnel
            
        Returns:
            APIResponse avec template_id
        """
        data = {
            'audio_data': audio_base64,
            'label': label or 'Voix enregistrée'
        }
        
        return self._make_request(
            method='POST',
            endpoint='/auth/voice/register',
            data=data,
            authenticated=True
        )
    
    def voice_verify(self, email: str, audio_base64: str) -> APIResponse:
        """
        Authentifie via reconnaissance vocale
        
        POST /auth/voice/verify
        
        Args:
            email: Email utilisateur
            audio_base64: Audio en base64
            
        Returns:
            APIResponse avec token si succès
        """
        data = {
            'email': email,
            'audio_data': audio_base64
        }
        
        return self._make_request(
            method='POST',
            endpoint='/auth/voice/verify',
            data=data,
            authenticated=False
        )
    
    def liveness_detect(self, 
                        image_base64: str,
                        challenge_response: str = None) -> APIResponse:
        """
        Détecte vivacité (liveness detection)
        
        POST /auth/liveness/detect
        
        Args:
            image_base64: Image en base64
            challenge_response: Challenge response (optionnel)
            
        Returns:
            APIResponse avec is_live et confidence
        """
        data = {
            'image_data': image_base64,
            'challenge_response': challenge_response
        }
        
        return self._make_request(
            method='POST',
            endpoint='/auth/liveness/detect',
            data=data,
            authenticated=False
        )
    
    # ====== ENDPOINTS UTILISATEUR ======
    
    def get_user_profile(self) -> APIResponse:
        """
        Récupère le profil utilisateur connecté
        
        GET /users/profile
        
        Returns:
            APIResponse avec user data
        """
        return self._make_request(
            method='GET',
            endpoint='/users/profile',
            authenticated=True
        )
    
    def update_user_profile(self, data: Dict) -> APIResponse:
        """
        Met à jour le profil utilisateur
        
        PUT /users/profile
        
        Args:
            data: Données profil à mettre à jour
            
        Returns:
            APIResponse
        """
        return self._make_request(
            method='PUT',
            endpoint='/users/profile',
            data=data,
            authenticated=True
        )
    
    # ====== ENDPOINTS LOGS ======
    
    def get_auth_logs(self, limit: int = 50) -> APIResponse:
        """
        Récupère les logs d'authentification
        
        GET /logs/auth
        
        Args:
            limit: Nombre de logs
            
        Returns:
            APIResponse avec logs
        """
        return self._make_request(
            method='GET',
            endpoint='/logs/auth',
            params={'limit': limit},
            authenticated=True
        )
    
    def health_check(self) -> bool:
        """
        Vérifie la disponibilité de l'API
        
        Returns:
            bool: True si API accessible
        """
        response = self._make_request(
            method='GET',
            endpoint='/health',
            authenticated=False
        )
        return response.success and response.status_code == 200


# Singleton instance
_api_client: Optional[BioAccessAPIClient] = None


def get_api_client(api_base: str = None) -> BioAccessAPIClient:
    """Retourne l'instance unique du client API"""
    global _api_client
    if _api_client is None:
        _api_client = BioAccessAPIClient(api_base=api_base)
    return _api_client


# Convenience namespace pour utilisation simple
class BiometricAPI:
    """Namespace pour accès simplifié aux fonctions API"""
    
    @staticmethod
    def set_base_url(url: str):
        """Configure l'URL de base"""
        global _api_client
        _api_client = BioAccessAPIClient(api_base=url)
    
    @staticmethod
    def set_token(token: str):
        """Configure le token d'authentification"""
        get_api_client().set_auth_token(token)
    
    @staticmethod
    def face_register(image_base64: str, label: str = None) -> APIResponse:
        """Enregistre un visage"""
        return get_api_client().face_register(image_base64, label)
    
    @staticmethod
    def face_verify(email: str, image_base64: str) -> APIResponse:
        """Authentifie via visage"""
        return get_api_client().face_verify(email, image_base64)
    
    @staticmethod
    def voice_register(audio_base64: str, label: str = None) -> APIResponse:
        """Enregistre la voix"""
        return get_api_client().voice_register(audio_base64, label)
    
    @staticmethod
    def voice_verify(email: str, audio_base64: str) -> APIResponse:
        """Authentifie via voix"""
        return get_api_client().voice_verify(email, audio_base64)
    
    @staticmethod
    def liveness_check(image_base64: str) -> APIResponse:
        """Vérifie la vivacité"""
        return get_api_client().liveness_detect(image_base64)
    
    @staticmethod
    def is_healthy() -> bool:
        """Vérifie si l'API est accessible"""
        return get_api_client().health_check()
