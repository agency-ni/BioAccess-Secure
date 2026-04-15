"""
Routes API pour les logs d'accès
GET    /api/v1/logs
GET    /api/v1/logs/<log_id>
GET    /api/v1/logs/user/<user_id>
"""

from flask import Blueprint, request, g
from datetime import datetime, timedelta
import logging

from core.database import db
from core.errors import ValidationError, NotFoundError
from api.middlewares.auth_middleware import token_required, admin_required
from api.response_handler import APIResponse

from models.log import LogAcces

logger = logging.getLogger(__name__)

logs_bp = Blueprint('logs', __name__)


@logs_bp.route('', methods=['GET'])
@admin_required
def list_logs():
    """
    Lister les logs d'accès avec filtres
    
    GET /api/v1/logs?page=1&per_page=10&type_acces=poste&statut=succes&days=7
    Response: { status, code, timestamp, message, data: [logs...], meta: {...} }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        type_acces = request.args.get('type_acces')
        statut = request.args.get('statut')
        days = request.args.get('days', 30, type=int)
        user_id = request.args.get('user_id')
        
        # Limiter per_page
        per_page = min(per_page, 100)
        
        # Filtrer par date
        since = datetime.utcnow() - timedelta(days=days)
        query = LogAcces.query.filter(LogAcces.date_heure >= since)
        
        # Filtres additionnels
        if type_acces:
            query = query.filter_by(type_acces=type_acces)
        if statut:
            query = query.filter_by(statut=statut)
        if user_id:
            query = query.filter_by(utilisateur_id=user_id)
        
        # Trier par date décroissante
        query = query.order_by(LogAcces.date_heure.desc())
        
        # Pagination
        paginated = query.paginate(page=page, per_page=per_page)
        
        logs_data = [log.to_dict() for log in paginated.items]
        
        return APIResponse.paginated(
            logs_data,
            paginated.total,
            page,
            per_page,
            "Logs récupérés avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur listage logs: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération des logs",
            error_code="LIST_LOGS_ERROR",
            status_code=500
        )


@logs_bp.route('/<log_id>', methods=['GET'])
@admin_required
def get_log(log_id):
    """
    Récupérer un log spécifique
    
    GET /api/v1/logs/<log_id>
    Response: { status, code, timestamp, message, data: {log...} }
    """
    try:
        log = LogAcces.query.get(log_id)
        if not log:
            return APIResponse.error(
                "Log non trouvé",
                error_code="LOG_NOT_FOUND",
                status_code=404
            )
        
        return APIResponse.success(
            log.to_dict(),
            "Log récupéré avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur récupération log {log_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="GET_LOG_ERROR",
            status_code=500
        )


@logs_bp.route('/user/<user_id>', methods=['GET'])
@token_required
def get_user_logs(user_id):
    """
    Récupérer les logs d'un utilisateur
    
    GET /api/v1/logs/user/<user_id>
    Response: { status, code, timestamp, message, data: [logs...], meta: {...} }
    """
    try:
        # Vérifier permissions (self ou admin)
        if g.user_id != user_id and g.user_role not in ['admin', 'super_admin']:
            return APIResponse.error(
                "Accès refusé",
                error_code="ACCESS_DENIED",
                status_code=403
            )
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        days = request.args.get('days', 30, type=int)
        
        per_page = min(per_page, 100)
        
        since = datetime.utcnow() - timedelta(days=days)
        
        query = LogAcces.query.filter(
            LogAcces.utilisateur_id == user_id,
            LogAcces.date_heure >= since
        ).order_by(LogAcces.date_heure.desc())
        
        paginated = query.paginate(page=page, per_page=per_page)
        logs_data = [log.to_dict() for log in paginated.items]
        
        return APIResponse.paginated(
            logs_data,
            paginated.total,
            page,
            per_page,
            "Logs utilisateur récupérés avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur récupération logs utilisateur {user_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="GET_USER_LOGS_ERROR",
            status_code=500
        )


@logs_bp.route('/stats', methods=['GET'])
@admin_required
def get_logs_stats():
    """
    Récupérer les statistiques sur les logs
    
    GET /api/v1/logs/stats?days=7
    Response: { status, code, timestamp, message, data: {stats...} }
    """
    try:
        days = request.args.get('days', 7, type=int)
        since = datetime.utcnow() - timedelta(days=days)
        
        total_logs = LogAcces.query.filter(LogAcces.date_heure >= since).count()
        success_logs = LogAcces.query.filter(
            LogAcces.date_heure >= since,
            LogAcces.statut == 'succes'
        ).count()
        failure_logs = total_logs - success_logs
        success_rate = (success_logs / total_logs * 100) if total_logs > 0 else 0
        
        stats = {
            'total_logs': total_logs,
            'success_logs': success_logs,
            'failure_logs': failure_logs,
            'success_rate': round(success_rate, 2),
            'period_days': days,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return APIResponse.success(
            stats,
            "Statistiques des logs récupérées avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur statistiques logs: {e}")
        return APIResponse.error(
            "Erreur lors du calcul des statistiques",
            error_code="STATS_ERROR",
            status_code=500
        )
