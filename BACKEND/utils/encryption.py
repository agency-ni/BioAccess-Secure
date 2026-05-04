"""
Utilitaires de chiffrement
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class EncryptionManager:
    """Gestionnaire de chiffrement unifié"""
    
    @staticmethod
    def generate_key():
        """Génère une clé de chiffrement"""
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key(password: str, salt: bytes = None):
        """Dérive une clé à partir d'un mot de passe"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        """Chiffre des données"""
        f = Fernet(key)
        return f.encrypt(data)
    
    @staticmethod
    def decrypt(data: bytes, key: bytes) -> bytes:
        """Déchiffre des données"""
        f = Fernet(key)
        return f.decrypt(data)