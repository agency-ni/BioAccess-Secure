"""
Routes API pour les alertes
GET    /api/v1/alerts
GET    /api/v1/alerts/<alert_id>
PUT    /api/v1/alerts/<alert_id>
POST   /api/v1/alerts/<alert_id>/resolve
"""

from flask import Blueprint, request, g, current_app
from functools import wraps
from datetime import datetime
import logging

from core.database import db
from core.errors import ValidationError, NotFoundError, AuthenticationError, AuthorizationError
from core.security import SecurityManager
from api.middlewares.auth_middleware import token_required, admin_required, get_token_from_header
from api.response_handler import APIResponse

from models.log import Alerte

logger = logging.getLogger(__name__)

alerts_bp = Blueprint('alerts', __name__)


def admin_or_door_required(f):
    """
    Accepte soit un JWT Bearer admin soit un X-Admin-Token (door-system).
    Protège les endpoints appelés par le door-system ET le frontend admin.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. X-Admin-Token : authentification door-system
        x_admin_token = request.headers.get('X-Admin-Token', '')
        configured_token = current_app.config.get('ADMIN_TOKEN', '')
        if x_admin_token and configured_token and x_admin_token == configured_token:
            return f(*args, **kwargs)

        # 2. JWT Bearer : authentification frontend admin
        from models.user import User
        token = get_token_from_header()
        if not token:
            raise AuthenticationError("Authentification requise")

        payload = SecurityManager.decode_jwt_token(token)
        if not payload:
            raise AuthenticationError("Token invalide ou expiré")

        user = User.query.get(payload.get('user_id') or payload.get('sub'))
        if not user or not user.is_active:
            raise AuthenticationError("Utilisateur invalide")

        if user.role not in ['admin', 'super_admin']:
            raise AuthorizationError("Accès réservé aux administrateurs")

        g.user = user
        g.user_id = user.id
        g.user_role = user.role
        return f(*args, **kwargs)
    return decorated


@alerts_bp.route('', methods=['GET'])
@admin_required
def list_alerts():
    """
    Lister les alertes avec filtres
    
    GET /api/v1/alerts?page=1&per_page=10&type=securite&gravite=haute&traitee=false
    Response: { status, code, timestamp, message, data: [alerts...], meta: {...} }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        alert_type = request.args.get('type')
        gravite = request.args.get('gravite')
        traitee = request.args.get('traitee')
        
        # Limiter per_page
        per_page = min(per_page, 100)
        
        # Query
        query = Alerte.query
        
        # Filtres
        if alert_type:
            query = query.filter_by(type=alert_type)
        if gravite:
            query = query.filter_by(gravite=gravite)
        if traitee is not None:
            traitee_bool = traitee.lower() in ['true', '1', 'yes']
            query = query.filter_by(traitee=traitee_bool)
        
        # Trier par date décroissante
        query = query.order_by(Alerte.date_creation.desc())
        
        # Pagination
        paginated = query.paginate(page=page, per_page=per_page)
        
        alerts_data = [alert.to_dict() for alert in paginated.items]
        
        return APIResponse.paginated(
            alerts_data,
            paginated.total,
            page,
            per_page,
            "Alertes récupérées avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur listage alertes: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération des alertes",
            error_code="LIST_ALERTS_ERROR",
            status_code=500
        )


@alerts_bp.route('/<alert_id>', methods=['GET'])
@admin_required
def get_alert(alert_id):
    """
    Récupérer une alerte spécifique
    
    GET /api/v1/alerts/<alert_id>
    Response: { status, code, timestamp, message, data: {alert...} }
    """
    try:
        alert = Alerte.query.get(alert_id)
        if not alert:
            return APIResponse.error(
                "Alerte non trouvée",
                error_code="ALERT_NOT_FOUND",
                status_code=404
            )
        
        return APIResponse.success(
            alert.to_dict(),
            "Alerte récupérée avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur récupération alerte {alert_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="GET_ALERT_ERROR",
            status_code=500
        )


