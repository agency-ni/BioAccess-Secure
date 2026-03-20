"""
Gestion des files d'attente asynchrones (Celery)
Pour les tâches longues : envoi emails, génération rapports, logs
"""

from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

celery_app = None

def init_queue(app):
    """Initialise Celery avec Redis comme broker"""
    global celery_app
    
    celery_app = Celery(
        'bioaccess',
        broker=app.config['REDIS_URL'],
        backend=app.config['REDIS_URL'],
        include=['services.tasks']
    )
    
    # Configuration
    celery_app.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_max_tasks_per_child=200,
        worker_prefetch_multiplier=1,
        result_expires=3600,  # 1 heure
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        task_default_rate_limit='100/m',
        beat_schedule={
            'cleanup-old-logs': {
                'task': 'services.tasks.cleanup_old_logs',
                'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h
            },
            'generate-daily-reports': {
                'task': 'services.tasks.generate_daily_reports',
                'schedule': crontab(hour=3, minute=0),  # Tous les jours à 3h
            },
            'check-system-health': {
                'task': 'services.tasks.check_system_health',
                'schedule': crontab(minute='*/15'),  # Toutes les 15 minutes
            },
        }
    )
    
    logger.info("✅ File d'attente Celery initialisée")

def get_queue():
    """Retourne l'instance Celery"""
    return celery_app