"""
Modèle Rapport
Conforme au diagramme de classes
"""

from datetime import datetime
from core.database import db
import uuid
import json

class Rapport(db.Model):
    """
    Modèle Rapport
    Conforme au diagramme de classes
    """
    __tablename__ = 'rapports'
    
    # Attributs (conformes au diagramme)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = db.Column(db.String(50), nullable=False)  # journalier, hebdomadaire, mensuel, personnalise
    periode_debut = db.Column(db.Date, nullable=False)
    periode_fin = db.Column(db.Date, nullable=False)
    donnees = db.Column(db.JSON, nullable=False)  # Données du rapport
    format = db.Column(db.Enum('pdf', 'excel', 'csv', name='format_rapport'), default='pdf')
    
    # Métadonnées
    titre = db.Column(db.String(200), nullable=False)
    date_generation = db.Column(db.DateTime, default=datetime.utcnow)
    generateur_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    taille_fichier = db.Column(db.Integer, nullable=True)  # en bytes
    chemin_fichier = db.Column(db.String(500), nullable=True)
    
    # Relations
    generateur = db.relationship('User', foreign_keys=[generateur_id])
    logs = db.relationship('LogAcces', secondary='rapport_logs', lazy='dynamic')
    
    # Méthodes (conformes au diagramme)
    def generer(self):
        """
        Génère le rapport
        Retourne les données binaires du fichier
        """
        from services.report_service import ReportService
        return ReportService.generate(self)
    
    def exporter(self):
        """
        Exporte le rapport vers un fichier
        """
        from services.report_service import ReportService
        return ReportService.export(self)
    
    def to_dict(self):
        return {
            'id': self.id,
            'titre': self.titre,
            'type': self.type,
            'periode_debut': self.periode_debut.isoformat(),
            'periode_fin': self.periode_fin.isoformat(),
            'format': self.format,
            'date_generation': self.date_generation.isoformat(),
            'generateur': self.generateur.full_name if self.generateur else None,
            'taille_fichier': self.taille_fichier,
            'nb_logs': self.logs.count()
        }


# Table d'association pour Rapport <-> LogAcces
rapport_logs = db.Table('rapport_logs',
    db.Column('rapport_id', db.String(36), db.ForeignKey('rapports.id'), primary_key=True),
    db.Column('log_id', db.String(36), db.ForeignKey('logs_acces.id'), primary_key=True)
)