"""
Fonctions de sécurité : hash, JWT, validation, etc.
"""

import bcrypt
import jwt
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Gestionnaire de sécurité unifié"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash un mot de passe avec bcrypt (sel automatique)"""
        salt = bcrypt.gensalt(rounds=current_app.config['BCRYPT_ROUNDS'])
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        """Vérifie un mot de passe contre son hash"""
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                hashed.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Erreur vérification mot de passe: {e}")
            return False
    
    @staticmethod
    def generate_jwt_token(user_id: str, role: str, expires_delta: timedelta = None) -> str:
        """Génère un token JWT"""
        if expires_delta is None:
            expires_delta = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + expires_delta,
            'iat': datetime.utcnow(),
            'jti': secrets.token_urlsafe(16)  # Identifiant unique du token
        }
        
        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        
        return token
    
    @staticmethod
    def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """Décode et vérifie un token JWT"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token JWT expiré")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token JWT invalide: {e}")
            return None
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Génère un token CSRF"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_csrf_token(token: str, stored_token: str) -> bool:
        """Vérifie un token CSRF (constant-time)"""
        return hmac.compare_digest(token, stored_token)
    
    @staticmethod
    def hash_log_entry(data: str) -> str:
        """Hash une entrée de log pour garantir l'immutabilité"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def generate_api_key() -> str:
        """Génère une clé API unique"""
        return f"ba_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """Nettoie les entrées utilisateur (XSS prevention)"""
        # Remplacer les caractères dangereux
        replacements = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text