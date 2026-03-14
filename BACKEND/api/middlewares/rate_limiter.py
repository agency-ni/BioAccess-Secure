"""
Rate limiting avancé avec Flask-Limiter
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from core.errors import RateLimitError
import logging

logger = logging.getLogger(__name__)

# Initialiser le rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://",  # En production, utiliser Redis
    strategy="fixed-window",
    on_breach=lambda limit, request, response: logger.warning(
        f"Rate limit breached: {limit.key}"
    )
)

def init_rate_limiter(app):
    """Initialise le rate limiter avec l'application"""
    limiter.init_app(app)
    
    # Personnaliser la réponse en cas de dépassement
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return RateLimitError().to_dict(), 429

# Décorateurs spécifiques
login_limiter = limiter.limit("5 per 15 minutes")  # 5 tentatives / 15min
api_limiter = limiter.limit("100 per minute")      # 100 req / minute
sensitive_limiter = limiter.limit("20 per minute") # Opérations sensibles