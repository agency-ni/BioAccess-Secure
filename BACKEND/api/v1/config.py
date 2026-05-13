"""
Routes API pour la configuration système
GET    /api/v1/config              — toute la config
GET    /api/v1/config/<key>        — une clé
PUT    /api/v1/config/<key>        — modifier une clé
POST   /api/v1/config/batch        — modifier plusieurs clés
POST   /api/v1/config/reset        — remettre les valeurs par défaut
"""

from flask import Blueprint, request, jsonify, g
from datetime import datetime
import logging

from core.database import db
from api.middlewares.auth_middleware import token_required, admin_required
from models.access_point import Configuration

logger = logging.getLogger(__name__)

config_bp = Blueprint('config', __name__, url_prefix='/config')

# Valeurs par défaut + métadonnées
CONFIG_DEFAULTS = {
    # Biométrie
    'facial_threshold':   {'valeur': '0.55', 'type_donnee': 'float',   'description': 'Seuil distance faciale (0.0-1.0, plus bas = plus strict)'},
    'voice_threshold':    {'valeur': '0.70', 'type_donnee': 'float',   'description': 'Seuil similarité cosinus vocale (0.0-1.0)'},
    'max_attempts':       {'valeur': '3',    'type_donnee': 'integer', 'description': 'Tentatives max avant verrouillage'},
    'lockout_duration':   {'valeur': '15',   'type_donnee': 'integer', 'description': 'Durée verrouillage en minutes'},
    'liveness_required':  {'valeur': 'true', 'type_donnee': 'boolean', 'description': 'Exiger détection de vivant'},
    # Accès physique
    'lock_delay':         {'valeur': '5',    'type_donnee': 'integer', 'description': 'Délai auto-verrouillage (minutes)'},
    'door_open_time':     {'valeur': '3',    'type_donnee': 'integer', 'description': 'Durée ouverture porte (secondes)'},
    'anti_tailgating':    {'valeur': 'true', 'type_donnee': 'boolean', 'description': 'Protection anti-tailgating'},
    'access_alarm':       {'valeur': 'true', 'type_donnee': 'boolean', 'description': 'Alarme accès non autorisé'},
    # Notifications
    'email_alerts':       {'valeur': 'true',  'type_donnee': 'boolean', 'description': 'Alertes par email'},
    'sms_alerts':         {'valeur': 'false', 'type_donnee': 'boolean', 'description': 'Alertes par SMS'},
    'system_alerts':      {'valeur': 'true',  'type_donnee': 'boolean', 'description': 'Alertes système internes'},
    'alert_level':        {'valeur': 'all',   'type_donnee': 'string',  'description': 'Niveau alertes: all|high|critical'},
    # Journalisation
    'log_level':          {'valeur': 'info',  'type_donnee': 'string',  'description': 'Niveau log: debug|info|warning|error'},
    'log_retention':      {'valeur': '90',    'type_donnee': 'integer', 'description': 'Rétention logs (jours)'},
    'auto_archive':       {'valeur': 'true',  'type_donnee': 'boolean', 'description': 'Archivage automatique des logs'},
    'secure_backup':      {'valeur': 'true',  'type_donnee': 'boolean', 'description': 'Sauvegarde chiffrée des logs'},
    # API
    'api_enabled':        {'valeur': 'true',  'type_donnee': 'boolean', 'description': 'API externe activée'},
    'api_rate_limit':     {'valeur': '100',   'type_donnee': 'integer', 'description': 'Limite requêtes/heure par IP'},
    'api_version':        {'valeur': 'v1.0',  'type_donnee': 'string',  'description': 'Version API exposée'},
    'oauth2':             {'valeur': 'true',  'type_donnee': 'boolean', 'description': 'OAuth2 activé'},
    'tls_encryption':     {'valeur': 'true',  'type_donnee': 'boolean', 'description': 'TLS obligatoire'},
    'custom_headers':     {'valeur': 'true',  'type_donnee': 'boolean', 'description': 'Headers personnalisés autorisés'},
}


