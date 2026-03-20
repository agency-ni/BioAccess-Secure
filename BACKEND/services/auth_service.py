"""
Service d'authentification - Logique métier
"""

from models.user import User, UserSession
from models.log import LogAcces
from core.security import SecurityManager
from core.database import db
from core.cache import Cache
from flask import request, g
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AuthService:
    """Service gérant l'authentification"""
    
    @staticmethod
    def authenticate(email, password, ip_address, user_agent, remember=False):
        """
        Authentifie un utilisateur
        Retourne (user, token, refresh_token, error)
        """
        # Vérifier rate limiting
        rate_key = f"rate:login:{ip_address}"
        attempts = Cache.get(rate_key)
        if attempts and int(attempts) >= 5:
            return None, None, None, "Trop de tentatives. Réessayez dans 15 minutes."
        
        # Incrémenter compteur
        Cache.incr(rate_key)
        Cache.expire(rate_key, 900)  # 15 minutes
        
        # Rechercher utilisateur
        user = User.query.filter_by(email=email.lower()).first()
        
        # Journaliser tentative
        log = LogAcces(
            type_acces='auth',
            statut='echec',
            adresse_ip=ip_address,
            user_agent=user_agent,
            details={'email': email}
        )
        
        if not user:
            log.raison_echec = "Utilisateur inexistant"
            log.enregistrer()
            return None, None, None, "Email ou mot de passe incorrect"
        
        # Vérifier si compte verrouillé
        if user.is_locked():
            log.raison_echec = "Compte verrouillé"
            log.utilisateur_id = user.id
            log.enregistrer()
            return None, None, None, "Compte temporairement verrouillé"
        
        # Vérifier mot de passe
        is_valid, new_hash = SecurityManager.check_password_and_rehash(password, user.password_hash)
        
        if not is_valid:
            user.increment_login_attempts(success=False)
            log.raison_echec = "Mot de passe incorrect"
            log.utilisateur_id = user.id
            log.enregistrer()
            
            # Vérifier si maintenant verrouillé
            if user.is_locked():
                return None, None, None, "Compte temporairement verrouillé"
            
            return None, None, None, "Email ou mot de passe incorrect"
        
        # Mise à jour du hash si nécessaire
        if new_hash:
            user.password_hash = new_hash
        
        # Succès
        user.increment_login_attempts(success=True)
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        
        # Générer tokens
        access_token = SecurityManager.generate_jwt_token(
            user.id, user.role, token_type='access'
        )
        
        refresh_token = None
        if remember:
            refresh_token = SecurityManager.generate_jwt_token(
                user.id, user.role, token_type='refresh'
            )
            
            # Créer session
            session = UserSession(
                user_id=user.id,
                session_token=access_token,
                refresh_token=refresh_token,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(days=30),
                device_fingerprint=AuthService._get_device_fingerprint(request)
            )
            db.session.add(session)
        
        # Log de succès
        log.statut = 'succes'
        log.utilisateur_id = user.id
        log.enregistrer()
        
        db.session.commit()
        
        # Réinitialiser rate limiting
        Cache.delete(rate_key)
        
        return user, access_token, refresh_token, None
    
    @staticmethod
    def refresh_token(refresh_token, ip_address):
        """Rafraîchit un token"""
        payload = SecurityManager.decode_jwt_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            return None, "Token de rafraîchissement invalide"
        
        # Vérifier que la session existe
        session = UserSession.query.filter_by(
            refresh_token=refresh_token,
            is_active=True
        ).first()
        
        if not session:
            return None, "Session invalide"
        
        # Vérifier IP (optionnel)
        if session.ip_address != ip_address:
            # Alerte de sécurité
            from services.alert_service import AlertService
            AlertService.create_alert(
                'securite',
                'moyenne',
                f"Tentative de refresh depuis IP différente: {ip_address}",
                session.user_id
            )
        
        # Générer nouveau token
        user = session.user
        new_token = SecurityManager.generate_jwt_token(
            user.id, user.role, token_type='access'
        )
        
        # Mettre à jour session
        session.last_activity = datetime.utcnow()
        db.session.commit()
        
        return new_token, None
    
    @staticmethod
    def logout(user_id, refresh_token=None):
        """Déconnecte un utilisateur"""
        if refresh_token:
            # Révoquer session spécifique
            session = UserSession.query.filter_by(
                refresh_token=refresh_token,
                user_id=user_id
            ).first()
            if session:
                session.is_active = False
                # Révoquer les tokens
                SecurityManager.revoke_token(session.session_token)
                SecurityManager.revoke_token(refresh_token)
        else:
            # Révoquer toutes les sessions
            sessions = UserSession.query.filter_by(
                user_id=user_id,
                is_active=True
            ).all()
            for session in sessions:
                session.is_active = False
                SecurityManager.revoke_token(session.session_token)
                if session.refresh_token:
                    SecurityManager.revoke_token(session.refresh_token)
        
        db.session.commit()
        return True
    
    @staticmethod
    def _get_device_fingerprint(request):
        """Génère une empreinte du dispositif client"""
        import hashlib
        data = f"{request.user_agent.string}{request.accept_languages}{request.accept_encodings}"
        return hashlib.sha256(data.encode()).hexdigest()