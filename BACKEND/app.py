"""
Application principale BioAccess Secure
Configuration et initialisation de tous les composants
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_compress import Compress
# PrometheusMetrics importé à la demande dans create_app() si PROMETHEUS_ENABLED=True
# from flasgger import Flasgger

# Configuration
from config import config_by_name
# OPENAPI_SPEC importé à la demande (Swagger désactivé en dev)

# Core
from core.database import db, init_db, health_check
from core.security import SecurityManager
from core.logger import setup_logger
from core.errors import register_error_handlers
from core.cache import init_cache
from core.queue import init_queue
from core.sentry import SentryConfig

# Middlewares
from api.middlewares.rate_limiter import limiter, init_rate_limiter
from api.middlewares.security_headers import SecurityHeadersMiddleware
from api.middlewares.csrf_protection import csrf, init_csrf, CSRFValidationMiddleware
# from api.middlewares.audit import AuditMiddleware  # Optional audit middleware
from api.middlewares.sentry_middleware import setup_sentry_middleware

# Blueprints
from api.v1 import (
    auth_bp, users_bp, logs_bp, alerts_bp,
    dashboard_bp, biometric_bp, access_bp, audit_bp, facial_bp, health_bp,
    enrollment_bp, admin_biometric_bp, config_bp, desktop_bp
)

# Utils
from utils.network import get_client_ip

def create_app(config_name=None):
    """Factory pattern pour créer l'application Flask"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # ============================================
    # INITIALISATION DES EXTENSIONS
    # ============================================
    
    # Compression Gzip
    Compress(app)
    
    # Protection CSRF (OWASP A01 - Broken Access Control)
    init_csrf(app)
    
    # CORS sécurisé
    CORS(
        app,
        origins=app.config['CORS_ORIGINS'].split(','),
        supports_credentials=app.config['CORS_ALLOW_CREDENTIALS'],
        allow_headers=['Content-Type', 'Authorization', 'X-CSRFToken', app.config['API_KEY_HEADER']],
        expose_headers=['Content-Disposition'],
        max_age=600
    )
    
    # Base de données
    init_db(app)
    
    # ============================================
    # LOGGING (AVANT autres services)
    # ============================================
    logger, audit_logger = setup_logger(app)
    app.logger = logger
    app.audit_logger = audit_logger
    
    # Cache Redis
    init_cache(app)
    
    # File d'attente (Celery)
    init_queue(app)
    
    # Rate Limiting
    init_rate_limiter(app)
    
    # Monitoring Prometheus (désactivé en dev pour accélérer le démarrage)
    if app.config.get('PROMETHEUS_ENABLED', False):
        try:
            from prometheus_flask_exporter import PrometheusMetrics
            metrics = PrometheusMetrics(app, path='/metrics')
            metrics.info('bioaccess_info', 'BioAccess Secure API', version='2.0.0')
        except Exception as e:
            logger.warning(f"⚠️  PrometheusMetrics non initialisé: {e}")
    
    # Monitoring Sentry (Error Tracking & Alerting)
    SentryConfig.init_sentry(app)
    
    # Documentation API OpenAPI/Swagger (Flasgger simplifié pour le dev)
    # try:
    #     swagger = Flasgger(app)
    #     logger.info("✅ Swagger/API Documentation initialisée")
    # except Exception as e:
    #     logger.warning(f"⚠️  Erreur Swagger: {e}")
    
    # ============================================
    # MIDDLEWARES PERSONNALISÉS
    # ============================================
    
    # Headers de sécurité
    app.wsgi_app = SecurityHeadersMiddleware(app.wsgi_app, app.config)
    
    # Audit logging (optional - if audit middleware exists)
    # app.wsgi_app = AuditMiddleware(app.wsgi_app, app.config)
    
    # Sentry monitoring (Error tracking & alerting)
    try:
        setup_sentry_middleware(app, app.config)
    except Exception as e:
        logger.warning(f"⚠️  Sentry middleware non initialisé: {e}")
    
    # ============================================
    # GESTIONNAIRES D'ERREURS
    # ============================================
    
    register_error_handlers(app)
    
    # ============================================
    # BEFORE_REQUEST / AFTER_REQUEST
    # ============================================
    
    @app.before_request
    def before_request():
        """Actions avant chaque requête"""
        try:
            g.client_ip = get_client_ip(request)
        except Exception:
            g.client_ip = request.remote_addr or 'unknown'

        g.user_agent = request.headers.get('User-Agent', 'unknown')

        if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': 'Fichier trop volumineux'}), 413

        try:
            csrf_error = CSRFValidationMiddleware.validate_csrf_headers()
            if csrf_error:
                return csrf_error
        except Exception as e:
            logger.error(f"Erreur CSRF validation: {e}")

    @app.after_request
    def after_request(response):
        """Actions après chaque requête"""
        try:
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

            content_type = response.content_type or ''
            if 'text/html' in content_type:
                response.headers['Content-Security-Policy'] = (
                    "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:; "
                    "connect-src 'self' http://localhost:5000 ws://localhost:5000; "
                    "media-src 'self' blob:;"
                )
            else:
                response.headers['Content-Security-Policy'] = (
                    "default-src 'none'; "
                    "frame-ancestors 'none'"
                )
        except Exception as e:
            logger.error(f"Erreur after_request headers: {e}")

        return response
    
    # ============================================
    # ROUTES DE SANTÉ ET MONITORING
    # ============================================
    
    @app.route('/health')
    def health():
        """Endpoint de healthcheck"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected' if health_check() else 'disconnected',
            'redis': cache_health_check(),
            'version': app.config['API_VERSION']
        })
    
    @app.route('/ready')
    def ready():
        """Endpoint de readiness (pour orchestrateur)"""
        if not health_check():
            return jsonify({'status': 'not ready'}), 503
        return jsonify({'status': 'ready'})
    
    @app.route('/')
    def index():
        """Redirige vers le login (frontend servi par run_prod.py)"""
        from flask import redirect
        return redirect('/login.html')
    
    # ============================================
    # SERVIR LES FICHIERS STATIQUES DU FRONTEND
    # ============================================
    
    from flask import send_from_directory, abort
    FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'FRONTEND')
    
    @app.route('/<path:filename>')
    def serve_frontend(filename):
        """Sert les fichiers statiques du frontend (HTML, JS, CSS, etc.)"""
        # Bloquer les routes API et endpoints de monitoring
        if filename.startswith(('api/', 'health', 'ready', 'metrics', 'docs')):
            return abort(404)
        try:
            return send_from_directory(FRONTEND_DIR, filename)
        except Exception:
            # Si le fichier n'existe pas, servir login.html (SPA fallback)
            try:
                return send_from_directory(FRONTEND_DIR, 'login.html')
            except Exception:
                return abort(404)
    
    # ============================================
    # ENREGISTREMENT DES BLUEPRINTS
    # ============================================

    api_prefix = app.config['API_PREFIX']

    # Blueprints obligatoires
    app.register_blueprint(health_bp,           url_prefix=f"{api_prefix}")
    app.register_blueprint(auth_bp,             url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(facial_bp,           url_prefix=f"{api_prefix}/facial")
    app.register_blueprint(dashboard_bp,        url_prefix=f"{api_prefix}/dashboard")
    app.register_blueprint(biometric_bp,        url_prefix=f"{api_prefix}/biometric")
    app.register_blueprint(enrollment_bp,       url_prefix=f"{api_prefix}/auth/biometric")
    app.register_blueprint(admin_biometric_bp,  url_prefix=f"{api_prefix}/admin/biometric")
    app.register_blueprint(config_bp,           url_prefix=f"{api_prefix}/config")
    app.register_blueprint(desktop_bp,          url_prefix=f"{api_prefix}/desktop")

    # Blueprints optionnels (vérifier None)
    if users_bp:
        app.register_blueprint(users_bp,  url_prefix=f"{api_prefix}/users")
    if logs_bp:
        app.register_blueprint(logs_bp,   url_prefix=f"{api_prefix}/logs")
    if alerts_bp:
        app.register_blueprint(alerts_bp, url_prefix=f"{api_prefix}/alerts")
    if access_bp:
        app.register_blueprint(access_bp, url_prefix=f"{api_prefix}/access")
    if audit_bp:
        app.register_blueprint(audit_bp,  url_prefix=f"{api_prefix}/audit")

    # Exempter toutes les routes API du CSRF.
    # Les routes JWT Bearer sont inhéremment CSRF-safe : un attaquant cross-origin
    # ne peut pas injecter un header Authorization Bearer depuis un autre domaine.
    # csrf.exempt() s'applique aux fonctions de vue (pas aux blueprints directement).
    for _endpoint, _view_func in app.view_functions.items():
        if _endpoint not in ('static', 'index', 'health', 'ready'):
            csrf.exempt(_view_func)
    
    app.logger.info(f"✅ Application BioAccess Secure démarrée en mode {config_name}")
    
    return app

def cache_health_check():
    """Vérifie la connexion Redis"""
    try:
        from core.cache import Cache
        Cache.set('health_check', 'ok', ex=5)
        result = Cache.get('health_check')
        return result == 'ok'
    except Exception as e:
        logging.error(f"Redis health check failed: {str(e)}")
        return False