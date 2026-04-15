"""
Sentry Monitoring et Alerting Configuration
Intégration de monitoring, logging et alerting pour production
"""

import os
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.tracing import trace


class SentryConfig:
    """Configuration Sentry pour monitoring production"""
    
    @staticmethod
    def init_sentry(app):
        """Initialise Sentry pour l'application"""
        
        sentry_dsn = os.environ.get('SENTRY_DSN')
        environment = os.environ.get('FLASK_ENV', 'development')
        
        if not sentry_dsn and environment == 'production':
            app.logger.warning("SENTRY_DSN non configuré en production")
            return
        
        if sentry_dsn:
            # Intégrations multiples
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[
                    FlaskIntegration(),
                    SqlAlchemyIntegration(),
                    RedisIntegration(),
                    CeleryIntegration(),
                    LoggingIntegration(
                        level=20,  # INFO
                        event_level=40  # ERROR
                    ),
                ],
                environment=environment,
                traces_sample_rate=0.1,  # 10% des transactions (performance monitoring)
                profiles_sample_rate=0.1,  # 10% pour profiling
                
                # Configuration des erreurs
                before_send=SentryConfig.before_send,
                before_breadcrumb=SentryConfig.before_breadcrumb,
                
                # Release tracking
                release=os.environ.get('APP_VERSION', '2.0.0'),
                
                # Server name
                server_name=os.environ.get('SERVER_NAME', 'bioaccess-backend'),
                
                # Attachement de contextes
                attach_stacktrace=True,
                with_locals=environment != 'production',  # Pas de locals en prod pour sécurité
                include_local_variables=False,
                
                # Ignorer certains erreurs
                ignore_errors=[
                    'flask.wrappers.HTTPException',
                    'werkzeug.exceptions.HTTPException',
                ],
            )
            
            app.logger.info(f"✅ Sentry initialized (env: {environment})")
    
    @staticmethod
    def before_send(event, hint):
        """Filtre les événements avant envoi à Sentry"""
        
        # Ne pas envoyer les erreurs 404
        if 'status_code' in event.get('request', {}) and \
           event['request']['status_code'] == 404:
            return None
        
        # Ne pas envoyer les erreurs 401 (non-autorisé)
        if 'status_code' in event.get('request', {}) and \
           event['request']['status_code'] == 401:
            return None
        
        # Ajouter du contexte utilisateur si disponible
        if 'exc_info' in hint:
            exc_info = hint['exc_info']
            if exc_info and len(exc_info) > 1:
                exception = exc_info[1]
                if hasattr(exception, 'user_id'):
                    event.setdefault('user', {})['id'] = str(exception.user_id)
        
        return event
    
    @staticmethod
    def before_breadcrumb(crumb, hint):
        """Filtre les breadcrumbs avant envoi"""
        
        # Ignorer les logs SELECT (trop verbeux)
        if crumb['category'] == 'query' and 'SELECT' in crumb.get('data', {}).get('query', ''):
            return None
        
        # Ignorer les requests 200 OK (trop communs)
        if crumb['category'] == 'http' and \
           crumb.get('data', {}).get('status_code') == 200:
            return None
        
        return crumb
    
    @staticmethod
    def capture_exception(exception, level='error', **kwargs):
        """Capture une exception avec contexte"""
        sentry_sdk.capture_exception(exception, level=level)
    
    @staticmethod
    def capture_message(message, level='info', **kwargs):
        """Capture un message"""
        sentry_sdk.capture_message(message, level=level)
    
    @staticmethod
    def set_user_context(user_id, username=None, email=None):
        """Set le contexte utilisateur pour Sentry"""
        sentry_sdk.set_user({
            'id': str(user_id),
            'username': username,
            'email': email,
        })
    
    @staticmethod
    def clear_user_context():
        """Efface le contexte utilisateur"""
        sentry_sdk.set_user(None)
    
    @staticmethod
    def add_breadcrumb(message, category='custom', level='info', **data):
        """Ajoute une breadcrumb (trace d'événement)"""
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data,
        )
    
    @staticmethod
    def set_tag(key, value):
        """Ajoute un tag pour filtrer les erreurs"""
        sentry_sdk.set_tag(key, value)
    
    @staticmethod
    def set_context(name, data):
        """Ajoute un contexte personnalisé"""
        sentry_sdk.set_context(name, data)


class SentryAlerting:
    """Configuration des alertes Sentry"""
    
    # Règles d'alerte
    ALERT_RULES = {
        'critical': {
            'errors': ['DatabaseError', 'ConnectionError', 'AuthenticationError'],
            'threshold': 5,  # 5 erreurs en 5 min
            'severity': 'critical',
            'notify': ['team@bioaccess.local', 'on-call@bioaccess.local']
        },
        'high': {
            'errors': ['BiometricVerificationError', 'ValidationError', 'RateLimitError'],
            'threshold': 10,
            'severity': 'warning',
            'notify': ['ops@bioaccess.local']
        },
        'medium': {
            'errors': ['LogError', 'CacheError', 'TimeoutError'],
            'threshold': 20,
            'severity': 'info',
            'notify': ['monitoring@bioaccess.local']
        }
    }
    
    @staticmethod
    def get_alert_level(error_type):
        """Détermine le niveau d'alerte basé sur le type d'erreur"""
        for level, config in SentryAlerting.ALERT_RULES.items():
            if error_type in config['errors']:
                return level
        return 'low'


class PerformanceMonitoring:
    """Configuration du monitoring de performance"""
    
    @staticmethod
    def transaction_start(name):
        """Démarrer une transaction de monitoring"""
        return trace(name)
    
    @staticmethod
    def set_measurement(name, value, unit='none'):
        """Ajouter une mesure"""
        sentry_sdk.get_current_scope().set_measurement(name, value, unit)


# Alerting avancées
ALERT_RULES = {
    'biometric_failures': {
        'description': 'Taux d\'échec biométrique élevé',
        'metric': 'biometric_verify_fail',
        'threshold': '> 15%',
        'window': '5m',
        'severity': 'high',
        'actions': ['notify_team', 'page_oncall']
    },
    'auth_attacks': {
        'description': 'Tentatives d\'authentification suspectes',
        'metric': 'auth_failed',
        'threshold': '> 50 in 1m',
        'window': '1m',
        'severity': 'critical',
        'actions': ['notify_security', 'page_oncall', 'block_ip']
    },
    'database_errors': {
        'description': 'Erreurs base de données',
        'metric': 'database_error',
        'threshold': '> 10 in 5m',
        'window': '5m',
        'severity': 'critical',
        'actions': ['notify_dba', 'page_oncall', 'auto_failover']
    },
    'cache_failures': {
        'description': 'Défaillance Redis/Cache',
        'metric': 'cache_error',
        'threshold': '> 5 in 1m',
        'window': '1m',
        'severity': 'high',
        'actions': ['notify_infra', 'page_oncall']
    },
    'response_time': {
        'description': 'Temps de réponse élevé',
        'metric': 'response_time',
        'threshold': '> 5000ms',
        'percentile': 'p95',
        'window': '5m',
        'severity': 'medium',
        'actions': ['notify_performance', 'check_resources']
    },
    'ssl_certificate': {
        'description': 'Expiration certificat SSL approchante',
        'metric': 'ssl_expiration_days',
        'threshold': '< 30 days',
        'window': 'daily',
        'severity': 'high',
        'actions': ['notify_security', 'create_ticket']
    }
}
