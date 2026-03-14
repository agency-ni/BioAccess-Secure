"""
Modèles pour les logs d'accès (immuables)
"""

from datetime import datetime
from core.database import db
from core.security import SecurityManager
import uuid
import hashlib
import json

class AccessLog(db.Model):
    """Log d'accès immuable avec chaînage hash"""
    __tablename__ = 'access_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Utilisateur
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    user_email = db.Column(db.String(120))
    user_name = db.Column(db.String(200))
    
    # Accès
    access_type = db.Column(db.String(20), nullable=False)  # login, logout, poste, porte, config
    access_resource = db.Column(db.String(100))  # poste-102, porte-serveur, etc.
    status = db.Column(db.String(20), nullable=False)  # success, failed
    reason = db.Column(db.String(500), nullable=True)  # raison échec
    
    # Métadonnées
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    location = db.Column(db.String(100), nullable=True)
    
    # Immutabilité : hash de la ligne précédente
    previous_hash = db.Column(db.String(64), nullable=True)
    current_hash = db.Column(db.String(64), unique=True, nullable=False)
    
    # Données supplémentaires (JSON)
    details = db.Column(db.JSON, nullable=True)
    
    def __init__(self, **kwargs):
        super(AccessLog, self).__init__(**kwargs)
        # Générer le hash après création
        self.current_hash = self._compute_hash()
    
    def _compute_hash(self):
        """Calcule le hash de cette entrée"""
        data = {
            'id': self.id,
            'timestamp': str(self.timestamp),
            'user_id': self.user_id,
            'user_email': self.user_email,
            'access_type': self.access_type,
            'status': self.status,
            'ip_address': self.ip_address
        }
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    
    def set_previous_hash(self, previous_log):
        """Définit le hash de l'entrée précédente (chaînage)"""
        if previous_log:
            self.previous_hash = previous_log.current_hash
    
    def verify_chain(self):
        """Vérifie l'intégrité de la chaîne"""
        if self.previous_hash:
            prev_log = AccessLog.query.filter_by(current_hash=self.previous_hash).first()
            if not prev_log:
                return False
            return prev_log.verify_chain()
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'user': {
                'id': self.user_id,
                'email': self.user_email,
                'name': self.user_name
            },
            'access_type': self.access_type,
            'access_resource': self.access_resource,
            'status': self.status,
            'reason': self.reason,
            'ip': self.ip_address,
            'hash': self.current_hash[:8] + '...',
            'verified': self.verify_chain()
        }
    
    @staticmethod
    def verify_all():
        """Vérifie l'intégrité de tous les logs"""
        logs = AccessLog.query.order_by(AccessLog.timestamp).all()
        for i in range(1, len(logs)):
            expected_hash = logs[i-1].current_hash
            if logs[i].previous_hash != expected_hash:
                return False, i
        return True, len(logs)