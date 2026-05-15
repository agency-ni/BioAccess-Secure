"""
Gestion du cache Redis pour performances et rate limiting
"""

import redis
from flask import current_app
import json
import logging
from typing import Any, Optional
import os

logger = logging.getLogger(__name__)

# Instance Redis
redis_client = None

def init_cache(app):
    """Initialise la connexion Redis"""
    global redis_client
    
    # En développement ou si Redis est volontairement désactivé
    if not app.config.get('REDIS_ENABLED', True):
        logger.info("⚠️  Cache Redis désactivé par configuration")
        redis_client = None
        return
    
    try:
        redis_client = redis.from_url(
            app.config['REDIS_URL'],
            max_connections=app.config['REDIS_MAX_CONNECTIONS'],
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=2,
            retry_on_timeout=False,
            health_check_interval=30
        )
        # Tester la connexion
        redis_client.ping()
        logger.info("✅ Cache Redis initialisé avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur connexion Redis: {e}")
        if app.config['FLASK_ENV'] == 'production':
            raise
        logger.warning("⚠️  Redis non disponible - utilisation du cache en mémoire")
        redis_client = None

def get_cache():
    """Retourne l'instance Redis"""
    return redis_client

class Cache:
    """Wrapper pour les opérations de cache"""
    
    @staticmethod
    def get(key: str) -> Optional[str]:
        """Récupère une valeur du cache"""
        if not redis_client:
            return None
        try:
            return redis_client.get(key)
        except Exception as e:
            logger.error(f"Erreur cache get {key}: {e}")
            return None
    
    @staticmethod
    def set(key: str, value: str, ex: int = 3600) -> bool:
        """Stocke une valeur dans le cache avec expiration"""
        if not redis_client:
            return False
        try:
            return redis_client.setex(key, ex, value)
        except Exception as e:
            logger.error(f"Erreur cache set {key}: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """Supprime une clé du cache"""
        if not redis_client:
            return False
        try:
            return redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"Erreur cache delete {key}: {e}")
            return False
    
    @staticmethod
    def incr(key: str, amount: int = 1) -> Optional[int]:
        """Incrémente un compteur"""
        if not redis_client:
            return None
        try:
            return redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Erreur cache incr {key}: {e}")
            return None
    
    @staticmethod
    def expire(key: str, time: int) -> bool:
        """Définit l'expiration d'une clé"""
        if not redis_client:
            return False
        try:
            return redis_client.expire(key, time)
        except Exception as e:
            logger.error(f"Erreur cache expire {key}: {e}")
            return False
    
    @staticmethod
    def set_json(key: str, data: Any, ex: int = 3600) -> bool:
        """Stocke un objet JSON dans le cache"""
        try:
            return Cache.set(key, json.dumps(data), ex)
        except Exception as e:
            logger.error(f"Erreur cache set_json {key}: {e}")
            return False
    
    @staticmethod
    def get_json(key: str) -> Optional[Any]:
        """Récupère un objet JSON du cache"""
        val = Cache.get(key)
        if val:
            try:
                return json.loads(val)
            except:
                return None
        return None