"""
Routes d'authentification
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
POST   /api/v1/auth/change-password
POST   /api/v1/auth/forgot-password
POST   /api/v1/auth/reset-password
POST   /api/v1/auth/device-login                    (client desktop uniquement)
POST   /api/v1/auth/biometric                       (client desktop + web)
GET    /api/v1/auth/me
"""

from flask import Blueprint, request, g, current_app, jsonify
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

from core.database import db
from core.security import SecurityManager
from core.errors import AuthenticationError, ValidationError, NotFoundError
from core.logger import log_audit
from api.middlewares.auth_middleware import token_required, optional_token
from api.middlewares.rate_limiter import login_limiter, sensitive_limiter

from models.user import User, UserSession, LoginLog
from models.access_point import PosteTravail
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
        'user': user.getInfos()
    }

# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/auth/device-login   (client desktop — authentification par device)
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/device-login', methods=['POST'])
def device_login():
    """
    Authentifie un client desktop. Accepte:
      - device_id   (UUID PosteTravail -- backward compat)
      - employee_id (cle affichee dans l'admin, ex: 2421434JTKO)
    Retourne un JWT valide 24h.
    """
    data = request.get_json(silent=True) or {}
    device_id   = data.get('device_id',   '').strip()
    employee_id = data.get('employee_id', '').strip()

    if not device_id and not employee_id:
        raise ValidationError("device_id ou employee_id requis")

    try:
        user  = None
        poste = None

        # Resolution par device_id (UUID PosteTravail)
        if device_id:
            poste = db.session.get(PosteTravail, device_id)
            if poste:
                if not poste.employe_id:
                    log_audit('device_login_failed', None, request.remote_addr,
                             {'device_id': device_id, 'reason': 'device_not_linked'})
                    raise AuthenticationError(
                        "Appareil non encore associe a un employe — enrolement requis.")
                user = db.session.get(User, poste.employe_id)
                if not user:
                    log_audit('device_login_failed', poste.employe_id, request.remote_addr,
                             {'device_id': device_id, 'reason': 'user_not_found'})
                    raise AuthenticationError("Utilisateur introuvable. Contactez l'administrateur.")

        # Resolution par employee_id (cle auth desktop affichee dans l'admin)
        if not user and employee_id:
            user = User.query.filter_by(employee_id=employee_id).first()
            if user:
                poste = PosteTravail.query.filter_by(employe_id=user.id).first()
                logger.info(f"device_login par employee_id={employee_id} -> user={user.id}")

        if not user:
            log_audit('device_login_failed', None, request.remote_addr,
                     {'device_id': device_id, 'employee_id': employee_id, 'reason': 'not_found'})
            raise AuthenticationError(
                "ID non reconnu. Verifiez votre cle d'authentification ou contactez l'administrateur.")

        # Auto-activer si inactif (apres enrolement via admin)
        if not user.is_active:
            user.is_active = True
            logger.info(f"Compte {user.id} auto-active via device-login")

        access_token = SecurityManager.generate_jwt_token(
            user.id, user.role, timedelta(hours=24)
        )
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = request.remote_addr
        db.session.commit()

        log_audit('device_login_success', user.id, request.remote_addr,
                 {'device_id': device_id or (poste.id if poste else None),
                  'employee_id': user.employee_id})

        return {
            'access_token':  access_token,
            'token_type':    'bearer',
            'expires_in':    86400,
            'user_id':       user.id,
            'user_email':    user.email,
            'user_name':     user.full_name,
            'employee_id':   user.employee_id,
            'device_id':     poste.id if poste else None,
            'message':       'Connexion appareil reussie',
        }, 200

    except AuthenticationError:
        raise
    except Exception as e:
        logger.error(f"device_login error: {e}", exc_info=True)
        raise ValidationError(f"Erreur d'authentification: {e}")

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
        logger.debug(f"Reset token généré pour {user.email}")  # token non logué volontairement
    
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
    return jsonify(g.user.getInfos())


