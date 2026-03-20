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