def _cast_value(raw: str, type_donnee: str):
    """Convertit la valeur texte en type Python natif."""
    if type_donnee == 'boolean':
        return raw.lower() in ('true', '1', 'yes', 'on')
    if type_donnee == 'integer':
        return int(raw)
    if type_donnee == 'float':
        return float(raw)
    return raw


def _ensure_defaults():
    """Crée les entrées manquantes avec les valeurs par défaut."""
    for key, meta in CONFIG_DEFAULTS.items():
        existing = Configuration.query.filter_by(cle=key).first()
        if not existing:
            entry = Configuration(
                cle=key,
                valeur=meta['valeur'],
                type_donnee=meta['type_donnee'],
                description=meta['description'],
                date_modification=datetime.utcnow()
            )
            db.session.add(entry)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


def _config_to_dict(entry: Configuration) -> dict:
    meta = CONFIG_DEFAULTS.get(entry.cle, {})
    type_donnee = entry.type_donnee or meta.get('type_donnee', 'string')
    return {
        'key':         entry.cle,
        'value':       _cast_value(entry.valeur, type_donnee),
        'raw_value':   entry.valeur,
        'type':        type_donnee,
        'description': entry.description or meta.get('description', ''),
        'updated_at':  entry.date_modification.isoformat() if entry.date_modification else None,
    }


