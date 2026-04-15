"""
Routes API pour les alertes
GET    /api/v1/alerts
GET    /api/v1/alerts/<alert_id>
PUT    /api/v1/alerts/<alert_id>
POST   /api/v1/alerts/<alert_id>/resolve
"""

from flask import Blueprint, request, g
from datetime import datetime
import logging

from core.database import db
from core.errors import ValidationError, NotFoundError
from api.middlewares.auth_middleware import token_required, admin_required
from api.response_handler import APIResponse

from models.log import Alerte

logger = logging.getLogger(__name__)

alerts_bp = Blueprint('alerts', __name__)


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


@alerts_bp.route('/<alert_id>', methods=['PUT'])
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
