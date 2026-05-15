"""
Middleware Sentry pour Flask
Capture des erreurs et contexte des requêtes.

sentry_sdk n'est importé qu'à l'exécution des méthodes, afin de ne pas
ralentir le démarrage quand Sentry n'est pas configuré (dev).
"""

from flask import request, g
from functools import wraps
from utils.network import get_client_ip


def _sdk():
    """Retourne sentry_sdk si installé ET initialisé, sinon None."""
    try:
        import sentry_sdk
        return sentry_sdk
    except ImportError:
        return None


class SentryMiddleware:
    """Middleware pour capturer les requêtes et erreurs avec Sentry"""

    def __init__(self, app, config):
        self.app = app
        self.config = config

    def before_request(self):
        sdk = _sdk()
        if not sdk:
            return
        try:
            if 'user_id' in g and hasattr(g, 'user_id'):
                sdk.set_user({'id': str(g.user_id), 'username': getattr(g, 'username', None)})
            sdk.set_tag('method', request.method)
            sdk.set_tag('endpoint', request.endpoint or 'unknown')
            sdk.set_tag('path', request.path)
            sdk.set_context('request', {
                'method': request.method,
                'url': request.url,
                'remote_addr': get_client_ip(request),
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'content_type': request.content_type,
            })
            sdk.set_tag('environment', self.config.get('ENV', 'unknown'))
            sdk.set_tag('version', self.config.get('API_VERSION', 'unknown'))
        except Exception:
            pass

    def after_request(self, response):
        sdk = _sdk()
        if not sdk:
            return response
        try:
            if response.status_code >= 400:
                sdk.set_tag('status_code', response.status_code)
                sdk.add_breadcrumb(
                    message=f"{request.method} {request.path} -> {response.status_code}",
                    category='http',
                    level='warning' if response.status_code >= 500 else 'info',
                    data={'status_code': response.status_code, 'method': request.method, 'path': request.path},
                )
            sdk.set_user(None)
        except Exception:
            pass
        return response

    @staticmethod
    def capture_error_handler(error):
        sdk = _sdk()
        if not sdk:
            return
        sdk.set_context('error', {'type': type(error).__name__, 'message': str(error)})
        sdk.capture_exception(error)


def setup_sentry_middleware(app, config):
    """Configure le middleware Sentry (no-op si sentry_sdk absent)"""
    middleware = SentryMiddleware(app, config)
    app.before_request(middleware.before_request)
    app.after_request(middleware.after_request)
    return middleware


def sentry_trace(func):
    """Décorateur pour tracer une fonction avec Sentry (no-op si Sentry absent)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        sdk = _sdk()
        if not sdk:
            return func(*args, **kwargs)
        with sdk.start_transaction(op="task", name=func.__name__,
                                   description=func.__doc__ or func.__name__):
            return func(*args, **kwargs)
    return wrapper
