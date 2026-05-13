"""
Gestion de la base de données PostgreSQL
Connexion, session, pooling, migrations
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError, OperationalError
import logging
import time
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Instance SQLAlchemy pour Flask
db = SQLAlchemy()

def init_db(app):
    """Initialise la base de données avec l'application Flask"""
    db.init_app(app)
    
    with app.app_context():
        try:
            # Tester la connexion
            db.session.execute(text('SELECT 1'))
            logger.info("✅ Connexion à la base de données réussie")
        except OperationalError as e:
            logger.error(f"❌ Erreur de connexion à la BDD: {e}")
            if app.config.get('FLASK_ENV') == 'production':
                raise
            return

        try:
            # Créer les tables manquantes uniquement (checkfirst=True = ne crash pas si elles existent déjà)
            db.create_all()
        except Exception as e:
            # Tables / index déjà existants → pas bloquant, purger l'état de la session
            try:
                db.session.rollback()
            except Exception:
                pass
            logger.warning(f"⚠️  db.create_all() partiel (tables/index existants): {e}")

        try:
            seed_random_phrases()
        except Exception as e:
            logger.warning(f"⚠️  Seed phrases ignoré: {e}")

        logger.info("✅ Base de données initialisée")


def seed_random_phrases():
    """Initialise les 20 phrases aléatoires pour l'authentification vocale"""
    try:
        from models.biometric import PhraseAleatoire
        import uuid
        from datetime import datetime
        
        # Vérifier si déjà créées
        if PhraseAleatoire.query.count() > 0:
            logger.info("Phrases aléatoires déjà présentes en BD")
            return
        
        # 20 phrases de défi vocales en français
        phrases = [
            "Bonjour, je suis une personne autorisée.",
            "Mon code d'accès est personnel et unique.",
            "Je reconnais les conditions d'utilisation.",
            "La sécurité biométrique est essentielle.",
            "Mon visage identifie qui je suis.",
            "Ma voix est un code de sécurité.",
            "J'accepte les politiques de confidentialité.",
            "Ces données biométriques sont protégées.",
            "L'authentification multifacteurs est forte.",
            "Mes empreintes digitales sont confidentielles.",
            "La reconnaissance faciale est précise.",
            "Je confirme mon authentification vocale.",
            "Aucun partage de données biométriques.",
            "La protection des données est prioritaire.",
            "Ces informations restent confidentielles.",
            "L'accès est contrôlé et sécurisé.",
            "Je valide cette tentative d'authentification.",
            "Mes identifiants biométriques sont uniques.",
            "La cryptographie protège mes données.",
            "L'audit trail enregistre tous les accès."
        ]
        
        for texte in phrases:
            phrase = PhraseAleatoire(
                id=str(uuid.uuid4()),
                texte=texte,
                langue='fr',
                user_id=None,  # Phrases globales (colonne ORM = user_id)
                date_creation=datetime.utcnow()
            )
            db.session.add(phrase)
        
        db.session.commit()
        logger.info(f"✅ {len(phrases)} phrases aléatoires créées en BD")
        
    except Exception as e:
        logger.warning(f"⚠️  Erreur seed phrases: {e} (non-critique)")
        db.session.rollback()
        # Ne pas bloquer l'initialisation si les phrases échouent

def get_db_engine(uri, pool_size=10, max_overflow=20, pool_timeout=30, pool_recycle=1800):
    """Crée un moteur SQLAlchemy avec pooling optimisé"""
    return create_engine(
        uri,
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=True,  # Vérifie la connexion avant utilisation
        echo=False,
        connect_args={
            'connect_timeout': 10,
            'keepalives': 1,
            'keepalives_idle': 30,
            'keepalives_interval': 10,
            'keepalives_count': 5
        }
    )

def health_check():
    """Vérifie la connexion à la base de données"""
    try:
        db.session.execute(text('SELECT 1'))
        return True
    except SQLAlchemyError as e:
        logger.error(f"Health check BDD échoué: {e}")
        return False

@contextmanager
def db_transaction():
    """
    Context manager pour les transactions
    Garantit le rollback en cas d'erreur
    """
    try:
        yield
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur transaction BDD: {e}")
        raise

def execute_with_retry(query, params=None, max_retries=3, retry_delay=1):
    """
    Exécute une requête avec tentatives en cas d'échec
    Utile pour gérer les deadlocks et les timeouts
    """
    for attempt in range(max_retries):
        try:
            if params:
                result = db.session.execute(text(query), params)
            else:
                result = db.session.execute(text(query))
            db.session.commit()
            return result
        except OperationalError as e:
            db.session.rollback()
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Tentative {attempt + 1} échouée, nouvelle tentative dans {retry_delay}s")
            time.sleep(retry_delay)
        except Exception as e:
            db.session.rollback()
            raise

def bulk_insert(model, data_list, chunk_size=1000):
    """
    Insertion en masse avec chunking pour éviter les timeouts
    """
    try:
        for i in range(0, len(data_list), chunk_size):
            chunk = data_list[i:i + chunk_size]
            db.session.bulk_insert_mappings(model, chunk)
            db.session.commit()
            logger.info(f"Insertion lot {i//chunk_size + 1} terminée")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur insertion en masse: {e}")
        raise

def get_db_stats():
    """
    Récupère des statistiques sur la base de données
    """
    stats = {}
    try:
        # Taille de la base
        result = db.session.execute(text("""
            SELECT pg_database_size(current_database()) / 1024 / 1024 as size_mb
        """)).first()
        stats['size_mb'] = result[0] if result else 0
        
        # Nombre de connexions actives
        result = db.session.execute(text("""
            SELECT count(*) FROM pg_stat_activity WHERE state = 'active'
        """)).first()
        stats['active_connections'] = result[0] if result else 0
        
        # Taux de cache hit
        result = db.session.execute(text("""
            SELECT 
                sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as hit_ratio
            FROM pg_statio_user_tables
        """)).first()
        stats['cache_hit_ratio'] = round(result[0] * 100, 2) if result and result[0] else 0
        
    except Exception as e:
        logger.error(f"Erreur récupération stats BDD: {e}")
    
    return stats