@alerts_bp.route('/<alert_id>', methods=['PATCH'])
@admin_required
def update_alert(alert_id):
    """
    Mettre à jour une alerte
    
    PUT /api/v1/alerts/<alert_id>
    Body: { commentaire?, assignee_id? }
    Response: { status, code, timestamp, message, data: {alert...} }
    """
    try:
        alert = Alerte.query.get(alert_id)
        if not alert:
            return APIResponse.error(
                "Alerte non trouvée",
                error_code="ALERT_NOT_FOUND",
                status_code=404
            )
        
        data = request.get_json() or {}
        
        if 'commentaire' in data:
            alert.commentaire = data['commentaire']
        
        if 'assignee_id' in data:
            alert.assignee_id = data['assignee_id']
        
        db.session.commit()
        
        return APIResponse.success(
            alert.to_dict(),
            "Alerte mise à jour avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur mise à jour alerte {alert_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la mise à jour",
            error_code="UPDATE_ALERT_ERROR",
            status_code=500
        )


@alerts_bp.route('/<alert_id>/resolve', methods=['POST'])
@admin_required
def resolve_alert(alert_id):
    """
    Marquer une alerte comme traitée
    
    POST /api/v1/alerts/<alert_id>/resolve
    Body: { commentaire? }
    Response: { status, code, timestamp, message, data: {alert...} }
    """
    try:
        alert = Alerte.query.get(alert_id)
        if not alert:
            return APIResponse.error(
                "Alerte non trouvée",
                error_code="ALERT_NOT_FOUND",
                status_code=404
            )
        
        alert.traitee = True
        alert.date_traitement = datetime.utcnow()
        alert.assignee_id = g.user_id
        
        data = request.get_json() or {}
        if 'commentaire' in data:
            alert.commentaire = data['commentaire']
        
        db.session.commit()
        
        return APIResponse.success(
            alert.to_dict(),
            "Alerte marquée comme résolue"
        )
    
    except Exception as e:
        logger.error(f"Erreur résolution alerte {alert_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la résolution",
            error_code="RESOLVE_ALERT_ERROR",
            status_code=500
        )


