"""
Modèle User pour la base de données
"""

from datetime import datetime
from flask_login import UserMixin
from core.database import db
from core.security import SecurityManager
import uuid

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='employe')  # super_admin, admin, employe
    departement = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    twofa_enabled = db.Column(db.Boolean, default=False)
    twofa_secret = db.Column(db.String(32), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)
    last_login_ip = db.Column(db.String(45), nullable=True)  # IPv6 compatible
    
    # Relations
    sessions = db.relationship('UserSession', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    login_logs = db.relationship('LoginLog', backref='user', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if 'password' in kwargs:
            self.set_password(kwargs['password'])
    
    def set_password(self, password):
        """Hash et stocke le mot de passe"""
        self.password_hash = SecurityManager.hash_password(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return SecurityManager.check_password(password, self.password_hash)
    
    def update_last_login(self, ip):
        self.last_login_at = datetime.utcnow()
        self.last_login_ip = ip
        db.session.commit()
    
    def to_dict(self):
        """Convertit l'utilisateur en dictionnaire (sans données sensibles)"""
        return {
            'id': self.id,
            'email': self.email,
            'nom': self.nom,
            'prenom': self.prenom,
            'role': self.role,
            'departement': self.departement,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'twofa_enabled': self.twofa_enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
    
    @property
    def full_name(self):
        return f"{self.prenom} {self.nom}".strip()
    
    def __repr__(self):
        return f"<User {self.email}>"

class UserSession(db.Model):
    """Sessions actives des utilisateurs"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(256), unique=True, nullable=False)
    refresh_token = db.Column(db.String(256), unique=True, nullable=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'is_active': self.is_active
        }

class LoginLog(db.Model):
    """Journal des tentatives de connexion"""
    __tablename__ = 'login_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    email = db.Column(db.String(120), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    success = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'ip': self.ip_address,
            'success': self.success,
            'timestamp': self.created_at.isoformat()
        }