"""
Sentry Monitoring et Alerting Configuration
Intégration de monitoring, logging et alerting pour production

Les imports sentry_sdk sont intentionnellement à l'intérieur de init_sentry()
afin de ne pas ralentir le démarrage en dev (SENTRY_DSN non configuré → import jamais exécuté).
"""

import os
import logging

logger = logging.getLogger(__name__)


class SentryConfig:
    """Configuration Sentry pour monitoring production"""

    @staticmethod
    def init_sentry(app):
        """Initialise Sentry pour l'application (no-op si SENTRY_DSN absent)"""

        sentry_dsn = os.environ.get('SENTRY_DSN')
        environment = os.environ.get('FLASK_ENV', 'development')

        if not sentry_dsn:
            if environment == 'production':
                app.logger.warning("SENTRY_DSN non configuré en production")
            return  # ← sort ici en dev : sentry_sdk n'est jamais importé

        # Import seulement si Sentry est réellement utilisé
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        try:
            from sentry_sdk.integrations.sqlalchemy import SqlAlchemyIntegration
        except ImportError:
            SqlAlchemyIntegration = None
        try:
            from sentry_sdk.integrations.redis import RedisIntegration
        except ImportError:
            RedisIntegration = None
        try:
            from sentry_sdk.integrations.celery import CeleryIntegration
        except (ImportError, Exception):
            CeleryIntegration = None

        integrations = [
            FlaskIntegration(),
            LoggingIntegration(level=20, event_level=40),
        ]
        if SqlAlchemyIntegration:
            integrations.append(SqlAlchemyIntegration())
        if RedisIntegration:
            integrations.append(RedisIntegration())
        if CeleryIntegration:
            integrations.append(CeleryIntegration())

        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=integrations,
            environment=environment,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            before_send=SentryConfig.before_send,
            before_breadcrumb=SentryConfig.before_breadcrumb,
            release=os.environ.get('APP_VERSION', '2.0.0'),
            server_name=os.environ.get('SERVER_NAME', 'bioaccess-backend'),
            attach_stacktrace=True,
            with_locals=environment != 'production',
            include_local_variables=False,
            ignore_errors=[
                'flask.wrappers.HTTPException',
                'werkzeug.exceptions.HTTPException',
            ],
        )

        app.logger.info(f"✅ Sentry initialized (env: {environment})")

    # ── Helpers utilisables même sans Sentry actif (no-op si sentry_sdk absent) ──

    @staticmethod
    def before_send(event, hint):
        if 'status_code' in event.get('request', {}) and \
           event['request']['status_code'] in (404, 401):
            return None
        if 'exc_info' in hint:
            exc_info = hint['exc_info']
            if exc_info and len(exc_info) > 1:
                exception = exc_info[1]
                if hasattr(exception, 'user_id'):
                    event.setdefault('user', {})['id'] = str(exception.user_id)
        return event

    @staticmethod
    def before_breadcrumb(crumb, hint):
        if crumb['category'] == 'query' and 'SELECT' in crumb.get('data', {}).get('query', ''):
            return None
        if crumb['category'] == 'http' and crumb.get('data', {}).get('status_code') == 200:
            return None
        return crumb

    @staticmethod
    def _sdk():
        """Retourne sentry_sdk si disponible, sinon None."""
        try:
            import sentry_sdk as _sdk
            return _sdk
        except ImportError:
            return None

    @staticmethod
    def capture_exception(exception, level='error', **kwargs):
        sdk = SentryConfig._sdk()
        if sdk:
            sdk.capture_exception(exception, level=level)

    @staticmethod
    def capture_message(message, level='info', **kwargs):
        sdk = SentryConfig._sdk()
        if sdk:
            sdk.capture_message(message, level=level)

    @staticmethod
    def set_user_context(user_id, username=None, email=None):
        sdk = SentryConfig._sdk()
        if sdk:
            sdk.set_user({'id': str(user_id), 'username': username, 'email': email})

    @staticmethod
    def clear_user_context():
        sdk = SentryConfig._sdk()
        if sdk:
            sdk.set_user(None)

    @staticmethod
    def add_breadcrumb(message, category='custom', level='info', **data):
        sdk = SentryConfig._sdk()
        if sdk:
            sdk.add_breadcrumb(message=message, category=category, level=level, data=data)

    @staticmethod
    def set_tag(key, value):
        sdk = SentryConfig._sdk()
        if sdk:
            sdk.set_tag(key, value)

    @staticmethod
    def set_context(name, data):
        sdk = SentryConfig._sdk()
        if sdk:
            sdk.set_context(name, data)


# ── Alerting config (statique, pas de dépendance sentry) ──────────────────────

ALERT_RULES = {
    'biometric_failures': {
        'description': "Taux d'échec biométrique élevé",
        'metric': 'biometric_verify_fail',
        'threshold': '> 15%',
        'window': '5m',
        'severity': 'high',
        'actions': ['notify_team', 'page_oncall'],
    },
    'auth_attacks': {
        'description': "Tentatives d'authentification suspectes",
        'metric': 'auth_failed',
        'threshold': '> 50 in 1m',
        'window': '1m',
        'severity': 'critical',
        'actions': ['notify_security', 'page_oncall', 'block_ip'],
    },
    'database_errors': {
        'description': 'Erreurs base de données',
        'metric': 'database_error',
        'threshold': '> 10 in 5m',
        'window': '5m',
        'severity': 'critical',
        'actions': ['notify_dba', 'page_oncall', 'auto_failover'],
    },
}


class SentryAlerting:
    ALERT_RULES = ALERT_RULES

    @staticmethod
    def get_alert_level(error_type):
        for level, cfg in SentryAlerting.ALERT_RULES.items():
            if error_type in cfg.get('errors', []):
                return level
        return 'low'


class PerformanceMonitoring:
    @staticmethod
    def transaction_start(name):
        sdk = SentryConfig._sdk()
        if sdk:
            from sentry_sdk.tracing import trace
            return trace(name)
        return None

    @staticmethod
    def set_measurement(name, value, unit='none'):
        sdk = SentryConfig._sdk()
        if sdk:
            sdk.get_current_scope().set_measurement(name, value, unit)
