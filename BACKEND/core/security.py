"""
Module de sécurité centralisé
Gestion du hash, JWT, chiffrement, anti-CSRF, etc.
"""

import bcrypt
import jwt
import secrets
import hashlib
import hmac
import base64
import zlib
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from flask import current_app, request, g
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import logging

logger = logging.getLogger(__name__)

# Initialisation Argon2 (plus sécurisé que bcrypt)
ph = PasswordHasher(
    time_cost=2,          # Nombre d'itérations
    memory_cost=102400,    # 100 MB
    parallelism=8,         # Parallélisme
    hash_len=32            # Longueur du hash
)

class SecurityManager:
    """Gestionnaire de sécurité unifié - Niveau industriel"""
    
    # ============================================
    # HASH DE MOTS DE PASSE (Argon2)
    # ============================================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash un mot de passe avec Argon2id (recommandé OWASP)
        Argon2id est résistant aux attaques GPU et side-channel
        """
        try:
            return ph.hash(password)
        except Exception as e:
            logger.error(f"Erreur hash password: {e}")
            raise
    
    @staticmethod
    def check_password(password: str, hashed: str) -> bool:
        """
        Vérifie un mot de passe contre son hash Argon2
        """
        try:
            return ph.verify(hashed, password)
        except VerifyMismatchError:
            return False
        except Exception as e:
            logger.error(f"Erreur vérification password: {e}")
            return False
    
    @staticmethod
    def check_password_and_rehash(password: str, hashed: str) -> Tuple[bool, Optional[str]]:
        """
        Vérifie le mot de passe et retourne un nouveau hash si nécessaire
        (pour mettre à jour les paramètres de hash)
        """
        try:
            # Vérification
            is_valid = ph.verify(hashed, password)
            
            # Vérifier si besoin de rehash
            if is_valid and ph.check_needs_rehash(hashed):
                new_hash = ph.hash(password)
                return True, new_hash
            
            return is_valid, None
        except VerifyMismatchError:
            return False, None
        except Exception as e:
            logger.error(f"Erreur vérification password: {e}")
            return False, None
    
    # ============================================
    # JWT (JSON Web Tokens)
    # ============================================
    
    @staticmethod
    def generate_jwt_token(
        user_id: str,
        role: str,
        expires_delta: timedelta = None,
        token_type: str = 'access'
    ) -> str:
        """
        Génère un token JWT avec les claims de sécurité
        """
        if expires_delta is None:
            if token_type == 'access':
                expires_delta = timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
            else:
                expires_delta = timedelta(seconds=current_app.config['JWT_REFRESH_TOKEN_EXPIRES'])
        
        # Claims standards
        now = datetime.utcnow()
        payload = {
            'sub': user_id,                          # Subject
            'role': role,                            # Rôle utilisateur
            'type': token_type,                       # Type de token
            'exp': now + expires_delta,               # Expiration
            'iat': now,                               # Issued at
            'nbf': now,                               # Not before
            'jti': secrets.token_urlsafe(16),         # Unique ID (pour revocation)
            'iss': 'bioaccess-secure',                 # Issuer
            'aud': 'bioaccess-api',                    # Audience
            'ip': request.remote_addr if request else 'unknown',  # IP (pour détection)
            'ua': request.headers.get('User-Agent', 'unknown')[:50]  # User-Agent
        }
        
        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        return token
    
    @staticmethod
    def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Décode et vérifie un token JWT
        Vérifie aussi la signature, l'expiration, l'audience, etc.
        """
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']],
                audience='bioaccess-api',
                issuer='bioaccess-secure',
                options={
                    'verify_exp': True,
                    'verify_aud': True,
                    'verify_iss': True
                }
            )
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token JWT expiré")
            return None
        except jwt.InvalidAudienceError:
            logger.warning("Audience JWT invalide")
            return None
        except jwt.InvalidIssuerError:
            logger.warning("Issuer JWT invalide")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token JWT invalide: {e}")
            return None
    
    @staticmethod
    def revoke_token(token: str) -> bool:
        """
        Révoque un token (à stocker dans Redis)
        """
        payload = SecurityManager.decode_jwt_token(token)
        if payload and 'jti' in payload:
            from core.cache import cache
            jti = payload['jti']
            exp = payload['exp'] - datetime.utcnow().timestamp()
            if exp > 0:
                cache.setex(f"revoked_token:{jti}", int(exp), 'revoked')
                return True
        return False
    
    @staticmethod
    def is_token_revoked(token: str) -> bool:
        """
        Vérifie si un token est révoqué
        """
        from core.cache import cache
        payload = SecurityManager.decode_jwt_token(token)
        if payload and 'jti' in payload:
            return cache.exists(f"revoked_token:{payload['jti']}")
        return True
    
    # ============================================
    # CHIFFREMENT SYMÉTRIQUE (pour données sensibles)
    # ============================================
    
    @staticmethod
    def get_fernet():
        """Récupère une instance Fernet (chiffrement symétrique)"""
        # Dériver une clé à partir du SECRET_KEY
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'bioaccess_salt',
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(
            current_app.config['SECRET_KEY'].encode()
        ))
        return Fernet(key)
    
    @staticmethod
    def encrypt_data(data: str) -> str:
        """Chiffre des données sensibles"""
        f = SecurityManager.get_fernet()
        return f.encrypt(data.encode()).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """Déchiffre des données sensibles"""
        try:
            f = SecurityManager.get_fernet()
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Erreur déchiffrement: {e}")
            return ""
    
    # ============================================
    # CSRF (Cross-Site Request Forgery)
    # ============================================
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Génère un token CSRF unique"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def verify_csrf_token(token: str, stored_token: str) -> bool:
        """Vérifie un token CSRF (temps constant)"""
        return hmac.compare_digest(token, stored_token)
    
    # ============================================
    # HASH POUR IMMUTABILITÉ DES LOGS
    # ============================================
    
    @staticmethod
    def hash_log_entry(data: Dict[str, Any]) -> str:
        """
        Hash une entrée de log pour garantir l'immutabilité
        Utilise SHA-256 avec un salt
        """
        # Trier les clés pour garantir la cohérence
        data_str = str(sorted(data.items()))
        salt = current_app.config['SECRET_KEY']
        return hashlib.sha256(f"{salt}:{data_str}".encode()).hexdigest()
    
    @staticmethod
    def verify_log_chain(logs: list) -> bool:
        """
        Vérifie la chaîne de hash des logs (blockchain-like)
        """
        for i in range(1, len(logs)):
            expected_hash = SecurityManager.hash_log_entry(logs[i-1])
            if logs[i].get('previous_hash') != expected_hash:
                return False
        return True
    
    # ============================================
    # API KEYS
    # ============================================
    
    @staticmethod
    def generate_api_key() -> str:
        """Génère une clé API unique et sécurisée"""
        return f"ba_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash une clé API pour stockage sécurisé"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    # ============================================
    # SANITIZATION (XSS Prevention)
    # ============================================
    
    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Nettoie les entrées utilisateur pour prévenir XSS
        Utilise un allowlist de caractères
        """
        if not text:
            return ""
        
        # Remplacer les caractères dangereux
        replacements = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '/': '&#x2F;',
            '\\': '&#x5C;',
            '`': '&#x60;',
            '=': '&#x3D;'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        return text
    
    @staticmethod
    def sanitize_html(html: str) -> str:
        """
        Nettoie du HTML (plus agressif)
        """
        import bleach
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3']
        allowed_attrs = {}
        return bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
    
    # ============================================
    # DÉTECTION DES INJECTIONS
    # ============================================
    
    @staticmethod
    def detect_sql_injection(text: str) -> bool:
        """
        Détecte les tentatives d'injection SQL basiques
        """
        sql_patterns = [
            r'\bSELECT\b.*\bFROM\b',
            r'\bINSERT\b.*\bINTO\b',
            r'\bUPDATE\b.*\bSET\b',
            r'\bDELETE\b.*\bFROM\b',
            r'\bDROP\b.*\bTABLE\b',
            r'\bUNION\b.*\bSELECT\b',
            r'--',
            r';',
            r'\'\'',
            r'\"\"',
            r'\bOR\b.*=',
            r'\bAND\b.*='
        ]
        
        text_upper = text.upper()
        for pattern in sql_patterns:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def detect_command_injection(text: str) -> bool:
        """
        Détecte les tentatives d'injection de commandes
        """
        cmd_patterns = [
            r'[;&|`]',
            r'\brm\b.*\b-rf\b',
            r'\bwget\b',
            r'\bcurl\b',
            r'\bnc\b.*\b-e\b',
            r'\bbash\b.*\b-i\b',
            r'\$\{.*\}',
            r'\$\(.*\)'
        ]
        
        for pattern in cmd_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    # ============================================
    # VALIDATION DE FICHIERS
    # ============================================
    
    @staticmethod
    def validate_file_type(filename: str, content: bytes) -> bool:
        """
        Valide le type de fichier (empêche les attaques par extension)
        Utilise la signature magique plutôt que l'extension
        """
        import magic
        
        # Types MIME autorisés
        allowed_mime = {
            'image/jpeg': [b'\xFF\xD8\xFF'],
            'image/png': [b'\x89\x50\x4E\x47'],
            'image/webp': [b'RIFF....WEBP'],
            'audio/wav': [b'RIFF....WAVE'],
            'audio/mpeg': [b'\xFF\xFB', b'\xFF\xF3', b'\xFF\xF2'],
            'audio/ogg': [b'OggS'],
            'audio/mp4': [b'....ftyp']
        }
        
        try:
            mime = magic.from_buffer(content[:1024], mime=True)
            
            # Vérifier le MIME
            if mime not in allowed_mime:
                return False
            
            # Vérifier la signature (en production)
            ext = filename.split('.')[-1].lower()
            allowed_ext = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'webp': 'image/webp',
                'wav': 'audio/wav',
                'mp3': 'audio/mpeg',
                'ogg': 'audio/ogg',
                'm4a': 'audio/mp4'
            }
            
            if ext not in allowed_ext or allowed_ext[ext] != mime:
                return False
            
            return True
        except Exception as e:
            logger.error(f"Erreur validation fichier: {e}")
            return False
    
    @staticmethod
    def validate_image_size(image: bytes, max_size: Tuple[int, int] = (1920, 1080)) -> bool:
        """
        Valide la taille d'une image (empêche les bombes de décompression)
        """
        try:
            from PIL import Image
            import io
            
            img = Image.open(io.BytesIO(image))
            width, height = img.size
            
            if width > max_size[0] or height > max_size[1]:
                return False
            
            # Vérifier que l'image n'est pas malformée
            img.verify()
            
            return True
        except Exception as e:
            logger.error(f"Erreur validation image: {e}")
            return False
    
    # ============================================
    # PROTECTION CONTRE LE RATE LIMITING
    # ============================================
    
    @staticmethod
    def get_rate_limit_key() -> str:
        """
        Génère une clé unique pour le rate limiting
        Combine IP, User-Agent et d'autres facteurs
        """
        ip = request.remote_addr or 'unknown'
        ua = request.headers.get('User-Agent', 'unknown')
        # Ajouter un hash pour éviter les collisions
        return hashlib.sha256(f"{ip}:{ua}".encode()).hexdigest()
    
    # ============================================
    # DÉTECTION DES ATTAQUES
    # ============================================
    
    @staticmethod
    def detect_bruteforce(ip: str, threshold: int = 5, window: int = 300) -> bool:
        """
        Détecte les attaques par brute force
        """
        from core.cache import cache
        
        key = f"bruteforce:{ip}"
        attempts = cache.get(key) or 0
        
        if attempts >= threshold:
            return True
        
        cache.setex(key, window, attempts + 1)
        return False
    
    @staticmethod
    def detect_ddos() -> bool:
        """
        Détection basique de DDoS (à compléter avec un vrai WAF)
        """
        from core.cache import cache
        
        ip = request.remote_addr
        key = f"ddos:{ip}"
        
        # Compter les requêtes par IP
        count = cache.get(key) or 0
        
        # Seuil de 100 requêtes en 10 secondes
        if count > 100:
            return True
        
        cache.setex(key, 10, count + 1)
        return False
    
    # ============================================
    # GÉNÉRATION DE NOMBRES ALÉATOIRES SÉCURISÉS
    # ============================================
    
    @staticmethod
    def secure_random_string(length: int = 32) -> str:
        """
        Génère une chaîne aléatoire cryptographiquement sécurisée
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def secure_random_bytes(length: int = 32) -> bytes:
        """
        Génère des bytes aléatoires cryptographiquement sécurisés
        """
        return secrets.token_bytes(length)