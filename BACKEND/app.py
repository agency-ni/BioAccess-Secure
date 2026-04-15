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
from prometheus_flask_exporter import PrometheusMetrics
from flasgger import Flasgger

# Configuration
from config import config_by_name
from openapi import OPENAPI_SPEC

# Core
from core.database import db, init_db, health_check
from core.security import SecurityManager
from core.logger import setup_logger
from core.errors import register_error_handlers
from core.cache import init_cache
from core.queue import init_queue
from core.sentry import SentryConfig, SentryAlerting

# Middlewares
from api.middlewares.rate_limit import limiter, init_rate_limiter
from api.middlewares.security_headers import SecurityHeadersMiddleware
from api.middlewares.audit import AuditMiddleware
from api.middlewares.sentry_middleware import setup_sentry_middleware

# Blueprints
from api.v1 import (
    auth_bp, users_bp, logs_bp, alerts_bp,
    dashboard_bp, biometric_bp, access_bp, audit_bp, facial_bp, health_bp
)

# Utils
from utils.network import get_client_ip
from utils.encryption import init_encryption

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
    
    # Cache Redis
    init_cache(app)
    
    # File d'attente (Celery)
    init_queue(app)
    
    # Rate Limiting
    init_rate_limiter(app)
    
    # Monitoring Prometheus
    metrics = PrometheusMetrics(app, path='/metrics')
    metrics.info('bioaccess_info', 'BioAccess Secure API', version='2.0.0')
    
    # Monitoring Sentry (Error Tracking & Alerting)
    SentryConfig.init_sentry(app)
    
    # Documentation API OpenAPI/Swagger
    swagger = Flasgger(
        app,
        spec=OPENAPI_SPEC,
        title='BioAccess Secure API',
        version='2.0.0',
        uiversion=3,
        swagger_ui_path='/api/docs',
        swagger_ui_bundle_js='//cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js',
        swagger_ui_standalone_preset_js='//cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-standalone-preset.js',
        swagger_css='//cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css',
    )
    
    # ============================================
    # MIDDLEWARES PERSONNALISÉS
    # ============================================
    
    # Headers de sécurité
    app.wsgi_app = SecurityHeadersMiddleware(app.wsgi_app, app.config)
    
    # Audit logging
    app.wsgi_app = AuditMiddleware(app.wsgi_app, app.config)
    
    # Sentry monitoring (Error tracking & alerting)
    setup_sentry_middleware(app, app.config)
    
    # ============================================
    # LOGGING
    # ============================================
    
    logger, audit_logger = setup_logger(app)
    app.logger = logger
    app.audit_logger = audit_logger
    
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
        # Stocker l'IP client
        g.client_ip = get_client_ip(request)
        
        # Stocker le User-Agent
        g.user_agent = request.headers.get('User-Agent', 'unknown')
        
        # Vérification basique de sécurité
        if request.content_length and request.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': 'Fichier trop volumineux'}), 413
    
    @app.after_request
    def after_request(response):
        """Actions après chaque requête"""
        # Ajouter des headers de sécurité
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # CSP (Content Security Policy)
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'"
        )
        
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
        """Page d'accueil de l'API"""
        return jsonify({
            'name': 'BioAccess Secure API',
            'version': app.config['API_VERSION'],
            'status': 'operational',
            'endpoints': {
                'auth': f"{app.config['API_PREFIX']}/auth",
                'users': f"{app.config['API_PREFIX']}/users",
                'logs': f"{app.config['API_PREFIX']}/logs",
                'alerts': f"{app.config['API_PREFIX']}/alerts",
                'dashboard': f"{app.config['API_PREFIX']}/dashboard",
                'biometric': f"{app.config['API_PREFIX']}/biometric",
                'access': f"{app.config['API_PREFIX']}/access",
                'audit': f"{app.config['API_PREFIX']}/audit"
            },
            'documentation': '/docs'  # Swagger à ajouter
        })
    
    # ============================================
    # ENREGISTREMENT DES BLUEPRINTS
    # ============================================
    
    api_prefix = app.config['API_PREFIX']
    
    app.register_blueprint(health_bp, url_prefix=f"{api_prefix}")
    app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(facial_bp, url_prefix=f"{api_prefix}/facial")
    app.register_blueprint(users_bp, url_prefix=f"{api_prefix}/users")
    app.register_blueprint(logs_bp, url_prefix=f"{api_prefix}/logs")
    app.register_blueprint(alerts_bp, url_prefix=f"{api_prefix}/alerts")
    app.register_blueprint(dashboard_bp, url_prefix=f"{api_prefix}/dashboard")
    app.register_blueprint(biometric_bp, url_prefix=f"{api_prefix}/biometric")
    app.register_blueprint(access_bp, url_prefix=f"{api_prefix}/access")
    app.register_blueprint(audit_bp, url_prefix=f"{api_prefix}/audit")
    
    app.logger.info(f"✅ Application BioAccess Secure démarrée en mode {config_name}")
    
    return app

def cache_health_check():
    """Vérifie la connexion Redis"""
    try:
        from core.cache import cache
        cache.set('health_check', 'ok', ex=5)
        return cache.get('health_check') == 'ok'
    except:
        return False