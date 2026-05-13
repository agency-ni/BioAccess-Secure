"""
Modèles biométriques (conformes au diagramme de classes)
- TemplateBiometrique
- PhraseAleatoire
- TentativeAuth
"""

from datetime import datetime
from core.database import db
from core.security import SecurityManager
import uuid
import json
import hashlib

class TemplateBiometrique(db.Model):
    """
    Modèle TemplateBiometrique
    Conforme au diagramme de classes
    """
    __tablename__ = 'templates_biometriques'
    
    # Attributs (conformes au diagramme)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type_biometrique = db.Column(db.String(50), nullable=False)  # FACE, VOICE
    template_data = db.Column(db.JSON, nullable=False)  # Template en JSON array
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_derniere_utilisation = db.Column(db.DateTime, nullable=True)
    label = db.Column(db.String(255), nullable=True)
    
    # Clé étrangère
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
    # Métadonnées de sécurité
    quality_score = db.Column(db.Float, default=0.0)  # Score de qualité (0-1)
    version = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    
    # Méthodes (conformes au diagramme)
    def compare(self, template):
        """
        Compare ce template avec un autre
        Retourne un score de similarité (0-1)
        """
        if self.type_biometrique != template.type_biometrique:
            return 0.0
        
        # Logique de comparaison (simplifiée)
        # En production, utiliser des algorithmes spécialisés
        import numpy as np
        from scipy.spatial.distance import cosine
        
        try:
            vec1 = np.array(self.template_data, dtype=np.float64)
            vec2 = np.array(template.template_data, dtype=np.float64)
            if vec1.shape != vec2.shape or vec1.size == 0:
                return 0.0
            return float(1.0 - cosine(vec1, vec2))
        except:
            return 0.0
    
    def generate(self, data):
        """
        Génère un template à partir de données brutes
        """
        # Stocker les données en JSON
        self.template_data = data if isinstance(data, list) else [data]
        return self
    
    def to_dict(self):
        """Version dictionnaire (sans données sensibles)"""
        return {
            'id': self.id,
            'type_biometrique': self.type_biometrique,
            'date_creation': self.date_creation.isoformat(),
            'date_derniere_utilisation': self.date_derniere_utilisation.isoformat() if self.date_derniere_utilisation else None,
            'label': self.label,
            'quality_score': self.quality_score,
            'version': self.version,
            'is_active': self.is_active
        }


class PhraseAleatoire(db.Model):
    """
    Modèle PhraseAleatoire
    Conforme au diagramme de classes
    """
    __tablename__ = 'phrases_aleatoires'
    
    # Attributs (conformes au diagramme)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    texte = db.Column(db.String(255), nullable=False)
    langue = db.Column(db.String(10), default='fr')
    
    # Clé étrangère
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Métadonnées
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    used_count = db.Column(db.Integer, default=0)
    
    @classmethod
    def getRandom(cls, user_id=None):
        """
        Récupère une phrase aléatoire
        Conforme au diagramme
        """
        query = cls.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        else:
            query = query.filter(cls.user_id.is_(None))
        
        return query.order_by(db.func.random()).first()
    
    def to_dict(self):
        return {
            'id': self.id,
            'texte': self.texte,
            'langue': self.langue
        }


