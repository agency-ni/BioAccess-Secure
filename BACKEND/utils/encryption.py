"""
Utilitaires de chiffrement supplémentaires
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import os

class EncryptionUtils:
    """Utilitaires de chiffrement"""
    
    @staticmethod
    def generate_key():
        """Génère une clé de chiffrement aléatoire"""
        return Fernet.generate_key()
    
    @staticmethod
    def derive_key(password, salt=None):
        """Dérive une clé à partir d'un mot de passe"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt
    
    @staticmethod
    def encrypt_file(file_path, key):
        """Chiffre un fichier"""
        fernet = Fernet(key)
        
        with open(file_path, 'rb') as f:
            data = f.read()
        
        encrypted = fernet.encrypt(data)
        
        with open(file_path + '.enc', 'wb') as f:
            f.write(encrypted)
        
        return file_path + '.enc'
    
    @staticmethod
    def decrypt_file(file_path, key):
        """Déchiffre un fichier"""
        fernet = Fernet(key)
        
        with open(file_path, 'rb') as f:
            encrypted = f.read()
        
        decrypted = fernet.decrypt(encrypted)
        
        output_path = file_path.replace('.enc', '')
        with open(output_path, 'wb') as f:
            f.write(decrypted)
        
        return output_path