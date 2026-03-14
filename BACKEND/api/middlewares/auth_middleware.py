"""
Middleware d'authentification JWT
"""

from functools import wraps
from flask import request, g
from core.security import SecurityManager
from core.errors import AuthenticationError, AuthorizationError
from models.user import User
import logging

logger = logging.getLogger(__name__)

def get_token_from_header():
    """Extrait le token JWT du header Authorization"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]

def token_required(f):
    """Décorateur : token JWT valide requis"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        
        if not token:
            raise AuthenticationError("Token manquant")
        
        payload = SecurityManager.decode_jwt_token(token)
        if not payload:
            raise AuthenticationError("Token invalide ou expiré")
        
        # Récupérer l'utilisateur
        user = User.query.get(payload.get('user_id'))
        if not user:
            raise AuthenticationError("Utilisateur non trouvé")
        
        if not user.is_active:
            raise AuthenticationError("Compte désactivé")
        
        # Stocker l'utilisateur dans le contexte de requête
        g.user = user
        g.user_id = user.id
        g.user_role = user.role
        g.token_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Décorateur : admin requis"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.user_role not in ['admin', 'super_admin']:
            raise AuthorizationError("Accès réservé aux administrateurs")
        return f(*args, **kwargs)
    
    return decorated

def super_admin_required(f):
    """Décorateur : super admin requis (audit)"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if g.user_role != 'super_admin':
            raise AuthorizationError("Accès réservé aux super administrateurs")
        return f(*args, **kwargs)
    
    return decorated

def optional_token(f):
    """Décorateur : token optionnel"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_header()
        if token:
            payload = SecurityManager.decode_jwt_token(token)
            if payload:
                user = User.query.get(payload.get('user_id'))
                if user and user.is_active:
                    g.user = user
                    g.user_id = user.id
        return f(*args, **kwargs)
    
    return decorated