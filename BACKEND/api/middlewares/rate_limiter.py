"""
Rate limiting avancé avec Flask-Limiter
Support per-IP, per-user, et per-endpoint
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import g, request
from core.errors import RateLimitError
from core.database import db
import logging
import redis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Initialiser le rate limiter avec stratégie Redis pour la production
def get_limiter_key():
    """
    Clé dynamique pour le rate limiting
    Combine: IP + User ID + Endpoint
    """
    user_id = getattr(g, 'user_id', None)
    endpoint = request.endpoint or 'unknown'
    ip = get_remote_address()
    
    if user_id:
        return f"limiter:{endpoint}:{user_id}"
    else:
        return f"limiter:{endpoint}:{ip}"

limiter = Limiter(
    key_func=get_limiter_key,
    default_limits=["100 per hour"],
    # En développement: memory, en prod: redis
    storage_uri="memory://",
    strategy="fixed-window-elastic-expiry",
    on_breach=lambda limit, request, response, endpoint: logger.warning(
        f"Rate limit breached: {limit.key} for {request.remote_addr}"
    )
)

def init_rate_limiter(app):
    """Initialise le rate limiter avec l'application"""
    # Utiliser Redis en production
    if app.config.get('FLASK_ENV') == 'production':
        try:
            limiter.storage_uri = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
            logger.info("✅ Rate limiter utilise Redis backend")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de se connecter à Redis: {e}. Fallback à memory.")
    
    limiter.init_app(app)
    
    # Personnaliser la réponse en cas de dépassement
    @app.errorhandler(429)
    def ratelimit_handler(e):
        from api.response_handler import APIResponse
        return APIResponse.too_many_requests(
            f"Limite atteinte. {e.description}"
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
    Supporte: blacklist, whitelist, allowances personnalisées
    """
    
    def __init__(self, redis_client=None):
        """Initialise avec client Redis optionnel"""
        try:
            self.redis = redis_client or redis.from_url(
                'redis://localhost:6379/0',
                decode_responses=True
            )
            self.enabled = True
        except Exception as e:
            logger.warning(f"Redis non disponible: {e}. Features avancés désactivés.")
            self.enabled = False
            self.redis = None
    
    def check_rate_limit(self, key, max_requests, window_seconds):
        """
        Vérification manuelle du rate limit
        
        Args:
            key: Identifiant unique (ex: "user:123:login")
            max_requests: Nombre max de requêtes
            window_seconds: Fenêtre de temps en secondes
        
        Returns:
            (is_allowed, remaining, reset_time)
        """
        if not self.enabled or not self.redis:
            return True, max_requests, None
        
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            results = pipe.execute()
            
            current_count = results[0]
            
            if current_count <= max_requests:
                remaining = max_requests - current_count
                return True, remaining, window_seconds
            else:
                # Dépassé
                ttl = self.redis.ttl(key)
                return False, 0, ttl
        
        except Exception as e:
            logger.error(f"Erreur rate limit check: {e}")
            return True, max_requests, None  # Fail open
    
    def add_to_blacklist(self, key, duration_seconds=3600):
        """Ajoute une IP/utilisateur à la blacklist"""
        if not self.enabled or not self.redis:
            return False
        
        try:
            blacklist_key = f"blacklist:{key}"
            self.redis.setex(blacklist_key, duration_seconds, "1")
            logger.warning(f"Added to blacklist: {key} for {duration_seconds}s")
            return True
        except Exception as e:
            logger.error(f"Erreur blacklist: {e}")
            return False
    
    def is_blacklisted(self, key):
        """Vérifie si une clé est dans la blacklist"""
        if not self.enabled or not self.redis:
            return False
        
        try:
            blacklist_key = f"blacklist:{key}"
            return self.redis.exists(blacklist_key) > 0
        except Exception as e:
            logger.error(f"Erreur blacklist check: {e}")
            return False
    
    def add_to_whitelist(self, key):
        """Ajoute une IP/utilisateur à la whitelist"""
        if not self.enabled or not self.redis:
            return False
        
        try:
            whitelist_key = f"whitelist:{key}"
            self.redis.set(whitelist_key, "1")
            logger.info(f"Added to whitelist: {key}")
            return True
        except Exception as e:
            logger.error(f"Erreur whitelist: {e}")
            return False
    
    def is_whitelisted(self, key):
        """Vérifie si une clé est dans la whitelist"""
        if not self.enabled or not self.redis:
            return False
        
        try:
            whitelist_key = f"whitelist:{key}"
            return self.redis.exists(whitelist_key) > 0
        except Exception as e:
            logger.error(f"Erreur whitelist check: {e}")
            return False
    
    def get_stats(self, key):
        """Récupère les stats de rate limit d'une clé"""
        if not self.enabled or not self.redis:
            return None
        
        try:
            count = self.redis.get(key)
            ttl = self.redis.ttl(key)
            return {
                "current_count": int(count) if count else 0,
                "ttl_seconds": ttl,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur stats: {e}")
            return None

# Instance globale
advanced_limiter = AdvancedRateLimiter()