class TentativeAuth(db.Model):
    """
    Modèle TentativeAuth
    Conforme au diagramme de classes
    """
    __tablename__ = 'tentatives_auth'
    
    # Attributs (conformes au diagramme)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date_heure = db.Column(db.DateTime, default=datetime.utcnow)
    etape = db.Column(db.String(50))  # facial, vocal, combine
    resultat = db.Column(db.Enum('succes', 'echec', name='resultat_auth'), nullable=False)
    
    # Informations supplémentaires
    raison_echec = db.Column(db.String(255), nullable=True)
    adresse_ip = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    
    # Clés étrangères
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    template_id = db.Column(db.String(36), db.ForeignKey('templates_biometriques.id'), nullable=True)
    phrase_id = db.Column(db.String(36), db.ForeignKey('phrases_aleatoires.id'), nullable=True)
    
    # Métadonnées
    score_similarite = db.Column(db.Float)
    temps_traitement_ms = db.Column(db.Integer)
    
    # Méthode (conforme au diagramme)
    def journaliser(self):
        """
        Journalise la tentative
        """
        # La sauvegarde est déjà faite par SQLAlchemy
        from models.log import LogAcces
        
        # Créer aussi un log d'accès
        log = LogAcces(
            type_acces='auth',
            statut=self.resultat,
            raison_echec=self.raison_echec,
            adresse_ip=self.adresse_ip or '127.0.0.1',
            utilisateur_id=self.user_id,
            details={
                'etape': self.etape,
                'score': self.score_similarite,
                'temps_ms': self.temps_traitement_ms
            }
        )
        log.enregistrer()
        
        return self
    
    def to_dict(self):
        return {
            'id': self.id,
            'date_heure': self.date_heure.isoformat(),
            'etape': self.etape,
            'resultat': self.resultat,
            'raison_echec': self.raison_echec,
            'adresse_ip': self.adresse_ip
        }


class AuthenticationAttempt(db.Model):
    """
    Modèle pour logs détaillés des tentatives d'authentification
    Utilisé pour dashboard admin et alertes
    """
    __tablename__ = 'authentication_attempts'
    
    # Identifiant
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Informations authentification
    email = db.Column(db.String(255), nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    success = db.Column(db.Boolean, default=False, index=True)
    reason = db.Column(db.String(100), nullable=False)  # MATCH_SUCCESS, FACE_MISMATCH, NO_FACE_DETECTED, etc
    similarity_score = db.Column(db.Float, nullable=True)
    
    # Informations client
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    
    # Contexte
    is_admin_attempt = db.Column(db.Boolean, default=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Index pour requêtes rapides (ix_authentication_attempts_timestamp est créé par index=True sur la colonne)
    __table_args__ = (
        db.Index('idx_auth_user_timestamp', 'user_id', 'timestamp'),
        db.Index('idx_auth_success_timestamp', 'success', 'timestamp'),
    )
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'email': self.email,
            'user_id': self.user_id,
            'success': self.success,
            'reason': self.reason,
            'similarity_score': self.similarity_score,
            'ip_address': self.ip_address,
            'is_admin': self.is_admin_attempt,
            'timestamp': self.timestamp.isoformat()
        }


class BiometricErrorLog(db.Model):
    """
    Modèle pour enregistrer les erreurs d'authentification biométrique
    Utilisé pour les alertes admin sur les erreurs Client Desktop
    """
    __tablename__ = 'biometric_error_logs'
    
    # Identifiant
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Informations erreur
    error_type = db.Column(db.String(100), nullable=False, index=True)
    error_message = db.Column(db.String(512), nullable=False)
    
    # Utilisateur concerné
    user_email = db.Column(db.String(255), nullable=True, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True, index=True)
    
    # Type d'authentification
    auth_type = db.Column(db.String(50), default='unknown')  # live, upload, api, desktop, etc
    
    # Informations client (pour Desktop)
    client_info = db.Column(db.JSON, nullable=True)  # os, app_version, screen_res, etc
    
    # Sévérité (1-10)
    severity = db.Column(db.Integer, default=5)
    
    # Status
    resolved = db.Column(db.Boolean, default=False, index=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    admin_notes = db.Column(db.String(512), nullable=True)
    
    # Timestamp
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Index pour requêtes rapides
    __table_args__ = (
        db.Index('idx_error_type_timestamp', 'error_type', 'timestamp'),
        db.Index('idx_error_user_timestamp', 'user_email', 'timestamp'),
        db.Index('idx_error_unresolved', 'resolved', 'timestamp'),
    )
    
    def mark_resolved(self, admin_id=None, notes=None):
        """Marquer l'erreur comme résolue"""
        self.resolved = True
        self.resolved_at = datetime.utcnow()
        self.admin_notes = notes
        db.session.commit()
        return self
    
    def to_dict(self):
        """Convertir en dictionnaire"""
        return {
            'id': self.id,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'user_email': self.user_email,
            'auth_type': self.auth_type,
            'client_info': self.client_info or {},
            'severity': self.severity,
            'resolved': self.resolved,
            'timestamp': self.timestamp.isoformat()
        }