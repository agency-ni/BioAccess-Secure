"""
Validateurs pour les données entrantes
"""

import re
from datetime import datetime
import ipaddress

class Validators:
    """Collection de validateurs"""
    
    @staticmethod
    def validate_email(email):
        """Valide un email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """
        Valide un mot de passe:
        - 8+ caractères
        - Au moins une majuscule
        - Au moins une minuscule
        - Au moins un chiffre
        - Au moins un caractère spécial
        """
        if len(password) < 8:
            return False, "Trop court (min 8 caractères)"
        
        if not re.search(r'[A-Z]', password):
            return False, "Doit contenir une majuscule"
        
        if not re.search(r'[a-z]', password):
            return False, "Doit contenir une minuscule"
        
        if not re.search(r'[0-9]', password):
            return False, "Doit contenir un chiffre"
        
        if not re.search(r'[@$!%*?&]', password):
            return False, "Doit contenir un caractère spécial (@$!%*?&)"
        
        return True, "OK"
    
    @staticmethod
    def validate_ip(ip):
        """Valide une adresse IP (IPv4/IPv6)"""
        try:
            ipaddress.ip_address(ip)
            return True
        except:
            return False
    
    @staticmethod
    def validate_mac(mac):
        """Valide une adresse MAC"""
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return re.match(pattern, mac) is not None
    
    @staticmethod
    def validate_phone(phone):
        """Valide un numéro de téléphone (format international)"""
        pattern = r'^\+?[0-9]{8,15}$'
        return re.match(pattern, phone) is not None
    
    @staticmethod
    def validate_date(date_str):
        """Valide une date au format YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except:
            return False
    
    @staticmethod
    def validate_uuid(uuid_str):
        """Valide un UUID"""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return re.match(pattern, uuid_str, re.IGNORECASE) is not None
    
    @staticmethod
    def validate_url(url):
        """Valide une URL"""
        pattern = r'^https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*$'
        return re.match(pattern, url) is not None
    
    @staticmethod
    def validate_json(json_str):
        """Valide une chaîne JSON"""
        import json
        try:
            json.loads(json_str)
            return True
        except:
            return False
    
    # ========== VALIDATEURS BIOMÉTRIQUES ==========
    
    @staticmethod
    def validate_base64_image(image_data_b64, max_size_bytes=5 * 1024 * 1024):
        """
        Valide une image en base64
        
        Args:
            image_data_b64: Chaîne base64
            max_size_bytes: Taille max (défaut 5MB)
        
        Returns:
            (is_valid, error_message, decoded_bytes)
        """
        import base64
        
        if not image_data_b64:
            return False, "Image manquante", None
        
        try:
            # Décoder
            image_bytes = base64.b64decode(image_data_b64)
            
            # Vérifier la taille
            if len(image_bytes) > max_size_bytes:
                size_mb = len(image_bytes) / 1024 / 1024
                max_mb = max_size_bytes / 1024 / 1024
                return False, f"Image trop volumineux: {size_mb:.1f}MB (max {max_mb:.1f}MB)", None
            
            # Vérifier la signature de fichier (magic bytes)
            # JPEG: FF D8 FF
            # PNG: 89 50 4E 47
            # BMP: 42 4D
            valid_signatures = [
                (b'\xFF\xD8\xFF', 'JPEG'),
                (b'\x89PNG', 'PNG'),
                (b'BM', 'BMP'),
                (b'GIF', 'GIF')
            ]
            
            is_image = any(image_bytes.startswith(sig) for sig, _ in valid_signatures)
            if not is_image:
                return False, "Format image non valide (JPEG, PNG, BMP, GIF attendus)", None
            
            return True, "Valide", image_bytes
        
        except base64.binascii.Error:
            return False, "Format base64 invalide", None
        except Exception as e:
            return False, f"Erreur validation image: {str(e)}", None
    
    @staticmethod
    def validate_face_similarity_score(score):
        """Valide un score de similarité faciale (0.0 - 1.0)"""
        try:
            score = float(score)
            if 0.0 <= score <= 1.0:
                return True, "OK"
            else:
                return False, "Score doit être entre 0.0 et 1.0"
        except:
            return False, "Score invalide"
    
    @staticmethod
    def validate_biometric_template(template_data):
        """Valide un template biométrique"""
        if not template_data:
            return False, "Template manquant"
        
        if not isinstance(template_data, (list, bytes)):
            return False, "Template doit être un array ou bytes"
        
        if isinstance(template_data, list):
            if len(template_data) == 0:
                return False, "Template vide"
            if len(template_data) > 1000000:  # Limite raisonnable
                return False, "Template trop volumineux"
        
        return True, "Valide"