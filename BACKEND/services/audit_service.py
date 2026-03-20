"""
Service d'audit - Traçabilité des actions admin
"""

from models.user import User
from models.log import LogAcces
from core.database import db
from flask import g
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class AuditService:
    """Service pour l'audit des actions admin"""
    
    @staticmethod
    def log_action(action, user_id=None, details=None, ip_address=None):
        """
        Journalise une action admin
        """
        if not user_id and hasattr(g, 'user_id'):
            user_id = g.user_id
        if not ip_address and hasattr(g, 'client_ip'):
            ip_address = g.client_ip
        
        log = LogAcces(
            type_acces='config',
            statut='succes',
            adresse_ip=ip_address,
            utilisateur_id=user_id,
            details={
                'action': action,
                'timestamp': datetime.utcnow().isoformat(),
                **details
            } if details else {'action': action}
        )
        
        db.session.add(log)
        db.session.commit()
        
        logger.info(f"AUDIT: {action} par {user_id}")
        return log
    
    @staticmethod
    def get_admin_actions(filters=None, page=1, per_page=50):
        """Récupère l'historique des actions admin"""
        query = LogAcces.query.filter_by(type_acces='config')
        
        if filters:
            if filters.get('user_id'):
                query = query.filter_by(utilisateur_id=filters['user_id'])
            if filters.get('date_debut'):
                query = query.filter(LogAcces.date_heure >= filters['date_debut'])
            if filters.get('date_fin'):
                query = query.filter(LogAcces.date_heure <= filters['date_fin'])
            if filters.get('action'):
                query = query.filter(LogAcces.details['action'].astext == filters['action'])
        
        pagination = query.order_by(LogAcces.date_heure.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for log in pagination.items:
            entry = {
                'id': log.id,
                'date': log.date_heure.isoformat(),
                'ip': log.adresse_ip,
                'user': None
            }
            
            if log.utilisateur_id:
                user = User.query.get(log.utilisateur_id)
                if user:
                    entry['user'] = user.full_name
            
            if log.details:
                entry.update(log.details)
            
            result.append(entry)
        
        return {
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'logs': result
        }
    
    @staticmethod
    def export_for_legal(start_date, end_date):
        """
        Exporte les logs pour usage légal
        """
        logs = LogAcces.query.filter(
            LogAcces.date_heure >= start_date,
            LogAcces.date_heure <= end_date
        ).order_by(LogAcces.date_heure).all()
        
        # Vérifier l'intégrité
        is_valid, count = LogAcces.verify_chain()
        
        data = {
            'export_date': datetime.utcnow().isoformat(),
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'integrity': {
                'valid': is_valid,
                'logs_checked': count
            },
            'logs': []
        }
        
        for log in logs:
            log_data = log.to_dict()
            log_data['verified'] = log.verify_integrity()
            data['logs'].append(log_data)
        
        # Générer un hash global
        import hashlib
        data_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        data['global_hash'] = data_hash
        
        return data
    
    @staticmethod
    def verify_all_logs():
        """
        Vérifie l'intégrité de tous les logs
        """
        return LogAcces.verify_chain()