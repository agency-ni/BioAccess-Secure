"""
Tâches asynchrones pour Celery
"""

from core.queue import celery_app
from core.database import db
from models.log import LogAcces
from models.alert import Alerte
from services.report_service import ReportService
from services.email_service import EmailService
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def cleanup_old_logs(days=90):
    """Nettoie les logs plus vieux que 'days' jours"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = LogAcces.query.filter(LogAcces.date_heure < cutoff).delete()
        db.session.commit()
        logger.info(f"✅ Nettoyage logs: {result} entrées supprimées")
        return result
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage logs: {e}")
        db.session.rollback()
        return 0

@celery_app.task
def generate_daily_reports():
    """Génère les rapports quotidiens automatiques"""
    try:
        reports = ReportService.generate_daily_reports()
        logger.info(f"✅ {len(reports)} rapports quotidiens générés")
        
        # Envoyer par email aux admins
        for report in reports:
            EmailService.send_report.delay(report.id)
        
        return len(reports)
    except Exception as e:
        logger.error(f"❌ Erreur génération rapports: {e}")
        return 0

@celery_app.task
def check_system_health():
    """Vérifie la santé du système et crée des alertes si nécessaire"""
    try:
        from core.database import health_check
        from core.cache import get_cache
        
        alerts = []
        
        # Vérifier BDD
        if not health_check():
            alert = Alerte.create_from_rule(
                'database_down',
                message="Base de données inaccessible"
            )
            alerts.append(alert)
        
        # Vérifier Redis
        cache = get_cache()
        if cache:
            try:
                cache.ping()
            except:
                alert = Alerte.create_from_rule(
                    'redis_down',
                    message="Cache Redis inaccessible"
                )
                alerts.append(alert)
        
        logger.info(f"✅ Health check: {len(alerts)} alertes créées")
        return len(alerts)
    except Exception as e:
        logger.error(f"❌ Erreur health check: {e}")
        return 0

@celery_app.task
def send_email_async(recipient, subject, body, html=None):
    """Envoi d'email asynchrone"""
    from services.email_service import EmailService
    try:
        EmailService.send_sync(recipient, subject, body, html)
        return True
    except Exception as e:
        logger.error(f"❌ Erreur envoi email: {e}")
        return False

@celery_app.task
def process_biometric_template(image_path, user_id):
    """Traite un template biométrique (tâche lourde)"""
    from services.biometric_service import BiometricService
    try:
        result = BiometricService.process_template(image_path, user_id)
        return result
    except Exception as e:
        logger.error(f"❌ Erreur traitement biométrique: {e}")
        return None