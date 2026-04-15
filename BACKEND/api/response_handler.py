"""
Handler centralisé des réponses API
Standardise le format de toutes les réponses
"""

from flask import jsonify
from datetime import datetime


class APIResponse:
    """Standardise les réponses API"""
    
    @staticmethod
    def success(data=None, message="Succès", status_code=200, meta=None):
        """
        Réponse réussie
        
        Format:
        {
            "status": "success",
            "code": 200,
            "timestamp": "2026-04-12T10:30:45Z",
            "message": "Succès",
            "data": {...},
            "meta": {...}
        }
        """
        response = {
            "status": "success",
            "code": status_code,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": message
        }
        
        if data is not None:
            response["data"] = data
        
        if meta is not None:
            response["meta"] = meta
        
        return jsonify(response), status_code
    
    @staticmethod
    def error(message, error_code=None, status_code=400, details=None):
        """
        Réponse erreur
        
        Format:
        {
            "status": "error",
            "code": 400,
            "timestamp": "2026-04-12T10:30:45Z",
            "message": "Message d'erreur",
            "error_code": "VALIDATION_ERROR",
            "details": {...}
        }
        """
        response = {
            "status": "error",
            "code": status_code,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": message
        }
        
        if error_code:
            response["error_code"] = error_code
        
        if details is not None:
            response["details"] = details
        
        return jsonify(response), status_code
    
    @staticmethod
    def paginated(items, total, page, per_page, message="Résultats", status_code=200):
        """
        Réponse paginée
        """
        response = {
            "status": "success",
            "code": status_code,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": message,
            "data": items,
            "meta": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }
        }
        
        return jsonify(response), status_code
    
    @staticmethod
    def created(data=None, message="Créé avec succès"):
        """Réponse POST créée"""
        return APIResponse.success(data, message, 201)
    
    @staticmethod
    def no_content():
        """Réponse DELETE (204)"""
        return '', 204
    
    @staticmethod
    def unauthorized(message="Authentification requise"):
        """Réponse non authentifié"""
        return APIResponse.error(message, "UNAUTHORIZED", 401)
    
    @staticmethod
    def forbidden(message="Accès refusé"):
        """Réponse permission refusée"""
        return APIResponse.error(message, "FORBIDDEN", 403)
    
    @staticmethod
    def not_found(resource="Ressource"):
        """Réponse non trouvée"""
        return APIResponse.error(f"{resource} non trouvé(e)", "NOT_FOUND", 404)
    
    @staticmethod
    def conflict(message="Conflit"):
        """Réponse conflit"""
        return APIResponse.error(message, "CONFLICT", 409)
    
    @staticmethod
    def too_many_requests(message="Trop de requêtes, réessayez plus tard"):
        """Réponse rate limited"""
        return APIResponse.error(message, "RATE_LIMIT_EXCEEDED", 429)
    
    @staticmethod
    def validation_error(message, details=None):
        """Erreur validation"""
        return APIResponse.error(message, "VALIDATION_ERROR", 400, details)
    
    @staticmethod
    def server_error(message="Erreur interne du serveur"):
        """Erreur serveur 500"""
        return APIResponse.error(message, "INTERNAL_SERVER_ERROR", 500)


# Décorateur pour capturer les exceptions et les convertir en réponses standardisées
def handle_api_errors(f):
    """
    Décorateur pour convertir les exceptions standard en réponses API
    
    Utilisation:
    @app.route('/api/endpoint')
    @handle_api_errors
    def endpoint():
        if not valid:
            raise ValidationError("Message")
        return APIResponse.success(data)
    """
    from functools import wraps
    from core.errors import APIError, ValidationError, AuthenticationError, AuthorizationError, NotFoundError
    
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return APIResponse.validation_error(e.message, e.payload)
        except AuthenticationError as e:
            return APIResponse.unauthorized(e.message)
        except AuthorizationError as e:
            return APIResponse.forbidden(e.message)
        except NotFoundError as e:
            return APIResponse.not_found(e.message)
        except APIError as e:
            return APIResponse.error(e.message, status_code=e.status_code)
        except Exception as e:
            import logging
            logging.error(f"Erreur non gérée: {e}", exc_info=True)
            return APIResponse.server_error()
    
    return wrapper
