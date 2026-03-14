"""
Gestionnaire d'erreurs centralisé avec codes HTTP appropriés
"""

from flask import jsonify
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Exception personnalisée pour l'API"""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or {})
        rv['error'] = self.message
        rv['status'] = 'error'
        return rv

class ValidationError(APIError):
    """Erreur de validation des données"""
    def __init__(self, message, payload=None):
        super().__init__(message, 400, payload)

class AuthenticationError(APIError):
    """Erreur d'authentification"""
    def __init__(self, message="Authentification requise"):
        super().__init__(message, 401)

class AuthorizationError(APIError):
    """Erreur d'autorisation (permissions)"""
    def __init__(self, message="Accès non autorisé"):
        super().__init__(message, 403)

class NotFoundError(APIError):
    """Ressource non trouvée"""
    def __init__(self, resource="Ressource"):
        super().__init__(f"{resource} non trouvé(e)", 404)

class ConflictError(APIError):
    """Conflit (ex: email déjà existant)"""
    def __init__(self, message):
        super().__init__(message, 409)

class RateLimitError(APIError):
    """Trop de requêtes"""
    def __init__(self, message="Trop de requêtes, réessayez plus tard"):
        super().__init__(message, 429)

def register_error_handlers(app):
    """Enregistre les gestionnaires d'erreurs pour l'application"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        logger.warning(f"API Error {error.status_code}: {error.message}")
        return response
    
    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        response = jsonify({
            'error': error.description,
            'status': 'error'
        })
        response.status_code = error.code
        logger.warning(f"HTTP Error {error.code}: {error.description}")
        return response
    
    @app.errorhandler(500)
    def handle_500_error(error):
        logger.error(f"Internal Server Error: {error}")
        return jsonify({
            'error': 'Erreur interne du serveur',
            'status': 'error'
        }), 500
    
    @app.errorhandler(404)
    def handle_404_error(error):
        return jsonify({
            'error': 'Route non trouvée',
            'status': 'error'
        }), 404