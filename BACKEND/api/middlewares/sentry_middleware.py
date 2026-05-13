"""
Middleware Sentry pour Flask
Capture des erreurs et contexte des requêtes
"""

import sentry_sdk
from flask import request, g
from functools import wraps
from utils.network import get_client_ip


class SentryMiddleware:
    """Middleware pour capturer les requêtes et erreurs avec Sentry"""
    
    def __init__(self, app, config):
        self.app = app
        self.config = config
    
    def before_request(self):
        """Avant chaque requête"""
        try:
            if 'user_id' in g and hasattr(g, 'user_id'):
                sentry_sdk.set_user({
                    'id': str(g.user_id),
                    'username': getattr(g, 'username', None),
                })
            sentry_sdk.set_tag('method', request.method)
            sentry_sdk.set_tag('endpoint', request.endpoint or 'unknown')
            sentry_sdk.set_tag('path', request.path)
            sentry_sdk.set_context('request', {
                'method': request.method,
                'url': request.url,
                'remote_addr': get_client_ip(request),
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'content_type': request.content_type,
            })
            sentry_sdk.set_tag('environment', self.config.get('ENV', 'unknown'))
            sentry_sdk.set_tag('version', self.config.get('API_VERSION', 'unknown'))
        except Exception:
            pass

    def after_request(self, response):
        """Après chaque requête"""
        try:
            if response.status_code >= 400:
                sentry_sdk.set_tag('status_code', response.status_code)
                sentry_sdk.add_breadcrumb(
                    message=f"{request.method} {request.path} -> {response.status_code}",
                    category='http',
                    level='warning' if response.status_code >= 500 else 'info',
                    data={
                        'status_code': response.status_code,
                        'method': request.method,
                        'path': request.path,
                    }
                )
            sentry_sdk.set_user(None)
        except Exception:
            pass
        return response
    
    @staticmethod
    def capture_error_handler(error):
        """Gestionnaire d'erreur global pour capturer avec Sentry"""
        
        # Récupérer l'état de la requête
        sentry_sdk.set_context('error', {
            'type': type(error).__name__,
            'message': str(error),
        })
        
        # Capturer l'exception
        sentry_sdk.capture_exception(error)


def setup_sentry_middleware(app, config):
    """Configure le middleware Sentry"""
    
    middleware = SentryMiddleware(app, config)
    
    app.before_request(middleware.before_request)
    app.after_request(middleware.after_request)
    
    return middleware


def sentry_trace(func):
    """Décorateur pour tracer une fonction avec Sentry"""
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        with sentry_sdk.start_transaction(
            op="task",
            name=func.__name__,
            description=func.__doc__ or func.__name__
        ) as transaction:
            return func(*args, **kwargs)
    
    return wrapper
