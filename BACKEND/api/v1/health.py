"""
Health Check et Readiness Endpoints
Pour Docker et orchestrateurs (Kubernetes, Docker Swarm)
"""

from datetime import datetime, timezone
from flask import Blueprint, jsonify, current_app
from core.database import health_check

health_bp = Blueprint('health', __name__)

def cache_health_check():
    """Vérifie la connexion Redis"""
    try:
        from core.cache import cache
        cache.set('health_check_v1', 'ok', ex=5)
        return cache.get('health_check_v1') == 'ok'
    except Exception as e:
        current_app.logger.error(f"Cache health check failed: {e}")
        return False

@health_bp.route('/health', methods=['GET'])
def health():
    """
    Liveness probe pour Docker
    Retourne 200 si le service est opérationnel
    """
    try:
        db_status = health_check()
        cache_status = cache_health_check()
        
        response = {
            "status": "healthy" if (db_status and cache_status) else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "database": "connected" if db_status else "disconnected",
                "cache": "connected" if cache_status else "disconnected",
                "api": "operational"
            },
            "version": current_app.config.get('API_VERSION', '2.0.0')
        }
        
        # Retourner 200 si au moins DB et API sont OK
        status_code = 200 if (db_status and True) else 503
        return jsonify(response), status_code
    
    except Exception as e:
        current_app.logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503

@health_bp.route('/ready', methods=['GET'])
def ready():
    """
    Readiness probe pour Docker/Kubernetes
    Retourne 200 si le service peut traiter les requêtes
    """
    try:
        db_status = health_check()
        cache_status = cache_health_check()
        
        if not db_status:
            return jsonify({
                "status": "not ready",
                "reason": "database connection failed"
            }), 503
        
        return jsonify({
            "status": "ready",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Readiness check failed: {e}")
        return jsonify({
            "status": "not ready",
            "error": str(e)
        }), 503

@health_bp.route('/metrics', methods=['GET'])
def metrics():
    """
    Endpoint de métriques simples pour monitoring
    À utiliser avec Prometheus additionnellement
    """
    try:
        db_status = health_check()
        cache_status = cache_health_check()
        
        return jsonify({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": current_app.config.get('START_TIME', 0),
            "checks": {
                "database": {"status": "ok" if db_status else "error"},
                "cache": {"status": "ok" if cache_status else "error"}
            },
            "api": {
                "version": current_app.config.get('API_VERSION', '2.0.0'),
                "environment": current_app.config.get('ENV', 'development')
            }
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