@auth_bp.route('/me', methods=['PUT'])
@token_required
def update_current_user():
    """Mettre à jour les informations du profil (nom, prenom, telephone)."""
    data = request.get_json(silent=True) or {}
    user = g.user
    allowed = {'nom', 'prenom', 'telephone'}
    changed = False
    for field in allowed:
        val = data.get(field)
        if val is not None:
            setattr(user, field, str(val).strip())
            changed = True
    if not changed:
        return jsonify({'success': False, 'error': 'Aucun champ modifiable fourni'}), 400
    try:
        user.date_modification = datetime.utcnow()
        db.session.commit()
        log_audit('profile_update', user.id, request.remote_addr, {'fields': list(allowed & set(data.keys()))})
        return jsonify({'success': True, 'message': 'Profil mis à jour', 'user': user.getInfos()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"PUT /me: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/twofa/toggle', methods=['POST'])
@token_required
def toggle_twofa():
    """Active ou désactive la double authentification pour l'utilisateur connecté."""
    user = g.user
    try:
        user.twofa_enabled = not user.twofa_enabled
        db.session.commit()
        state = 'activée' if user.twofa_enabled else 'désactivée'
        log_audit('twofa_toggle', user.id, request.remote_addr, {'enabled': user.twofa_enabled})
        return jsonify({
            'success': True,
            'twofa_enabled': user.twofa_enabled,
            'message': f"Double authentification {state}",
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"twofa toggle: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/my-actions', methods=['GET'])
@token_required
def my_actions():
    """Retourne les 10 dernières actions de l'utilisateur connecté."""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        from models.log import LogAcces
        logs = (
            LogAcces.query
            .filter(LogAcces.utilisateur_id == g.user_id)
            .order_by(LogAcces.date_heure.desc())
            .limit(limit)
            .all()
        )
        actions = [{
            'date':        log.date_heure.isoformat() if log.date_heure else None,
            'action':      log.type_acces or '—',
            'statut':      log.statut or '—',
            'ip':          log.adresse_ip or '—',
            'resource':    log.resource or '',
            'details':     log.details or {},
        } for log in logs]
        return jsonify({'success': True, 'actions': actions, 'count': len(actions)})
    except Exception as e:
        logger.error(f"my-actions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# BIOMETRIC AUTHENTICATION ENDPOINTS
# ============================================

@auth_bp.route('/biometric/authenticate', methods=['POST'])
def biometric_authenticate():
    """Authenticate user with facial recognition"""
    data = request.get_json() or {}
    image_base64 = data.get('image_base64')
    auth_type = data.get('auth_type', 'web')
    is_admin = data.get('is_admin', False)
    
    if not image_base64:
        raise ValidationError("Image biométrique requise")
    
    try:
        from services.biometric_authentication_service import BiometricAuthenticationService
        service = BiometricAuthenticationService()
        
        result = service.authenticate_by_face(image_base64, auth_type, is_admin)

        # authenticate_by_face retourne un dataclass AuthenticationResult
        success = result.success if hasattr(result, 'success') else result.get('success', False)

        if success:
            user_id = result.user_id if hasattr(result, 'user_id') else result.get('user_id')
            user = User.query.get(user_id)
            access_token = SecurityManager.generate_jwt_token(
                user.id,
                user.role,
                timedelta(hours=24)
            )

            log_audit('biometric_auth_success', user.id, request.remote_addr, {'auth_type': auth_type})

            return {
                'success': True,
                'access_token': access_token,
                'user_id': user.id,
                'user_email': user.email,
                'user_name': user.full_name,
                'message': 'Authentification réussie'
            }, 200
        else:
            reason = (result.error if hasattr(result, 'error') else result.get('reason', ''))
            log_audit('biometric_auth_failed', None, request.remote_addr, {'reason': reason})
            return {
                'success': False,
                'message': reason or 'Authentification échouée'
            }, 401
            
    except Exception as e:
        logging.error(f"Biometric auth error: {str(e)}")
        raise ValidationError(f"Erreur authentification: {str(e)}")

@auth_bp.route('/send-verification-code', methods=['POST'])
def send_verification_code():
    """Send 6-digit verification code to user email"""
    data = request.get_json() or {}
    email = data.get('email', '').lower().strip()
    auth_type = data.get('auth_type', 'web')
    
    if not email or '@' not in email:
        raise ValidationError("Email invalide")
    
    try:
        from services.email_service import EmailService
        from models.biometric import PhraseAleatoire
        import random
        import string
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            # Still return success to prevent email enumeration
            return {'success': True, 'message': 'Code d\'authentification envoyé'}, 200
        
        # Generate 6-digit code
        code = ''.join(random.choices(string.digits, k=6))
        
        # Store code in temporary model
        phrase = PhraseAleatoire(
            email=email,
            phrase=code,
            expires_at=datetime.utcnow() + timedelta(minutes=15)
        )
        db.session.add(phrase)
        db.session.commit()
        
        # Send email
        email_service = EmailService()
        email_service.send_auth_code(email, code)
        
        log_audit('verification_code_sent', user.id if user else None, request.remote_addr, {'auth_type': auth_type})
        
        return {
            'success': True,
            'message': 'Code d\'authentification envoyé à votre email'
        }, 200
        
    except Exception as e:
        logging.error(f"Send verification code error: {str(e)}")
        return {'success': False, 'message': 'Erreur lors de l\'envoi du code'}, 500

@auth_bp.route('/verify-code', methods=['POST'])
def verify_code():
    """Verify the 6-digit verification code"""
    data = request.get_json() or {}
    email = data.get('email', '').lower().strip()
    code = data.get('code', '').strip()
    auth_type = data.get('auth_type', 'web')
    
    if not email or not code:
        raise ValidationError("Email et code requis")
    
    if len(code) != 6 or not code.isdigit():
        raise ValidationError("Code invalide")
    
    try:
        from models.biometric import PhraseAleatoire
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user:
            log_audit('verification_failed', None, request.remote_addr, {'reason': 'user_not_found'})
            raise AuthenticationError("Utilisateur non trouvé")
        
        # Verify code
        phrase = PhraseAleatoire.query.filter_by(
            email=email,
            phrase=code
        ).first()
        
        if not phrase:
            log_audit('verification_failed', user.id, request.remote_addr, {'reason': 'invalid_code'})
            raise AuthenticationError("Code invalide ou expiré")
        
        if phrase.expires_at < datetime.utcnow():
            db.session.delete(phrase)
            db.session.commit()
            log_audit('verification_failed', user.id, request.remote_addr, {'reason': 'code_expired'})
            raise AuthenticationError("Code expiré")
        
        # Code is valid - generate token
        access_token = SecurityManager.generate_jwt_token(
            user.id,
            user.role,
            timedelta(hours=24)
        )
        
        # Clean up code
        db.session.delete(phrase)
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = request.remote_addr
        db.session.commit()
        
        log_audit('verification_success', user.id, request.remote_addr, {'auth_type': auth_type})
        
        return {
            'success': True,
            'token': access_token,
            'user_id': user.id,
            'user_email': user.email,
            'user_name': user.full_name,
            'message': 'Authentification réussie'
        }, 200

    except AuthenticationError:
        raise
    except Exception as e:
        logging.error(f"Verify code error: {str(e)}")
        raise ValidationError(f"Erreur vérification: {str(e)}")

# ============================================
# GOOGLE OAUTH ENDPOINT
# ============================================

@auth_bp.route('/google', methods=['POST'])
def google_auth():
    """Google OAuth authentication endpoint"""
    try:
        # Récupérer et valider les données
        try:
            data = request.get_json()
            if not data:
                return {'success': False, 'error': 'Requête vide'}, 400
        except Exception as e:
            logging.error(f"Erreur parsing JSON: {str(e)}")
            return {'success': False, 'error': f'Erreur format JSON: {str(e)}'}, 400
        
        credential = data.get('credential')
        if not credential:
            return {'success': False, 'error': 'Credential Google requise'}, 400
        
        # Vérifier qu'on a le Client ID configuré
        google_client_id = current_app.config.get('GOOGLE_CLIENT_ID')
        if not google_client_id or google_client_id.startswith('VOTRE'):
            logging.error("GOOGLE_CLIENT_ID non configuré ou placeholder")
            return {'success': False, 'error': 'Authentification Google non configurée'}, 500
        
        # Importer les modules Google Auth
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests
        except ImportError as e:
            logging.error(f"Modules Google Auth manquants: {str(e)}")
            return {'success': False, 'error': 'Modules OAuth Google manquants'}, 500
        
        # Vérifier le token Google
        try:
            idinfo = id_token.verify_oauth2_token(
                credential,
                google_requests.Request(),
                google_client_id
            )
            logging.info(f"Token Google vérifié pour: {idinfo.get('email')}")
        except Exception as e:
            logging.error(f"Vérification token Google échouée: {str(e)}")
            return {'success': False, 'error': f'Token Google invalide: {str(e)}'}, 401
        
        # Extraire les informations
        email = idinfo.get('email')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        google_id = idinfo.get('sub')
        
        if not email:
            return {'success': False, 'error': 'Email Google manquant'}, 400
        
        # Chercher ou créer l'utilisateur
        user = User.query.filter_by(email=email.lower()).first()
        
        if not user:
            logging.warning(f"Tentative Google OAuth avec email inconnu: {email}")
            return {'success': False, 'error': 'Compte non trouvé. Contactez votre administrateur.'}, 403
        
        if not user.is_active:
            return {'success': False, 'error': 'Compte désactivé'}, 403
        
        # Créer les tokens JWT
        try:
            access_token = SecurityManager.generate_jwt_token(
                user.id,
                user.role,
                timedelta(hours=24)
            )
            
            refresh_token = SecurityManager.generate_jwt_token(
                user.id,
                user.role,
                timedelta(days=30)
            )
        except Exception as e:
            logging.error(f"Erreur génération token: {str(e)}")
            return {'success': False, 'error': f'Erreur génération token: {str(e)}'}, 500
        
        # Enregistrer la session
        try:
            user_session = UserSession(
                user_id=user.id,
                session_token=access_token,
                refresh_token=refresh_token,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
            db.session.add(user_session)
            
            user.last_login_at = datetime.utcnow()
            user.last_login_ip = request.remote_addr
            db.session.commit()
            
            log_audit('login_google', user.id, request.remote_addr, {'email': email})
        except Exception as e:
            db.session.rollback()
            logging.error(f"Erreur session: {str(e)}")
            return {'success': False, 'error': f'Erreur session: {str(e)}'}, 500
        
        return {
            'success': True,
            'token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.prenom,
                'last_name': user.nom,
                'role': user.role
            },
            'message': 'Authentification Google réussie'
        }, 200
        
    except Exception as e:
        logging.error(f"Erreur Google auth non gérée: {str(e)}")
        return {'success': False, 'error': f'Erreur serveur: {str(e)}'}, 500


# ============================================================
# VOICE CHALLENGE — phrase aléatoire pour enrôlement vocal
# ============================================================

_FALLBACK_PHRASES = [
    "Ma voix est mon passeport, vérifiez moi s'il vous plaît",
    "L'accès biométrique garantit ma sécurité au quotidien",
    "Je confirme mon identité par reconnaissance vocale",
    "La sécurité de mes données est ma priorité absolue",
    "Mon empreinte vocale est unique et personnelle",
    "BioAccess Secure protège l'accès à nos installations",
    "Je valide mon entrée par authentification biométrique",
    "La reconnaissance vocale est une technologie fiable",
    "Mon identité est protégée par des systèmes avancés",
    "J'autorise l'accès grâce à ma voix authentique",
    "Le système vérifie mon identité en temps réel",
    "L'authentification forte garantit la sécurité des accès",
    "Je suis un utilisateur autorisé de ce système sécurisé",
    "Ma voix unique permet de m'identifier avec précision",
    "BioAccess vérifie mon identité de manière sécurisée",
    "L'accès sécurisé passe par la reconnaissance biométrique",
    "Je confirme que je suis bien le titulaire de ce compte",
    "Mon profil vocal est enregistré dans le système sécurisé",
    "La vérification vocale assure l'intégrité des accès",
    "Je m'identifie formellement auprès du système de contrôle",
]

@auth_bp.route('/voice/challenge', methods=['GET'])
def voice_challenge():
    """Retourne une phrase aléatoire pour l'enrôlement ou l'auth vocale (public)"""
    try:
        from models.biometric import PhraseAleatoire
        import random

        phrase_obj = PhraseAleatoire.getRandom()
        if phrase_obj:
            return jsonify({
                'success': True,
                'phrase_id': phrase_obj.id,
                'phrase': phrase_obj.texte,
                'instruction': 'Lisez cette phrase à voix haute et clairement'
            }), 200

        # Table vide — seed de 20 phrases puis retourner une
        for texte in _FALLBACK_PHRASES:
            existing = PhraseAleatoire.query.filter_by(texte=texte, user_id=None).first()
            if not existing:
                p = PhraseAleatoire(texte=texte, langue='fr')
                db.session.add(p)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        phrase_obj = PhraseAleatoire.getRandom()
        if phrase_obj:
            return jsonify({
                'success': True,
                'phrase_id': phrase_obj.id,
                'phrase': phrase_obj.texte,
                'instruction': 'Lisez cette phrase à voix haute et clairement'
            }), 200

        # Ultime fallback sans DB
        text = random.choice(_FALLBACK_PHRASES)
        return jsonify({
            'success': True,
            'phrase_id': 'fallback',
            'phrase': text,
            'instruction': 'Lisez cette phrase à voix haute et clairement'
        }), 200

    except Exception as e:
        logging.error(f"Voice challenge error: {str(e)}")
        import random
        text = random.choice(_FALLBACK_PHRASES)
        return jsonify({
            'success': True,
            'phrase_id': 'fallback',
            'phrase': text,
            'instruction': 'Lisez cette phrase à voix haute et clairement'
        }), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/auth/device-uninstall
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/device-uninstall', methods=['POST'])
def device_uninstall():
    """
    Notifie le backend lors de la désinstallation du client desktop.
    Requiert une authentification par mot de passe.
    Body: {device_id, password, reason?}
    """
    from models.log import Alerte

    data = request.get_json(silent=True) or {}
    device_id = data.get('device_id', '').strip()
    password  = data.get('password', '').strip()
    reason    = data.get('reason', 'Désinstallation manuelle')

    if not device_id:
        raise ValidationError("device_id requis")
    if not password:
        raise ValidationError("Authentification requise pour désinstaller (mot de passe)")

    try:
        poste = db.session.get(PosteTravail, device_id)
        if not poste or not poste.employe_id:
            raise AuthenticationError("Appareil non reconnu")

        user = db.session.get(User, poste.employe_id)
        if not user:
            raise AuthenticationError("Utilisateur introuvable")

        if not user.check_password(password):
            log_audit('uninstall_auth_failed', user.id, request.remote_addr,
                     {'device_id': device_id})
            raise AuthenticationError("Mot de passe incorrect")

        # Créer l'alerte d'audit
        alerte = Alerte(
            type='securite',
            gravite='haute',
            message=f"Désinstallation client desktop — {user.prenom} {user.nom} ({user.email})",
            titre='Désinstallation détectée',
            description=(
                f"L'employé {user.prenom} {user.nom} a désinstallé le client desktop.\n"
                f"IP: {request.remote_addr}\n"
                f"Poste: {poste.nom}\n"
                f"Raison: {reason}"
            ),
            utilisateur_id=user.id,
            statut='Non traitée',
            priorite='Haute',
            resource=f"poste-{poste.id[:8]}",
        )
        db.session.add(alerte)

        # Désactiver le poste (soft delete)
        poste.statut = 'inactif'
        db.session.commit()

        log_audit('device_uninstall', user.id, request.remote_addr,
                 {'device_id': device_id, 'reason': reason})

        return jsonify({
            'success': True,
            'message': "Désinstallation enregistrée. L'administrateur a été notifié."
        }), 200

    except (AuthenticationError, ValidationError):
        raise
    except Exception as e:
        db.session.rollback()
        logger.error(f"device_uninstall error: {e}", exc_info=True)
        raise ValidationError(f"Erreur: {e}")