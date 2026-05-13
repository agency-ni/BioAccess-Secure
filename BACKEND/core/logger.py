"""
Journalisation avancée avec rotation et format JSON
"""

import os
import logging
import json
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from pythonjsonlogger import jsonlogger

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Formatteur JSON personnalisé pour les logs"""
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['module'] = record.module
        log_record['function'] = record.funcName

def setup_logger(app):
    """Configure les logger pour l'application"""
    
    # Créer le dossier logs si nécessaire
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Niveau de log
    log_level = getattr(logging, app.config['LOG_LEVEL'], logging.INFO)
    
    # Logger pour l'application
    app_logger = logging.getLogger('bioaccess')
    app_logger.setLevel(log_level)
    
    # Handler fichier avec rotation
    file_handler = RotatingFileHandler(
        app.config['LOG_FILE'],
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(log_level)
    
    # Format JSON pour les logs structurés
    json_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(module)s %(function)s %(message)s'
    )
    file_handler.setFormatter(json_formatter)
    
    # Handler console (développement)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # Ajouter les handlers
    app_logger.addHandler(file_handler)
    
    if app.config['FLASK_ENV'] == 'development':
        app_logger.addHandler(console_handler)
    
    # Logger pour les accès (audit)
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(logging.INFO)
    
    audit_handler = RotatingFileHandler(
        'logs/audit.log',
        maxBytes=10485760,
        backupCount=30
    )
    audit_handler.setFormatter(json_formatter)
    audit_logger.addHandler(audit_handler)
    
    return app_logger, audit_logger

def log_audit(action=None, user_id=None, ip=None, details=None, **kwargs):
    """Log une action d'audit. Accepts both positional and keyword call styles."""
    audit_logger = logging.getLogger('audit')
    merged_details = details or {}
    if kwargs:
        merged_details = {**merged_details, **kwargs}
    audit_logger.info(json.dumps({
        'action': action,
        'user_id': str(user_id) if user_id else None,
        'ip': ip,
        'details': merged_details,
        'timestamp': datetime.utcnow().isoformat()
    }, default=str))