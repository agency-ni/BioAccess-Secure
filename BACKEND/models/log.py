"""
Modèles de journalisation (conformes au diagramme)
- LogAcces
- Alerte
"""

from datetime import datetime
from core.database import db
from core.security import SecurityManager
import uuid
import hashlib
import json

class LogAcces(db.Model):
    """
    Modèle LogAcces
    Conforme au diagramme de classes
    Implémente l'immutabilité avec chaînage de hash
    """
    __tablename__ = 'logs_acces'
    
    # Attributs (conformes au diagramme)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date_heure = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    type_acces = db.Column(db.Enum('poste', 'porte', 'auth', 'config', name='type_acces'), nullable=False)
    statut = db.Column(db.Enum('succes', 'echec', name='resultat_auth'), nullable=False)
    raison_echec = db.Column(db.String(500), nullable=True)
    adresse_ip = db.Column(db.String(45), nullable=False)
    
    # Clé étrangère
    utilisateur_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Données supplémentaires
    details = db.Column(db.JSON, nullable=True)
    user_agent = db.Column(db.String(256))
    resource = db.Column(db.String(100))  # poste-102, porte-serveur, etc.
    
    # Immutabilité - hash chaîné (blockchain-like)
    hash_precedent = db.Column(db.String(64), nullable=True)
    hash_actuel = db.Column(db.String(64), unique=True, nullable=False)
    signature = db.Column(db.String(256), nullable=True)  # Signature numérique
    
    # Méthode (conforme au diagramme)
    def enregistrer(self):
        """
        Enregistre le log avec calcul du hash
        """
        # Calculer le hash actuel
        data = {
            'id': self.id,
            'date_heure': str(self.date_heure),
            'type_acces': self.type_acces,
            'statut': self.statut,
            'adresse_ip': self.adresse_ip,
            'utilisateur_id': self.utilisateur_id
        }
        self.hash_actuel = SecurityManager.hash_log_entry(data)
        
        # Récupérer le dernier log pour chaînage
        dernier_log = LogAcces.query.order_by(LogAcces.date_heure.desc()).first()
        if dernier_log:
            self.hash_precedent = dernier_log.hash_actuel
        
        db.session.add(self)
        db.session.commit()
        return self
    
    @classmethod
    def verify_chain(cls):
        """
        Vérifie l'intégrité de toute la chaîne de logs
        """
        logs = cls.query.order_by(cls.date_heure).all()
        for i in range(1, len(logs)):
            # Recalculer le hash précédent
            prev_data = {
                'id': logs[i-1].id,
                'date_heure': str(logs[i-1].date_heure),
                'type_acces': logs[i-1].type_acces,
                'statut': logs[i-1].statut,
                'adresse_ip': logs[i-1].adresse_ip,
                'utilisateur_id': logs[i-1].utilisateur_id
            }
            expected_hash = SecurityManager.hash_log_entry(prev_data)
            
            if logs[i].hash_precedent != expected_hash:
                return False, i
        
        return True, len(logs)
    
    def to_dict(self):
        return {
            'id': self.id,
            'date_heure': self.date_heure.isoformat(),
            'type_acces': self.type_acces,
            'statut': self.statut,
            'raison_echec': self.raison_echec,
            'adresse_ip': self.adresse_ip,
            'utilisateur_id': self.utilisateur_id,
            'resource': self.resource,
            'hash': self.hash_actuel[:8] + '...' if self.hash_actuel else None,
            'verified': self.verify_integrity()
        }
    
    def verify_integrity(self):
        """Vérifie l'intégrité de ce log"""
        data = {
            'id': self.id,
            'date_heure': str(self.date_heure),
            'type_acces': self.type_acces,
            'statut': self.statut,
            'adresse_ip': self.adresse_ip,
            'utilisateur_id': self.utilisateur_id
        }
        expected = SecurityManager.hash_log_entry(data)
        return expected == self.hash_actuel


class Alerte(db.Model):
    """
    Modèle Alerte
    Conforme au diagramme de classes
    """
    __tablename__ = 'alertes'
    
    # Attributs (conformes au diagramme)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = db.Column(db.Enum('securite', 'systeme', 'tentative', name='type_alerte'), nullable=False)
    gravite = db.Column(db.Enum('basse', 'moyenne', 'haute', name='gravite'), nullable=False)
    message = db.Column(db.String(500), nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    traitee = db.Column(db.Boolean, default=False)
    
    # Clés étrangères
    utilisateur_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    log_id = db.Column(db.String(36), db.ForeignKey('logs_acces.id'), nullable=True)
    
    # Métadonnées
    assignee_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    date_traitement = db.Column(db.DateTime, nullable=True)
    commentaire = db.Column(db.Text, nullable=True)
    
    # Relations
    log = db.relationship('LogAcces', foreign_keys=[log_id])
    utilisateur = db.relationship('User', foreign_keys=[utilisateur_id])
    assignee = db.relationship('User', foreign_keys=[assignee_id])
    
    # Méthodes (conformes au diagramme)
    def envoyer(self):
        """
        Envoie l'alerte (notifications)
        """
        from services.alert_service import AlertService
        AlertService.send_alert(self)
        return self
    
    def marquerTraitee(self, user_id, commentaire=None):
        """
        Marque l'alerte comme traitée
        """
        self.traitee = True
        self.date_traitement = datetime.utcnow()
        self.assignee_id = user_id
        if commentaire:
            self.commentaire = commentaire
        db.session.commit()
        return self
    
    @classmethod
    def create_from_rule(cls, rule_name, user_id=None, log_id=None, **kwargs):
        """
        Crée une alerte à partir d'une règle prédéfinie
        """
        from utils.constants import ALERT_RULES
        
        if rule_name not in ALERT_RULES:
            return None
        
        rule = ALERT_RULES[rule_name]
        alerte = cls(
            type=rule['type'],
            gravite=rule['gravite'],
            message=rule['message'].format(**kwargs),
            utilisateur_id=user_id,
            log_id=log_id
        )
        db.session.add(alerte)
        db.session.commit()
        return alerte
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'gravite': self.gravite,
            'message': self.message,
            'date_creation': self.date_creation.isoformat(),
            'traitee': self.traitee,
            'date_traitement': self.date_traitement.isoformat() if self.date_traitement else None,
            'utilisateur': self.utilisateur.full_name if self.utilisateur else None,
            'assignee': self.assignee.full_name if self.assignee else None,
            'commentaire': self.commentaire
        }