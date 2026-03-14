"""
Gestion de la base de données PostgreSQL
Connexion, session, et utilitaires
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import logging

logger = logging.getLogger(__name__)

# Instance SQLAlchemy pour Flask
db = SQLAlchemy()

def init_db(app):
    """Initialise la base de données avec l'application Flask"""
    db.init_app(app)
    
    with app.app_context():
        try:
            # Créer les tables si elles n'existent pas
            db.create_all()
            logger.info("✅ Base de données initialisée avec succès")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation BDD: {e}")
            raise

def get_db_engine(uri, pool_size=10, max_overflow=20):
    """Crée un moteur SQLAlchemy avec pooling"""
    return create_engine(
        uri,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )

def health_check():
    """Vérifie la connexion à la base de données"""
    try:
        db.session.execute('SELECT 1')
        return True
    except Exception as e:
        logger.error(f"Health check BDD échoué: {e}")
        return False