# ──────────────────────────────────────────────
# GET /api/v1/config
# ──────────────────────────────────────────────
@config_bp.route('', methods=['GET'])
@token_required
def get_all_config():
    """Retourne toute la configuration sous forme de dict {key: value}."""
    try:
        _ensure_defaults()
        entries = Configuration.query.order_by(Configuration.cle).all()
        result = {}
        for entry in entries:
            meta = CONFIG_DEFAULTS.get(entry.cle, {})
            type_donnee = entry.type_donnee or meta.get('type_donnee', 'string')
            result[entry.cle] = _cast_value(entry.valeur, type_donnee)
        return jsonify({'success': True, 'config': result})
    except Exception as e:
        logger.error(f"Erreur GET config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ──────────────────────────────────────────────
# GET /api/v1/config/<key>
# ──────────────────────────────────────────────
@config_bp.route('/<string:key>', methods=['GET'])
@token_required
def get_config_key(key):
    try:
        _ensure_defaults()
        entry = Configuration.query.filter_by(cle=key).first()
        if not entry:
            return jsonify({'success': False, 'error': f"Clé '{key}' introuvable"}), 404
        return jsonify({'success': True, 'data': _config_to_dict(entry)})
    except Exception as e:
        logger.error(f"Erreur GET config/{key}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ──────────────────────────────────────────────
# PUT /api/v1/config/<key>
# ──────────────────────────────────────────────
@config_bp.route('/<string:key>', methods=['PUT'])
@admin_required
def update_config_key(key):
    """Met à jour une clé de configuration."""
    try:
        data = request.get_json(silent=True) or {}
        if 'value' not in data:
            return jsonify({'success': False, 'error': "Champ 'value' requis"}), 400

        new_value = str(data['value'])

        _ensure_defaults()
        entry = Configuration.query.filter_by(cle=key).first()
        if not entry:
            if key not in CONFIG_DEFAULTS:
                return jsonify({'success': False, 'error': f"Clé '{key}' non reconnue"}), 404
            meta = CONFIG_DEFAULTS[key]
            entry = Configuration(
                cle=key,
                type_donnee=meta['type_donnee'],
                description=meta['description']
            )
            db.session.add(entry)

        entry.valeur = new_value
        entry.date_modification = datetime.utcnow()
        if hasattr(entry, 'admin_id') and hasattr(g, 'user_id'):
            entry.admin_id = g.user_id

        db.session.commit()
        logger.info(f"Config '{key}' mis à jour → '{new_value}' par user {getattr(g, 'user_id', '?')}")
        return jsonify({'success': True, 'data': _config_to_dict(entry)})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur PUT config/{key}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ──────────────────────────────────────────────
# POST /api/v1/config/batch
# ──────────────────────────────────────────────
@config_bp.route('/batch', methods=['POST'])
@admin_required
def batch_update_config():
    """Met à jour plusieurs clés en une seule requête.
    Body: {"updates": {"facial_threshold": 0.6, "max_attempts": 3, ...}}
    """
    try:
        data = request.get_json(silent=True) or {}
        updates = data.get('updates', {})
        if not updates:
            return jsonify({'success': False, 'error': "Champ 'updates' requis"}), 400

        _ensure_defaults()
        updated = []
        errors = []

        for key, value in updates.items():
            try:
                entry = Configuration.query.filter_by(cle=key).first()
                if not entry:
                    if key not in CONFIG_DEFAULTS:
                        errors.append(f"Clé inconnue: {key}")
                        continue
                    meta = CONFIG_DEFAULTS[key]
                    entry = Configuration(cle=key, type_donnee=meta['type_donnee'], description=meta['description'])
                    db.session.add(entry)

                entry.valeur = str(value)
                entry.date_modification = datetime.utcnow()
                if hasattr(entry, 'admin_id') and hasattr(g, 'user_id'):
                    entry.admin_id = g.user_id
                updated.append(key)
            except Exception as ex:
                errors.append(f"{key}: {ex}")

        db.session.commit()
        return jsonify({
            'success': True,
            'updated': updated,
            'errors': errors,
            'message': f"{len(updated)} clé(s) mise(s) à jour"
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur batch config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ──────────────────────────────────────────────
# POST /api/v1/config/reset
# ──────────────────────────────────────────────
@config_bp.route('/reset', methods=['POST'])
@admin_required
def reset_config():
    """Remet toutes les valeurs par défaut."""
    try:
        for key, meta in CONFIG_DEFAULTS.items():
            entry = Configuration.query.filter_by(cle=key).first()
            if entry:
                entry.valeur = meta['valeur']
                entry.date_modification = datetime.utcnow()
            else:
                entry = Configuration(
                    cle=key, valeur=meta['valeur'],
                    type_donnee=meta['type_donnee'],
                    description=meta['description'],
                    date_modification=datetime.utcnow()
                )
                db.session.add(entry)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Configuration réinitialisée'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erreur reset config: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ──────────────────────────────────────────────
# GET /api/v1/config/defaults
# ──────────────────────────────────────────────
@config_bp.route('/defaults', methods=['GET'])
@token_required
def get_defaults():
    """Retourne les valeurs par défaut de toutes les clés connues."""
    result = {}
    for key, meta in CONFIG_DEFAULTS.items():
        result[key] = _cast_value(meta['valeur'], meta['type_donnee'])
    return jsonify({'success': True, 'defaults': result})


# ──────────────────────────────────────────────
# GET /api/v1/config/history
# ──────────────────────────────────────────────
@config_bp.route('/history', methods=['GET'])
@token_required
def get_config_history():
    """
    Retourne l'historique des modifications de configuration.
    Utilise la table logs_acces (type_acces='config') comme source.
    """
    try:
        limit = min(int(request.args.get('limit', 20)), 100)
        from models.log import LogAcces
        from models.user import User

        logs = (
            LogAcces.query
            .filter(LogAcces.type_acces == 'config')
            .order_by(LogAcces.date_heure.desc())
            .limit(limit)
            .all()
        )
        history = []
        for log in logs:
            admin = db.session.get(User, log.utilisateur_id) if log.utilisateur_id else None
            details = log.details or {}
            history.append({
                'date':      log.date_heure.isoformat() if log.date_heure else None,
                'admin':     f"{admin.prenom} {admin.nom}" if admin else 'Système',
                'param':     details.get('key', details.get('param', '—')),
                'old_value': str(details.get('old_value', details.get('avant', '—'))),
                'new_value': str(details.get('new_value', details.get('apres', '—'))),
                'action':    log.statut or 'config',
            })
        return jsonify({'success': True, 'history': history, 'count': len(history)})
    except Exception as e:
        logger.error(f"Erreur GET config/history: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
