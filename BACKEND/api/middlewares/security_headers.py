"""
Middleware pour ajouter des headers de sécurité à toutes les réponses
Protège contre XSS, clickjacking, MIME sniffing, etc.
"""

from flask import request, jsonify
import time

"""
WSGI Middleware pour ajouter des en-têtes de sécurité
"""

import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware:
    """
    WSGI Middleware pour ajouter des en-têtes de sécurité
    """
    
    def __init__(self, app, config):
        self.app = app
        self.config = config
    
    def __call__(self, environ, start_response):
        try:
            def custom_start_response(status, headers, exc_info=None):
                try:
                    # Headers de sécurité complets (ancienne version)
                    security_headers = [
                        ('X-Content-Type-Options', 'nosniff'),
                        ('X-Frame-Options', 'DENY'),
                        ('X-XSS-Protection', '1; mode=block'),
                        ('Referrer-Policy', 'strict-origin-when-cross-origin'),
                        ('Permissions-Policy', 'geolocation=(), microphone=(self), camera=(self)'),
                        ('Cross-Origin-Resource-Policy', 'cross-origin'),
                    ]
                    
                    # HSTS si session sécurisée
                    if self.config.get('SESSION_COOKIE_SECURE', False):
                        security_headers.append(('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload'))
                    
                    if isinstance(headers, list):
                        headers.extend(security_headers)
                except Exception as header_err:
                    logger.warning(f"Erreur ajout headers sécurité: {header_err}")
                
                return start_response(status, headers, exc_info)
            
            return self.app(environ, custom_start_response)
        
        except Exception as e:
            # En cas d'erreur critique, on Continue sans les headers
            logger.error(f"SecurityHeadersMiddleware crash: {e}")
            return self.app(environ, start_response)


class RateLimitMiddleware:
    """
    Middleware pour le rate limiting au niveau WSGI
    """
    
    def __init__(self, app, limiter):
        self.app = app
        self.limiter = limiter
    
    def __call__(self, environ, start_response):
        # Implémentation du rate limiting
        # À compléter avec Redis
        return self.app(environ, start_response)


class AuditMiddleware:
    """
    Middleware pour journaliser toutes les requêtes
    """
    
    def __init__(self, app, config):
        self.app = app
        self.config = config
        self.logger = logging.getLogger('audit')
    
    def __call__(self, environ, start_response):
        start_time = time.time()
        
        # Récupérer les infos de la requête
        method = environ.get('REQUEST_METHOD')
        path = environ.get('PATH_INFO')
        ip = environ.get('REMOTE_ADDR')
        user_agent = environ.get('HTTP_USER_AGENT', 'unknown')
        
        def custom_start_response(status, headers, exc_info=None):
            # Calculer la durée
            duration = int((time.time() - start_time) * 1000)
            
            # Journaliser
            self.logger.info(json.dumps({
                'timestamp': datetime.utcnow().isoformat(),
                'method': method,
                'path': path,
                'status': status,
                'ip': ip,
                'user_agent': user_agent,
                'duration_ms': duration
            }))
            
            return start_response(status, headers, exc_info)
        
        return self.app(environ, custom_start_response)