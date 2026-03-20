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
    type = db.Column(db.Enum('facial', 'vocal', name='type_biometrie'), nullable=False)
    donnees = db.Column(db.LargeBinary, nullable=False)  # Template chiffré
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Clé étrangère
    utilisateur_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
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
        if self.type != template.type:
            return 0.0
        
        # Déchiffrer les données
        data1 = SecurityManager.decrypt_data(self.donnees.decode())
        data2 = SecurityManager.decrypt_data(template.donnees.decode())
        
        # Logique de comparaison (simplifiée)
        # En production, utiliser des algorithmes spécialisés
        import numpy as np
        from scipy.spatial.distance import cosine
        
        try:
            vec1 = np.frombuffer(data1.encode())
            vec2 = np.frombuffer(data2.encode())
            similarity = 1 - cosine(vec1, vec2)
            return float(similarity)
        except:
            return 0.0
    
    def generate(self, data):
        """
        Génère un template à partir de données brutes
        """
        # Chiffrer les données
        encrypted = SecurityManager.encrypt_data(data)
        self.donnees = encrypted.encode()
        return self
    
    def to_dict(self):
        """Version dictionnaire (sans données sensibles)"""
        return {
            'id': self.id,
            'type': self.type,
            'date_creation': self.date_creation.isoformat(),
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
    utilisateur_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    
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
            query = query.filter_by(utilisateur_id=user_id)
        
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
    utilisateur_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
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
            adresse_ip=self.adresse_ip,
            utilisateur_id=self.utilisateur_id,
            details={
                'etape': self.etape,
                'score': self.score_similarite,
                'temps_ms': self.temps_traitement_ms
            }
        )
        db.session.add(log)
        db.session.commit()
        
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