@alerts_bp.route('/stats', methods=['GET'])
@admin_required
def get_alerts_stats():
    """
    Récupérer les statistiques sur les alertes
    
    GET /api/v1/alerts/stats
    Response: { status, code, timestamp, message, data: {stats...} }
    """
    try:
        total_alerts = Alerte.query.count()
        pending_alerts = Alerte.query.filter_by(traitee=False).count()
        resolved_alerts = Alerte.query.filter_by(traitee=True).count()
        
        # Alertes par gravité
        by_gravite = {}
        for gravite_value in ['basse', 'moyenne', 'haute']:
            count = Alerte.query.filter_by(gravite=gravite_value).count()
            by_gravite[gravite_value] = count
        
        # Alertes par type
        by_type = {}
        for type_value in ['securite', 'systeme', 'tentative']:
            count = Alerte.query.filter_by(type=type_value).count()
            by_type[type_value] = count
        
        stats = {
            'total_alerts': total_alerts,
            'pending_alerts': pending_alerts,
            'resolved_alerts': resolved_alerts,
            'by_gravite': by_gravite,
            'by_type': by_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return APIResponse.success(
            stats,
            "Statistiques des alertes récupérées avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur statistiques alertes: {e}")
        return APIResponse.error(
            "Erreur lors du calcul des statistiques",
            error_code="STATS_ERROR",
            status_code=500
        )


# ============================================================
# ENDPOINTS CRITIQUES - Vérification d'accès
# ============================================================

@alerts_bp.route('/<alert_id>', methods=['PUT'])
@admin_required
def update_alert_access(alert_id):
    """
    Mettre à jour l'accès d'une alerte (ENDPOINT CRITIQUE)
    Permet d'autoriser/bloquer l'accès malgré une alerte active
    
    PUT /api/v1/alerts/{alert_id}
    Body:
        {
            "allow_access": true|false,
            "action": "autoriser|bloquer",  # Pour audit
            "notes": "Raison du changement"
        }
    
    Response: { success: true, data: {alert} }
    """
    try:
        alert = Alerte.query.get(alert_id)
        if not alert:
            return APIResponse.error(
                "Alerte non trouvée",
                error_code="ALERT_NOT_FOUND",
                status_code=404
            )
        
        data = request.get_json() or {}
        
        # Mettre à jour allow_access (CLEF)
        if 'allow_access' in data:
            alert.allow_access = bool(data.get('allow_access'))
            alert.access_modified_by = g.user_id
            alert.access_modified_at = datetime.utcnow()
            alert.admin_action = data.get('action', 'modification')
            alert.admin_notes = data.get('notes')
            
            logger.info(f"Accès alerte {alert_id} modifié par {g.user_id}: allow_access={alert.allow_access}")
        
        # Mettre à jour statut si fourni
        if 'statut' in data:
            alert.statut = data.get('statut')
        
        # Mettre à jour commentaire si fourni
        if 'commentaire' in data:
            alert.commentaire = data['commentaire']
        
        alert.updated_at = datetime.utcnow()
        db.session.commit()
        
        return APIResponse.success(
            alert.to_dict(),
            "Alerte mise à jour avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur mise à jour alerte {alert_id}: {e}")
        return APIResponse.error(
            str(e),
            error_code="UPDATE_ALERT_ERROR",
            status_code=500
        )


@alerts_bp.route('/access/check/<user_id>', methods=['GET'])
@admin_or_door_required
def check_user_access(user_id):
    """
    ENDPOINT CRITIQUE: Vérifier si un utilisateur peut accéder
    Appelé par Client Desktop et Door-System après authentification réussie
    
    GET /api/v1/alerts/access/check/{user_id}
    
    Response:
        {
            "success": true,
            "allowed": true|false,  # CLEF: true = accès autorisé
            "reason": "Aucune alerte de sécurité",
            "alert_id": "uuid ou null",
            "alert_title": "...",
            "resource_blocked": "poste-102"
        }
    """
    try:
        from models.user import User
        
        # Vérifier que l'utilisateur existe
        user = User.query.get(user_id)
        if not user:
            logger.warning(f"Tentative vérification accès utilisateur inexistant: {user_id}")
            return APIResponse.success({
                'allowed': False,
                'reason': 'Utilisateur non trouvé'
            }, status_code=200)
        
        # Chercher les alertes ACTIVES (non traitées) avec BLOCAGE
        active_blocked_alerts = Alerte.query.filter(
            Alerte.utilisateur_id == user_id,
            Alerte.traitee == False,
            Alerte.allow_access == False  # CLEF: Accès bloqué
        ).all()
        
        if active_blocked_alerts:
            # Accès BLOQUÉ - il y a une alerte active avec blocage
            alert = active_blocked_alerts[0]
            logger.warning(f"Accès bloqué pour {user_id}: alerte {alert.id}")
            return APIResponse.success({
                'allowed': False,  # BLOQUÉ
                'reason': 'Alerte de sécurité active',
                'alert_id': alert.id,
                'alert_title': alert.titre or alert.message,
                'resource_blocked': alert.resource,
                'timestamp': datetime.utcnow().isoformat()
            }, status_code=200)
        
        # Pas d'alerte active avec blocage - ACCÈS AUTORISÉ
        logger.info(f"Accès autorisé pour {user_id}: aucune alerte de blocage")
        return APIResponse.success({
            'allowed': True,  # AUTORISÉ
            'reason': 'Aucune alerte de sécurité',
            'timestamp': datetime.utcnow().isoformat()
        }, status_code=200)
        
    except Exception as e:
        logger.error(f"Erreur vérification accès {user_id}: {e}")
        # Fail-closed: en cas d'erreur, bloquer l'accès par défaut
        return APIResponse.success({
            'allowed': False,
            'reason': 'Erreur serveur - accès bloqué par défaut'
        }, status_code=200)


@alerts_bp.route('/access/status/<user_id>', methods=['GET'])
@admin_or_door_required
def get_access_status(user_id):
    """
    Alias pour check_user_access
    GET /api/v1/alerts/access/status/{user_id}
    """
    return check_user_access.__wrapped__(user_id)
