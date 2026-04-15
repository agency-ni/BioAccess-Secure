"""
Routes API pour l'audit des accès
GET    /api/v1/audit/logs
GET    /api/v1/audit/report
POST   /api/v1/audit/export
"""

from flask import Blueprint, request, g, send_file
from datetime import datetime, timedelta
import logging
import json
import io

from core.database import db
from core.errors import ValidationError
from api.middlewares.auth_middleware import token_required, admin_required
from api.response_handler import APIResponse

from models.log import LogAcces, Alerte
from models.user import User, LoginLog

logger = logging.getLogger(__name__)

audit_bp = Blueprint('audit', __name__)


@audit_bp.route('/logs', methods=['GET'])
@admin_required
def get_audit_logs():
    """
    Récupérer les logs d'audit complets
    
    GET /api/v1/audit/logs?page=1&per_page=10&days=7&user_id=...
    Response: { status, code, timestamp, message, data: [logs...], meta: {...} }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        days = request.args.get('days', 7, type=int)
        user_id = request.args.get('user_id')
        
        per_page = min(per_page, 100)
        
        # Date limite
        since = datetime.utcnow() - timedelta(days=days)
        
        # Query LogAcces
        query = LogAcces.query.filter(LogAcces.date_heure >= since)
        
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
            "Logs d'audit récupérés avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur récupération logs audit: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="GET_AUDIT_LOGS_ERROR",
            status_code=500
        )


@audit_bp.route('/login-logs', methods=['GET'])
@admin_required
def get_login_logs():
    """
    Récupérer l'historique des tentatives de connexion
    
    GET /api/v1/audit/login-logs?page=1&per_page=10&days=7&email=...
    Response: { status, code, timestamp, message, data: [logs...], meta: {...} }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        days = request.args.get('days', 7, type=int)
        email = request.args.get('email')
        success = request.args.get('success')
        
        per_page = min(per_page, 100)
        
        # Date limite
        since = datetime.utcnow() - timedelta(days=days)
        
        # Query
        query = LoginLog.query.filter(LoginLog.timestamp >= since)
        
        if email:
            query = query.filter_by(email=email.lower())
        
        if success is not None:
            success_bool = success.lower() in ['true', '1', 'yes']
            query = query.filter_by(success=success_bool)
        
        # Trier par date décroissante
        query = query.order_by(LoginLog.timestamp.desc())
        
        # Pagination
        paginated = query.paginate(page=page, per_page=per_page)
        
        logs_data = [log.to_dict() for log in paginated.items]
        
        return APIResponse.paginated(
            logs_data,
            paginated.total,
            page,
            per_page,
            "Logs de connexion récupérés avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur récupération login logs: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="GET_LOGIN_LOGS_ERROR",
            status_code=500
        )


@audit_bp.route('/report', methods=['GET'])
@admin_required
def get_audit_report():
    """
    Générer un rapport d'audit complet
    
    GET /api/v1/audit/report?days=7
    Response: { status, code, timestamp, message, data: {report...} }
    """
    try:
        days = request.args.get('days', 7, type=int)
        since = datetime.utcnow() - timedelta(days=days)
        
        # Statistiques d'accès
        total_logs = LogAcces.query.filter(LogAcces.date_heure >= since).count()
        success_logs = LogAcces.query.filter(
            LogAcces.date_heure >= since,
            LogAcces.statut == 'succes'
        ).count()
        failure_logs = total_logs - success_logs
        
        # Statistiques d'alertes
        total_alerts = Alerte.query.count()
        pending_alerts = Alerte.query.filter_by(traitee=False).count()
        
        # Top utilisateurs actifs
        active_users = db.session.query(
            User.id,
            User.email,
            User.nom,
            db.func.count(LogAcces.id).label('log_count')
        ).outerjoin(
            LogAcces,
            LogAcces.utilisateur_id == User.id
        ).filter(
            LogAcces.date_heure >= since
        ).group_by(
            User.id
        ).order_by(
            db.func.count(LogAcces.id).desc()
        ).limit(10).all()
        
        active_users_data = [
            {'user_id': u[0], 'email': u[1], 'name': u[2], 'access_count': u[3]}
            for u in active_users
        ]
        
        report = {
            'period_start': since.isoformat(),
            'period_end': datetime.utcnow().isoformat(),
            'period_days': days,
            'access_stats': {
                'total_logs': total_logs,
                'success_logs': success_logs,
                'failure_logs': failure_logs,
                'success_rate': round((success_logs / total_logs * 100) if total_logs > 0 else 0, 2)
            },
            'alert_stats': {
                'total_alerts': total_alerts,
                'pending_alerts': pending_alerts,
                'resolved_alerts': total_alerts - pending_alerts
            },
            'top_active_users': active_users_data,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return APIResponse.success(
            report,
            "Rapport d'audit généré avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur génération rapport: {e}")
        return APIResponse.error(
            "Erreur lors de la génération du rapport",
            error_code="REPORT_ERROR",
            status_code=500
        )


@audit_bp.route('/export', methods=['POST'])
@admin_required
def export_audit():
    """
    Exporter les logs d'audit en JSON ou CSV
    
    POST /api/v1/audit/export
    Body: { format: "json|csv", days: 7 }
    Response: Fichier téléchargeable
    """
    try:
        data = request.get_json() or {}
        export_format = data.get('format', 'json').lower()
        days = data.get('days', 7)
        
        if export_format not in ['json', 'csv']:
            return APIResponse.error(
                "Format invalide (json ou csv)",
                error_code="INVALID_FORMAT",
                status_code=400
            )
        
        since = datetime.utcnow() - timedelta(days=days)
        logs = LogAcces.query.filter(LogAcces.date_heure >= since).all()
        
        if export_format == 'json':
            logs_data = [log.to_dict() for log in logs]
            content = json.dumps(logs_data, indent=2, default=str)
            filename = f"audit_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            mimetype = 'application/json'
        
        else:  # csv
            import csv
            output = io.StringIO()
            
            if logs:
                fieldnames = logs[0].to_dict().keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for log in logs:
                    writer.writerow(log.to_dict())
            
            content = output.getvalue()
            filename = f"audit_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            mimetype = 'text/csv'
        
        # Créer le fichier en memoire
        file_data = io.BytesIO(content.encode('utf-8'))
        
        return send_file(
            file_data,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        logger.error(f"Erreur export audit: {e}")
        return APIResponse.error(
            "Erreur lors de l'export",
            error_code="EXPORT_ERROR",
            status_code=500
        )
