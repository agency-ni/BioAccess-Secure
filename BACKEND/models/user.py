"""
Modèle User pour la base de données
Respecte strictement le diagramme de classes
"""

from datetime import datetime, timedelta
from flask_login import UserMixin
from core.database import db
from core.security import SecurityManager
import uuid
import hashlib
import json

class User(UserMixin, db.Model):
    """
    Modèle Utilisateur (classe parente)
    Correspond à la classe Utilisateur du diagramme
    """
    __tablename__ = 'users'
    
    # Attributs de base (conformes au diagramme)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    departement = db.Column(db.String(50), nullable=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Attributs de sécurité (non visibles dans le diagramme mais essentiels)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='employe')  # super_admin, admin, employe, auditeur
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    twofa_enabled = db.Column(db.Boolean, default=False)
    twofa_secret = db.Column(db.String(32), nullable=True)
    
    # Métadonnées d'audit
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)
    login_count = db.Column(db.Integer, default=0)
    failed_login_count = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    # Relations (conformes au diagramme)
    templates = db.relationship('TemplateBiometrique', backref='utilisateur', lazy='dynamic', cascade='all, delete-orphan')
    phrases = db.relationship('PhraseAleatoire', backref='utilisateur', lazy='dynamic', cascade='all, delete-orphan')
    logs = db.relationship('LogAcces', backref='utilisateur', lazy='dynamic', cascade='all, delete-orphan')
    alertes = db.relationship('Alerte', backref='utilisateur', lazy='dynamic', cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    # Méthodes (conformes au diagramme)
    def getInfos(self):
        """Retourne les informations publiques de l'utilisateur"""
        return {
            'id': self.id,
            'nom': self.nom,
            'prenom': self.prenom,
            'email': self.email,
            'departement': self.departement,
            'role': self.role,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'twofa_enabled': self.twofa_enabled,
            'created_at': self.date_creation.isoformat() if self.date_creation else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
    
    def updateProfil(self, **kwargs):
        """Met à jour le profil de l'utilisateur"""
        for key, value in kwargs.items():
            if hasattr(self, key) and key not in ['id', 'password_hash', 'role', 'date_creation']:
                setattr(self, key, value)
        self.date_modification = datetime.utcnow()
        db.session.commit()
    
    # Méthodes de sécurité
    def set_password(self, password):
        """Hash et stocke le mot de passe"""
        self.password_hash = SecurityManager.hash_password(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return SecurityManager.check_password(password, self.password_hash)
    
    def increment_login_attempts(self, success=False):
        """Incrémente les compteurs de tentative"""
        if success:
            self.login_count += 1
            self.failed_login_count = 0
            self.locked_until = None
        else:
            self.failed_login_count += 1
            if self.failed_login_count >= 5:
                # Verrouiller pendant 15 minutes
                self.locked_until = datetime.utcnow() + timedelta(minutes=15)
    
    def is_locked(self):
        """Vérifie si le compte est verrouillé"""
        return self.locked_until and self.locked_until > datetime.utcnow()
    
    # Propriétés
    @property
    def full_name(self):
        return f"{self.prenom} {self.nom}".strip()
    
    # Méthodes spéciales
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


class Admin(User):
    """
    Modèle Admin (hérite de User)
    Correspond à la classe Admin du diagramme
    """
    __tablename__ = 'admins'
    __mapper_args__ = {
        'polymorphic_identity': 'admin',
        'concrete': True
    }
    
    id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    
    # Attributs spécifiques Admin (conformes au diagramme)
    niveau_habilitation = db.Column(db.String(50), default='standard')  # standard, super
    date_derniere_connexion = db.Column(db.DateTime, nullable=True)
    
    # Relations spécifiques
    configurations = db.relationship('Configuration', backref='admin', lazy='dynamic')
    
    # Méthodes (conformes au diagramme)
    def gererConfiguration(self):
        """Gère la configuration système"""
        pass
    
    def consulterLogs(self):
        """Consulte les logs"""
        from models.log import LogAcces
        return LogAcces.query.order_by(LogAcces.date_heure.desc()).all()
    
    def gererAlertes(self):
        """Gère les alertes"""
        from models.alert import Alerte
        return Alerte.query.filter_by(traitee=False).all()


class Employe(User):
    """
    Modèle Employé (hérite de User)
    Correspond à la classe Employé du diagramme
    """
    __tablename__ = 'employes'
    __mapper_args__ = {
        'polymorphic_identity': 'employe',
        'concrete': True
    }
    
    id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    
    # Attributs spécifiques Employé (conformes au diagramme)
    date_embauche = db.Column(db.Date, nullable=True)
    poste_occupe = db.Column(db.String(100), nullable=True)
    manager_id = db.Column(db.String(36), db.ForeignKey('employes.id'), nullable=True)
    
    # Relations
    poste_travail = db.relationship('PosteTravail', backref='employe', uselist=False)
    tentatives = db.relationship('TentativeAuth', backref='employe', lazy='dynamic')
    
    # Méthodes (conformes au diagramme)
    def authentifier(self):
        """Authentifie l'employé"""
        # La logique d'authentification est gérée ailleurs
        return True


class UserSession(db.Model):
    """Sessions actives des utilisateurs"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(512), unique=True, nullable=False)
    refresh_token = db.Column(db.String(512), unique=True, nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(256), nullable=True)
    device_fingerprint = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_active': self.is_active
        }


class LoginLog(db.Model):
    """
    Modèle pour enregistrer les tentatives de connexion
    Utilisé pour l'audit et la détection d'anomalies
    """
    __tablename__ = 'login_logs'
    
    # Attributs
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(256), nullable=True)
    success = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Foreign key
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Relations
    user = db.relationship('User', backref=db.backref('login_logs', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Métadonnées
    failure_reason = db.Column(db.String(255), nullable=True)
    method = db.Column(db.String(50), default='password')  # password, face, voice, google_oauth
    
    def to_dict(self):
        """Retourne un dictionnaire de la tentative"""
        return {
            'id': self.id,
            'email': self.email,
            'ip_address': self.ip_address,
            'success': self.success,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'failure_reason': self.failure_reason,
            'method': self.method
        }
    
    def __repr__(self):
        status = '✓' if self.success else '✗'
        return f"<LoginLog {self.email} {status} {self.timestamp}>"