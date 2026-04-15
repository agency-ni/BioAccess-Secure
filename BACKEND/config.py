"""
Configuration de l'application BioAccess Secure
Gestion des environnements (dev, test, prod)
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de base"""
    
    # Flask
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    FLASK_APP = os.environ.get('FLASK_APP', 'run.py')
    DEBUG = False
    TESTING = False
    
    # SECRET_KEY - CRITIQUE: Doit être défini en production
    if FLASK_ENV == 'production':
        secret = os.environ.get('SECRET_KEY')
        if not secret or secret.startswith('dev-key'):
            raise ValueError(
                '❌ ERREUR CRITIQUE: SECRET_KEY non configurée en production!\n'
                'Définir une clé sécurisée: export SECRET_KEY=<256-bits-hex>'
            )
        SECRET_KEY = secret
    else:
        SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-en-production')
    
    # Base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.environ.get('DATABASE_POOL_SIZE', 10)),
        'max_overflow': int(os.environ.get('DATABASE_MAX_OVERFLOW', 20)),
        'pool_timeout': int(os.environ.get('DATABASE_POOL_TIMEOUT', 30)),
        'pool_recycle': int(os.environ.get('DATABASE_POOL_RECYCLE', 1800)),
        'pool_pre_ping': True,
        'connect_args': {
            'sslmode': os.environ.get('DATABASE_SSL_MODE', 'require'),
            'connect_timeout': 10
        }
    }
    
    # Redis
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_MAX_CONNECTIONS = int(os.environ.get('REDIS_MAX_CONNECTIONS', 50))
    
    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 900))
    JWT_REFRESH_TOKEN_EXPIRES = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 2592000))
    JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS512')
    
    # Bcrypt / Argon2
    BCRYPT_ROUNDS = int(os.environ.get('BCRYPT_ROUNDS', 12))
    PASSWORD_HASH_ALGO = 'argon2'  # Plus sécurisé que bcrypt
    
    # Session
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'True') == 'True'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.environ.get('SESSION_COOKIE_SAMESITE', 'Lax')
    PERMANENT_SESSION_LIFETIME = int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600))
    
    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5500,http://127.0.0.1:5500')
    CORS_ALLOW_CREDENTIALS = os.environ.get('CORS_ALLOW_CREDENTIALS', 'True') == 'True'
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT = os.environ.get('RATE_LIMIT_DEFAULT', '100 per hour')
    RATE_LIMIT_LOGIN = os.environ.get('RATE_LIMIT_LOGIN', '5 per 15 minutes')
    RATE_LIMIT_API = os.environ.get('RATE_LIMIT_API', '1000 per minute')
    RATE_LIMIT_BIOMETRIC = os.environ.get('RATE_LIMIT_BIOMETRIC', '10 per minute')
    RATE_LIMIT_STORAGE_URL = REDIS_URL
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/bioaccess.log')
    AUDIT_LOG_FILE = os.environ.get('AUDIT_LOG_FILE', 'logs/audit.log')
    
    # Uploads
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))  # 10MB
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'jpg,jpeg,png,wav,mp3').split(','))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    
    # API
    API_VERSION = os.environ.get('API_VERSION', 'v1')
    API_PREFIX = f"/api/{API_VERSION}"
    API_KEY_HEADER = os.environ.get('API_KEY_HEADER', 'X-API-Key')
    
    # Sécurité renforcée
    SESSION_COOKIE_SECURE = True  # HTTPS only
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # CSP (Content Security Policy)
    CSP = {
        'default-src': ["'self'"],
        'style-src': ["'self'", "'unsafe-inline'"],
        'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        'img-src': ["'self'", "data:"],
        'font-src': ["'self'"],
        'connect-src': ["'self'"]
    }
    
    # Monitoring
    SENTRY_DSN = os.environ.get('SENTRY_DSN')
    PROMETHEUS_ENABLED = os.environ.get('PROMETHEUS_ENABLED', 'True') == 'True'
    
    # Google OAuth
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
    GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/api/v1/auth/google/callback')


class DevelopmentConfig(Config):
    """Configuration développement"""
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_pre_ping': True
    }


class TestingConfig(Config):
    """Configuration tests"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Configuration production"""
    DEBUG = False
    TESTING = False
    
    # Sécurité renforcée
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = 'Strict'
    
    # Rate limiting plus strict
    RATE_LIMIT_LOGIN = '3 per 15 minutes'
    RATE_LIMIT_BIOMETRIC = '5 per minute'
    
    # Sentry pour monitoring
    SENTRY_DSN = os.environ.get('SENTRY_DSN')


config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}