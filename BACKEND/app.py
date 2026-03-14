#!/usr/bin/env python3
"""
BioAccess Secure - Application principale Flask
Version 2.0 - Production Ready
"""

import os
import logging
from flask import Flask, jsonify
from flask_cors import CORS

# Configuration
from config import ConfigClass
from core.database import init_db, health_check
from core.logger import setup_logger
from core.errors import register_error_handlers
from api.middlewares.rate_limiter import init_rate_limiter, limiter

# Blueprints API v1
from api.v1.auth import auth_bp
from api.v1.dashboard import dashboard_bp
from api.v1.users import users_bp
from api.v1.logs import logs_bp
from api.v1.alerts import alerts_bp
from api.v1.config import config_bp
from api.v1.audit import audit_bp

def create_app(config_class=ConfigClass):
    """Factory pattern pour créer l'application Flask"""
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialisation des extensions
    CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True)
    init_db(app)
    init_rate_limiter(app)
    
    # Logger
    logger, audit_logger = setup_logger(app)
    app.logger = logger
    app.audit_logger = audit_logger
    
    # Gestionnaires d'erreurs
    register_error_handlers(app)
    
    # Enregistrement des blueprints
    api_prefix = app.config['API_PREFIX']
    
    app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(dashboard_bp, url_prefix=f"{api_prefix}/dashboard")
    app.register_blueprint(users_bp, url_prefix=f"{api_prefix}/users")
    app.register_blueprint(logs_bp, url_prefix=f"{api_prefix}/logs")
    app.register_blueprint(alerts_bp, url_prefix=f"{api_prefix}/alerts")
    app.register_blueprint(config_bp, url_prefix=f"{api_prefix}/config")
    app.register_blueprint(audit_bp, url_prefix=f"{api_prefix}/audit")
    
    # Route de santé
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected' if health_check() else 'disconnected',
            'version': app.config['API_VERSION']
        })
    
    # Route d'accueil
    @app.route('/')
    def index():
        return jsonify({
            'name': 'BioAccess Secure API',
            'version': app.config['API_VERSION'],
            'status': 'operational',
            'documentation': '/docs'  # Si tu ajoutes Swagger
        })
    
    app.logger.info("✅ Application BioAccess Secure démarrée")
    
    return app

from datetime import datetime

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])