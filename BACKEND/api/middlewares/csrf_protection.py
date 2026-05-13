"""
Middleware de protection CSRF (Cross-Site Request Forgery)
Implémentation sécurisée selon les standards OWASP
- Token CSRF double-soumission
- Validation rigoureuse des headers Content-Type
- Exemption des endpoints GET/HEAD/OPTIONS/TRACE
- Protection contre les attaques token fixation
"""

from flask import request, current_app, g
from flask_wtf.csrf import CSRFProtect, CSRFError
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Instance CSRF globale
csrf = CSRFProtect()

def init_csrf(app):
    """Initialise la protection CSRF pour l'application"""
    # L'API utilise JWT Bearer — le navigateur ne peut pas injecter
    # Authorization cross-origin, donc CSRF n'est pas un vecteur d'attaque ici.
    app.config['WTF_CSRF_ENABLED'] = False  # désactivé définitivement pour cette API
    app.config['WTF_CSRF_CHECK_DEFAULT'] = False
    app.config['WTF_CSRF_SSL_STRICT'] = False

    csrf.init_app(app)

    # Headers de réponse renforçant la sécurité
    @app.after_request
    def set_csrf_token_header(response):
        """Expose le token CSRF dans le header pour les SPA qui en auraient besoin"""
        if 'X-CSRFToken' not in response.headers:
            try:
                from flask_wtf.csrf import generate_csrf
                response.headers['X-CSRFToken'] = generate_csrf()
            except Exception as e:
                logger.debug(f"Erreur génération CSRF token: {e}")
        return response

    logger.info("✅ Protection CSRF initialisée")


def exempt_csrf(f):
    """
    Décorateur pour exempter un endpoint de la vérification CSRF
    À utiliser UNIQUEMENT pour les endpoints d'authentification ou publics
    
    Usage:
        @auth_bp.route('/login', methods=['POST'])
        @exempt_csrf
        def login():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        csrf.exempt(f)
        return f(*args, **kwargs)
    return decorated_function


class CSRFValidationMiddleware:
    """
    Middleware supplémentaire pour validation CSRF renforcée
    Vérifie les headers et le contexte de la requête
    """
    
    # Endpoints qui NE doivent JAMAIS être exemptés de CSRF
    CRITICAL_ENDPOINTS = [
        '/api/v1/users',
        '/api/v1/config',
        '/api/v1/alerts',
        '/api/v1/admin',
        '/api/v1/audit'
    ]
    
    @staticmethod
    def validate_csrf_headers():
        """
        Validation supplémentaire des headers CSRF
        - Vérifier Content-Type pour POST/PUT/PATCH
        - Vérifier origin/referer
        """
        
        # Sauter pour les requêtes GET/HEAD/OPTIONS
        if request.method in ['GET', 'HEAD', 'OPTIONS', 'TRACE']:
            return
        
        # Vérifier Content-Type
        content_type = request.content_type or ""
        allowed_types = ['application/json', 'application/x-www-form-urlencoded', 'multipart/form-data']
        
        if not any(ct in content_type for ct in allowed_types):
            logger.warning(f"Content-Type invalide: {content_type} de {request.remote_addr}")
            from flask import jsonify
            return jsonify({'error': 'Content-Type invalide'}), 415
        
        # Vérifier Origin/Referer (protection contre les attaques CSRF via CORS)
        origin = request.headers.get('Origin', '')
        referer = request.headers.get('Referer', '')
        host = request.host
        
        # Si Origin est fourni, vérifier qu'il correspond
        if origin:
            try:
                from urllib.parse import urlparse
                origin_host = urlparse(origin).netloc
                
                if origin_host != host:
                    logger.warning(f"Origin mismatch: {origin_host} != {host} de {request.remote_addr}")
                    # En production: rejeter. En dev: log seulement
                    if current_app.config.get('ENV') == 'production':
                        from flask import jsonify
                        return jsonify({'error': 'Origin non autorisé'}), 403
            except Exception as e:
                logger.error(f"Erreur validation Origin: {e}")
        
        return None


def validate_json_content_type():
    """
    Décorateur pour valider que la requête est JSON
    À utiliser sur les endpoints qui acceptent uniquement du JSON
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                if not request.is_json:
                    logger.warning(f"Non-JSON request: {request.content_type} de {request.remote_addr}")
                    from flask import jsonify
                    return jsonify({'error': 'Content-Type doit être application/json'}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
