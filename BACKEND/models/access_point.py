"""
Modèles pour les points d'accès physiques
- PosteTravail
- Porte
- Configuration
"""

from datetime import datetime
from core.database import db
import uuid

class PosteTravail(db.Model):
    """
    Modèle PosteTravail
    Conforme au diagramme de classes
    """
    __tablename__ = 'postes_travail'
    
    # Attributs (conformes au diagramme)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = db.Column(db.String(100), nullable=False)
    adresse_ip = db.Column(db.String(45), unique=True, nullable=False)
    systeme = db.Column(db.String(50), default='Windows')
    statut = db.Column(db.Enum('actif', 'inactif', 'verrouille', name='statut_poste'), default='actif')
    
    # FK vers users.id (l'employé est un User, pas une table séparée)
    employe_id = db.Column(db.String(36), db.ForeignKey('users.id'), unique=True, nullable=True)

    # Métadonnées
    localisation = db.Column(db.String(100))
    mac_address = db.Column(db.String(17), unique=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    os_version = db.Column(db.String(50))
    
    # Méthodes (conformes au diagramme)
    def verrouiller(self):
        """Verrouille le poste de travail"""
        self.statut = 'verrouille'
        db.session.commit()
        return self
    
    def deverrouiller(self):
        """Déverrouille le poste de travail"""
        self.statut = 'actif'
        db.session.commit()
        return self
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'adresse_ip': self.adresse_ip,
            'systeme': self.systeme,
            'statut': self.statut,
            'localisation': self.localisation,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'employe_id': self.employe_id
        }


class Porte(db.Model):
    """
    Modèle Porte
    Conforme au diagramme de classes
    """
    __tablename__ = 'portes'
    
    # Attributs (conformes au diagramme)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nom = db.Column(db.String(100), nullable=False)
    localisation = db.Column(db.String(100), nullable=False)
    statut = db.Column(db.Enum('ouverte', 'fermee', name='statut_porte'), default='fermee')
    
    # Métadonnées
    type_acces = db.Column(db.String(20), default='biometrique')  # biometrique, badge, etc.
    departements_autorises = db.Column(db.JSON, default=list)  # ['informatique', 'direction']
    horaires_autorises = db.Column(db.JSON, nullable=True)  # {'debut': '08:00', 'fin': '20:00'}
    timeout_ouverture = db.Column(db.Integer, default=5)  # secondes
    phrase_id = db.Column(db.String(36), db.ForeignKey('phrases_aleatoires.id'), nullable=True)
    
    # Méthodes (conformes au diagramme)
    def ouvrir(self):
        """Ouvre la porte"""
        self.statut = 'ouverte'
        db.session.commit()
        return self
    
    def fermer(self):
        """Ferme la porte"""
        self.statut = 'fermee'
        db.session.commit()
        return self
    
    def check_access(self, user):
        """
        Vérifie si un utilisateur a le droit d'accéder
        """
        from datetime import datetime
        
        # Vérifier le département
        if user.departement not in self.departements_autorises:
            return False, "Département non autorisé"
        
        # Vérifier les horaires (si configurés)
        if self.horaires_autorises:
            now = datetime.now().strftime('%H:%M')
            debut = self.horaires_autorises.get('debut', '00:00')
            fin = self.horaires_autorises.get('fin', '23:59')
            
            if not (debut <= now <= fin):
                return False, "Hors horaires autorisés"
        
        return True, "Accès autorisé"
    
    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'localisation': self.localisation,
            'statut': self.statut,
            'departements_autorises': self.departements_autorises,
            'horaires_autorises': self.horaires_autorises
        }


class Configuration(db.Model):
    """
    Modèle Configuration
    Conforme au diagramme de classes
    """
    __tablename__ = 'configurations'
    
    # Attributs (conformes au diagramme)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cle = db.Column(db.String(100), unique=True, nullable=False)
    valeur = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    
    # FK vers users.id (admin = User avec role admin/super_admin), nullable pour flexibilité
    admin_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    
    # Métadonnées
    date_modification = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    type_donnee = db.Column(db.String(20), default='string')  # string, int, float, bool, json
    
    # Méthodes (conformes au diagramme)
    def getValue(self, cle):
        """
        Récupère la valeur d'une configuration
        """
        config = self.query.filter_by(cle=cle).first()
        if not config:
            return None
        
        # Convertir selon le type
        if config.type_donnee == 'int':
            return int(config.valeur)
        elif config.type_donnee == 'float':
            return float(config.valeur)
        elif config.type_donnee == 'bool':
            return config.valeur.lower() in ['true', '1', 'yes']
        elif config.type_donnee == 'json':
            import json
            return json.loads(config.valeur)
        else:
            return config.valeur
    
    def setValue(self, cle, valeur, admin_id=None):
        """
        Définit la valeur d'une configuration
        """
        config = self.query.filter_by(cle=cle).first()
        if config:
            # Vérifier les permissions
            if admin_id:
                config.admin_id = admin_id
            config.valeur = str(valeur)
        else:
            config = self(cle=cle, valeur=str(valeur), admin_id=admin_id)
            db.session.add(config)
        
        db.session.commit()
        return config
    
    def to_dict(self):
        return {
            'id': self.id,
            'cle': self.cle,
            'valeur': self.valeur if self.type_donnee == 'string' else self.getValue(self.cle),
            'description': self.description,
            'type_donnee': self.type_donnee,
            'date_modification': self.date_modification.isoformat(),
            'admin_id': self.admin_id
        }