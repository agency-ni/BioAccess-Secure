"""
API v1 Blueprints
Exporte tous les blueprints APIs v1
"""

from .auth import auth_bp
from .biometric import biometric_bp
from .biometric_enrollment import enrollment_bp
from .admin_biometric import admin_biometric_bp
from .dashboard import dashboard_bp
from .facial_auth import facial_bp
from .health import health_bp

# Import des autres blueprints s'il en existe
try:
    from .users import users_bp
except ImportError:
    users_bp = None

try:
    from .logs import logs_bp
except ImportError:
    logs_bp = None

try:
    from .alerts import alerts_bp
except ImportError:
    alerts_bp = None

try:
    from .access import access_bp
except ImportError:
    access_bp = None

try:
    from .audit import audit_bp
except ImportError:
    audit_bp = None

__all__ = [
    'auth_bp',
    'biometric_bp',
    'enrollment_bp',
    'admin_biometric_bp',
    'dashboard_bp',
    'facial_bp',
    'health_bp',
    'users_bp',
    'logs_bp',
    'alerts_bp',
    'access_bp',
    'audit_bp'
]
