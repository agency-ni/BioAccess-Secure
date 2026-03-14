"""
Routes d'authentification
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
POST   /api/v1/auth/change-password
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
GET    /api/v1/auth/me
"""

from flask import Blueprint, request, g
from datetime import datetime, timedelta
import uuid

from core.database import db
from core.security import SecurityManager
from core.errors import AuthenticationError, ValidationError, NotFoundError
from core.logger import log_audit
from api.middlewares.auth_middleware import token_required, optional_token
from api.middlewares.rate_limiter import login_limiter, sensitive_limiter

from models.user import User, UserSession, LoginLog
from schemas.auth import (
    LoginRequest, ChangePasswordRequest,
    ForgotPasswordRequest, ResetPasswordRequest
)

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['POST'])
@login_limiter
def login():
    """Authentification utilisateur"""
    data = request.get_json()
    
    try:
        login_data = LoginRequest(**data)
    except Exception as e:
        raise ValidationError(str(e))
    
    # Rechercher l'utilisateur
    user = User.query.filter_by(email=login_data.email.lower()).first()
    
    # Journaliser la tentative
    log = LoginLog(
        email=login_data.email.lower(),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        success=False
    )
    
    if not user or not user.check_password(login_data.password):
        db.session.add(log)
        db.session.commit()
        raise AuthenticationError("Email ou mot de passe incorrect")
    
    if not user.is_active:
        db.session.add(log)
        db.session.commit()
        raise AuthenticationError("Compte désactivé. Contactez l'administrateur.")
    
    # Succès
    log.success = True
    log.user_id = user.id
    db.session.add(log)
    
    # Créer une session
    session_token = SecurityManager.generate_jwt_token(
        user.id,
        user.role,
        timedelta(hours=1)
    )
    
    refresh_token = None
    if login_data.remember:
        refresh_token = SecurityManager.generate_jwt_token(
            user.id,
            user.role,
            timedelta(days=30)
        )
        
        user_session = UserSession(
            user_id=user.id,
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        db.session.add(user_session)
    
    user.last_login_at = datetime.utcnow()
    user.last_login_ip = request.remote_addr
    db.session.commit()
    
    # Log d'audit
    log_audit('login', user.id, request.remote_addr, {'method': 'password'})
    
    return {
        'access_token': session_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer',
        'expires_in': 3600,
        'user': user.to_dict()
    }

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Rafraîchir un token JWT"""
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        raise ValidationError("refresh_token requis")
    
    payload = SecurityManager.decode_jwt_token(refresh_token)
    if not payload:
        raise AuthenticationError("Token de rafraîchissement invalide")
    
    # Vérifier que la session existe
    session = UserSession.query.filter_by(
        refresh_token=refresh_token,
        is_active=True
    ).first()
    
    if not session:
        raise AuthenticationError("Session invalide ou expirée")
    
    # Générer nouveau token
    new_token = SecurityManager.generate_jwt_token(
        payload['user_id'],
        payload['role'],
        timedelta(hours=1)
    )
    
    return {
        'access_token': new_token,
        'token_type': 'bearer',
        'expires_in': 3600
    }

@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """Déconnexion utilisateur"""
    data = request.get_json() or {}
    refresh_token = data.get('refresh_token')
    
    if refresh_token:
        # Invalider la session spécifique
        UserSession.query.filter_by(
            refresh_token=refresh_token,
            user_id=g.user_id
        ).update({'is_active': False})
    else:
        # Invalider toutes les sessions
        UserSession.query.filter_by(
            user_id=g.user_id,
            is_active=True
        ).update({'is_active': False})
    
    db.session.commit()
    
    log_audit('logout', g.user_id, request.remote_addr, {})
    
    return {'message': 'Déconnexion réussie'}

@auth_bp.route('/change-password', methods=['POST'])
@token_required
@sensitive_limiter
def change_password():
    """Changer le mot de passe"""
    data = request.get_json()
    
    try:
        change_data = ChangePasswordRequest(**data)
    except Exception as e:
        raise ValidationError(str(e))
    
    user = g.user
    
    if not user.check_password(change_data.old_password):
        raise AuthenticationError("Ancien mot de passe incorrect")
    
    user.set_password(change_data.new_password)
    db.session.commit()
    
    # Invalider toutes les sessions (sauf celle-ci)
    UserSession.query.filter_by(
        user_id=user.id,
        is_active=True
    ).update({'is_active': False})
    
    log_audit('change_password', user.id, request.remote_addr, {})
    
    return {'message': 'Mot de passe modifié avec succès'}

@auth_bp.route('/forgot-password', methods=['POST'])
@login_limiter
def forgot_password():
    """Demander la réinitialisation du mot de passe"""
    data = request.get_json()
    
    try:
        forgot_data = ForgotPasswordRequest(**data)
    except Exception as e:
        raise ValidationError(str(e))
    
    user = User.query.filter_by(email=forgot_data.email.lower()).first()
    
    # Toujours répondre la même chose pour ne pas révéler l'existence du compte
    if user:
        # En production, envoyer un email avec un token
        reset_token = SecurityManager.generate_jwt_token(
            user.id,
            user.role,
            timedelta(hours=1)
        )
        print(f"Reset token pour {user.email}: {reset_token}")  # En dev seulement
    
    return {'message': 'Si l\'email existe, un lien de réinitialisation a été envoyé'}

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """Réinitialiser le mot de passe avec token"""
    data = request.get_json()
    
    try:
        reset_data = ResetPasswordRequest(**data)
    except Exception as e:
        raise ValidationError(str(e))
    
    payload = SecurityManager.decode_jwt_token(reset_data.token)
    if not payload:
        raise AuthenticationError("Token invalide ou expiré")
    
    user = User.query.get(payload['user_id'])
    if not user:
        raise NotFoundError("Utilisateur")
    
    user.set_password(reset_data.new_password)
    db.session.commit()
    
    # Invalider toutes les sessions
    UserSession.query.filter_by(user_id=user.id).update({'is_active': False})
    
    log_audit('reset_password', user.id, request.remote_addr, {})
    
    return {'message': 'Mot de passe réinitialisé avec succès'}

@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user():
    """Récupérer les informations de l'utilisateur connecté"""
    return g.user.to_dict()