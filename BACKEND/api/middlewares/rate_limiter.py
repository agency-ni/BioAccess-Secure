"""
Rate limiting minimaliste sans Flask-Limiter
Évite les blocages lors de l'import
"""

import os
from flask import g, request
import logging
from datetime import datetime, timedelta
from functools import wraps
import time

logger = logging.getLogger(__name__)

# Global limiter instance
limiter = None

def get_limiter_key():
    """
    Clé dynamique pour le rate limiting
    Combine: IP + User ID + Endpoint
    """
    user_id = getattr(g, 'user_id', None)
    endpoint = request.endpoint or 'unknown'
    ip = request.remote_addr
    
    if user_id:
        return f"limiter:{endpoint}:{user_id}"
    else:
        return f"limiter:{endpoint}:{ip}"


class SimpleRateLimiter:
    """
    Rate limiter minimaliste sans dépendance externe
    Stockage mémoire simple
    """
    
    def __init__(self, app=None):
        self.app = app
        self.requests = {}  # {key: [(timestamp, count), ...]}
        self.max_age = 3600  # 1 heure
        self.storage_uri = 'memory://'
    
    def init_app(self, app):
        """Initialiser avec l'app Flask"""
        self.app = app
        app.rate_limiter = self
    
    def limit(self, limit_string):
        """Décorateur pour appliquer le rate limiting"""
        # Parser le limit_string (ex: "5 per 15 minutes")
        parts = limit_string.split()
        if len(parts) < 3:
            return lambda f: f  # Pas de limite valide
        
        max_requests = int(parts[0])
        time_unit = parts[2].lower()
        
        # Convertir en secondes
        time_map = {
            'minute': 60,
            'minutes': 60,
            'hour': 3600,
            'hours': 3600,
            'second': 1,
            'seconds': 1,
            'day': 86400,
            'days': 86400
        }
        
        window_seconds = time_map.get(time_unit, 60)
        
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                key = get_limiter_key()
                now = time.time()
                
                # Nettoyer les anciennes entrées
                if key in self.requests:
                    self.requests[key] = [
                        (ts, count) for ts, count in self.requests[key]
                        if now - ts < window_seconds
                    ]
                    
                    # Compter les requêtes dans la fenêtre
                    current_count = sum(count for ts, count in self.requests[key])
                    
                    if current_count >= max_requests:
                        logger.warning(f"Rate limit exceeded for {key}")
                        from api.response_handler import APIResponse
                        return APIResponse.too_many_requests(
                            f"Limite dépassée. Max {max_requests} par {time_unit}."
                        )
                    
                    # Ajouter la requête courante
                    self.requests[key].append((now, 1))
                else:
                    # Première requête
                    self.requests[key] = [(now, 1)]
                
                return f(*args, **kwargs)
            
            return decorated_function
        
        return decorator


# Créer l'instance globale
limiter = SimpleRateLimiter()

def init_rate_limiter(app):
    """Initialise le rate limiter avec l'application"""
    global limiter
    limiter.init_app(app)

    if app.config.get('REDIS_ENABLED', False):
        try:
            limiter.storage_uri = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            logger.info("✅ Rate limiter utilise Redis")
        except Exception:
            limiter.storage_uri = "memory://"
            logger.warning("Fallback mémoire")
    else:
        limiter.storage_uri = "memory://"
        logger.info("✅ Rate limiter mémoire (Redis désactivé)")

    # Personnaliser la réponse en cas de dépassement
    @app.errorhandler(429)
    def ratelimit_handler(e):
        from api.response_handler import APIResponse
        return APIResponse.too_many_requests(
            f"Limite atteinte. {e.description if hasattr(e, 'description') else ''}"
        )


# ========== DÉCORATEURS SPÉCIFIQUES PAR ENDPOINT ==========

# Authentification
login_limiter = limiter.limit("5 per 15 minutes")          # 5 tentatives / 15min
register_limiter = limiter.limit("3 per hour")              # 3 registrations / heure
password_reset_limiter = limiter.limit("3 per hour")        # 3 reset / heure
forgot_password_limiter = limiter.limit("5 per hour")       # 5 requêtes / heure

# Biométrique
biometric_auth_limiter = limiter.limit("10 per minute")     # 10 auth tentatives / min
biometric_enroll_limiter = limiter.limit("5 per hour")      # 5 enrollments / heure
face_recognition_limiter = limiter.limit("20 per minute")   # 20 auth / minute

# API générale
api_read_limiter = limiter.limit("1000 per minute")         # 1000 GET / minute
api_write_limiter = limiter.limit("100 per minute")         # 100 POST/PUT/DELETE / minute
sensitive_limiter = limiter.limit("20 per minute")          # Opérations sensibles

# Admin
admin_limiter = limiter.limit("500 per minute")             # Accès admin
audit_limiter = limiter.limit("200 per minute")             # Consultation audit


# ========== CLASSE DE GESTION AVANCÉE ==========

class AdvancedRateLimiter:
    """
    Gestion avancée du rate limiting
    Support blacklist/whitelist
    """
    
    def __init__(self):
        self.blacklist = {}  # {key: expiry_time}
        self.whitelist = set()
        self.redis = None
        self.enabled = False
    
    def is_blacklisted(self, key):
        """Vérifie si une clé est dans la blacklist"""
        now = time.time()
        if key in self.blacklist:
            if self.blacklist[key] > now:
                return True
            else:
                del self.blacklist[key]
        return False
    
    def add_to_blacklist(self, key, duration_seconds=3600):
        """Ajoute une IP/utilisateur à la blacklist"""
        expiry = time.time() + duration_seconds
        self.blacklist[key] = expiry
        logger.warning(f"Added to blacklist: {key} for {duration_seconds}s")
        return True
    
    def is_whitelisted(self, key):
        """Vérifie si une clé est dans la whitelist"""
        return key in self.whitelist
    
    def add_to_whitelist(self, key):
        """Ajoute une IP/utilisateur à la whitelist"""
        self.whitelist.add(key)
        logger.info(f"Added to whitelist: {key}")
        return True
    
    def check_rate_limit(self, key, max_requests, window_seconds):
        """
        Vérification manuelle du rate limit
        Retourne: (is_allowed, remaining, reset_time)
        """
        if self.is_whitelisted(key):
            return True, max_requests, None
        
        if self.is_blacklisted(key):
            return False, 0, None
        
        return True, max_requests, None


# Instance globale
advanced_limiter = AdvancedRateLimiter()
