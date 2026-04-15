"""
Routes du dashboard
GET    /api/v1/dashboard/kpis
GET    /api/v1/dashboard/activity
GET    /api/v1/dashboard/alerts/recent
GET    /api/v1/dashboard/top-failures
GET    /api/v1/dashboard/health
GET    /api/v1/dashboard/recent-logins
"""

from flask import Blueprint, request, g
from datetime import datetime, timedelta
from sqlalchemy import func, desc

from core.database import db
from core.errors import ValidationError
from api.middlewares.auth_middleware import token_required, admin_required

from models.user import User, LoginLog
from models.log import LogAcces, Alerte

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/kpis', methods=['GET'])
@token_required
def get_kpis():
    """Récupère les KPIs principaux pour le dashboard"""
    
    # Total employés actifs
    total_employees = User.query.filter_by(
        is_active=True,
        role='employe'
    ).count()
    
    # Tentatives aujourd'hui
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)
    
    attempts_today = LogAcces.query.filter(
        LogAcces.date_heure >= today,
        LogAcces.date_heure < tomorrow
    ).count()
    
    # Taux de succès
    success_today = LogAcces.query.filter(
        LogAcces.date_heure >= today,
        LogAcces.date_heure < tomorrow,
        LogAcces.statut == 'succes'
    ).count()
    
    success_rate = 0
    if attempts_today > 0:
        success_rate = round((success_today / attempts_today) * 100, 1)
    
    # Alertes non traitées
    pending_alerts = Alerte.query.filter_by(traitee=False).count()
    
    # Variation par rapport à hier
    yesterday = today - timedelta(days=1)
    attempts_yesterday = LogAcces.query.filter(
        LogAcces.date_heure >= yesterday,
        LogAcces.date_heure < today
    ).count()
    
    variation = 0
    if attempts_yesterday > 0:
        variation = round(
            ((attempts_today - attempts_yesterday) / attempts_yesterday) * 100,
            1
        )
    
    return {
        'total_employees': total_employees,
        'employees_variation': '+3',  # À calculer réellement
        'attempts_today': attempts_today,
        'attempts_variation': f"{variation:+.1f}%",
        'success_rate': success_rate,
        'success_target': 95,
        'pending_alerts': pending_alerts,
        'alerts_variation': '+2'  # À calculer réellement
    }

@dashboard_bp.route('/activity', methods=['GET'])
@token_required
def get_activity():
    """Graphique d'activité sur 7/30 jours"""
    days = request.args.get('days', 7, type=int)
    
    if days not in [7, 30, 90]:
        raise ValidationError("days doit être 7, 30 ou 90")
    
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days-1)
    
    # Préparer les dates
    dates = [(start_date + timedelta(days=i)) for i in range(days)]
    
    result = []
    for date in dates:
        next_day = date + timedelta(days=1)
        
        attempts = LogAcces.query.filter(
            LogAcces.date_heure >= date,
            LogAcces.date_heure < next_day
        ).count()
        
        successes = LogAcces.query.filter(
            LogAcces.date_heure >= date,
            LogAcces.date_heure < next_day,
            LogAcces.statut == 'succes'
        ).count()
        
        result.append({
            'date': date.isoformat(),
            'attempts': attempts,
            'successes': successes
        })
    
    return {
        'labels': [d.strftime('%d/%m') for d in dates],
        'attempts': [r['attempts'] for r in result],
        'successes': [r['successes'] for r in result]
    }

@dashboard_bp.route('/alerts/recent', methods=['GET'])
@token_required
def get_recent_alerts():
    """Récupère les 5 dernières alertes"""
    alerts = Alerte.query.order_by(
        desc(Alerte.date_creation)
    ).limit(5).all()
    
    return [a.to_dict() for a in alerts]

@dashboard_bp.route('/top-failures', methods=['GET'])
@token_required
def get_top_failures():
    """Top 5 utilisateurs avec le plus d'échecs"""
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    failures = db.session.query(
        User.id,
        User.nom,
        User.prenom,
        User.departement,
        func.count(LogAcces.id).label('fail_count')
    ).join(
        LogAcces,
        LogAcces.utilisateur_id == User.id
    ).filter(
        LogAcces.statut == 'echec',
        LogAcces.date_heure >= thirty_days_ago
    ).group_by(
        User.id
    ).order_by(
        desc('fail_count')
    ).limit(5).all()
    
    max_fail = failures[0].fail_count if failures else 1
    
    result = []
    for f in failures:
        result.append({
            'id': f.id,
            'name': f"{f.prenom} {f.nom}",
            'departement': f.departement,
            'failures': f.fail_count,
            'percentage': round((f.fail_count / max_fail) * 100)
        })
    
    return result

@dashboard_bp.route('/health', methods=['GET'])
@token_required
def get_system_health():
    """Statut des différents composants système"""
    
    # Vérifier la base de données
    db_status = 'healthy'
    try:
        db.session.execute('SELECT 1')
    except:
        db_status = 'unhealthy'
    
    # Simuler les autres composants
    return [
        {'name': 'Serveur', 'status': 'healthy', 'color': 'green'},
        {'name': 'Base données', 'status': db_status, 'color': 'green' if db_status == 'healthy' else 'red'},
        {'name': 'API', 'status': 'healthy', 'color': 'green'},
        {'name': 'Borne 1', 'status': 'degraded', 'color': 'yellow'},
    ]

@dashboard_bp.route('/recent-logins', methods=['GET'])
@admin_required
def get_recent_admin_logins():
    """Dernières connexions admin"""
    recent = LoginLog.query.filter(
        LoginLog.success == True
    ).order_by(
        desc(LoginLog.created_at)
    ).limit(5).all()
    
    result = []
    for log in recent:
        user = User.query.get(log.user_id) if log.user_id else None
        result.append({
            'admin': user.full_name if user else 'Inconnu',
            'date': log.created_at.isoformat(),
            'ip': log.ip_address,
            'status': 'success'
        })
    
    return result