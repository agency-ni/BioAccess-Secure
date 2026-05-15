"""
Service de gestion des alertes
"""

from models.alert import Alerte
from models.user import User
from core.database import db
from core.cache import Cache
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class AlertService:
    """Service pour la gestion des alertes"""
    
    @staticmethod
    def create_alert(alert_type, gravite, message, user_id=None, log_id=None, **kwargs):
        """Crée une nouvelle alerte"""
        alerte = Alerte(
            type=alert_type,
            gravite=gravite,
            message=message,
            utilisateur_id=user_id,
            log_id=log_id
        )
        
        db.session.add(alerte)
        db.session.commit()
        
        # Notifier en temps réel (via WebSocket plus tard)
        AlertService._notify_realtime(alerte)
        
        # Envoyer email si haute priorité
        if gravite == 'haute' and user_id:
            from services.email_service import EmailService
            user = db.session.get(User, user_id)
            if user:
                EmailService.send_alert_email(alerte, user)
        
        return alerte
    
    @staticmethod
    def check_rules(log_entry):
        """Vérifie les règles et crée des alertes si nécessaire"""
        
        # Règle 1: 3 échecs consécutifs
        if log_entry.type_acces == 'auth' and log_entry.statut == 'echec':
            key = f"failed_attempts:{log_entry.utilisateur_id}"
            attempts = Cache.incr(key)
            Cache.expire(key, 300)  # 5 minutes
            
            if attempts >= 3:
                AlertService.create_alert(
                    'securite',
                    'haute',
                    f"3 échecs consécutifs pour l'utilisateur {log_entry.utilisateur_id}",
                    log_entry.utilisateur_id,
                    log_entry.id
                )
        
        # Règle 2: Accès porte non autorisé
        if log_entry.type_acces == 'porte' and log_entry.statut == 'echec':
            if log_entry.raison_echec == "Département non autorisé":
                AlertService.create_alert(
                    'securite',
                    'haute',
                    f"Tentative accès porte non autorisé: {log_entry.raison_echec}",
                    log_entry.utilisateur_id,
                    log_entry.id
                )
        
        # Règle 3: Accès hors horaire
        if log_entry.type_acces == 'porte' and log_entry.statut == 'succes':
            hour = log_entry.date_heure.hour
            if hour < 8 or hour > 20:
                AlertService.create_alert(
                    'securite',
                    'moyenne',
                    f"Accès porte hors horaire (à {hour}h)",
                    log_entry.utilisateur_id,
                    log_entry.id
                )
        
        # Règle 4: 5 échecs en 10 minutes
        if log_entry.statut == 'echec':
            from models.log import LogAcces
            ten_min_ago = datetime.utcnow() - timedelta(minutes=10)
            recent_failures = LogAcces.query.filter(
                LogAcces.utilisateur_id == log_entry.utilisateur_id,
                LogAcces.statut == 'echec',
                LogAcces.date_heure >= ten_min_ago
            ).count()
            
            if recent_failures >= 5:
                AlertService.create_alert(
                    'securite',
                    'moyenne',
                    f"Activité suspecte: {recent_failures} échecs en 10 min",
                    log_entry.utilisateur_id,
                    log_entry.id
                )
    
    @staticmethod
    def get_alerts(filters=None, page=1, per_page=20):
        """Récupère les alertes avec filtres"""
        query = Alerte.query
        
        if filters:
            if filters.get('gravite'):
                query = query.filter_by(gravite=filters['gravite'])
            if filters.get('traitee') is not None:
                query = query.filter_by(traitee=filters['traitee'])
            if filters.get('type'):
                query = query.filter_by(type=filters['type'])
            if filters.get('user_id'):
                query = query.filter_by(utilisateur_id=filters['user_id'])
        
        pagination = query.order_by(Alerte.date_creation.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'alertes': [a.to_dict() for a in pagination.items]
        }
    
    @staticmethod
    def mark_as_treated(alert_id, user_id, commentaire=None):
        """Marque une alerte comme traitée"""
        alerte = db.session.get(Alerte, alert_id)
        if not alerte:
            return None
        
        alerte.marquerTraitee(user_id, commentaire)
        return alerte
    
    @staticmethod
    def cleanup_old_alerts(days=30):
        """Nettoie les alertes anciennes"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = Alerte.query.filter(
            Alerte.date_creation < cutoff,
            Alerte.traitee == True
        ).delete()
        db.session.commit()
        return result
    
    @staticmethod
    def _notify_realtime(alert):
        """Notifie en temps réel (WebSocket)"""
        # À implémenter avec Socket.IO ou Server-Sent Events
        pass