"""
Routes du dashboard
GET    /api/v1/dashboard/kpis
GET    /api/v1/dashboard/activity
GET    /api/v1/dashboard/alerts/recent
GET    /api/v1/dashboard/top-failures
GET    /api/v1/dashboard/health
GET    /api/v1/dashboard/recent-logins
"""

from flask import Blueprint, request, g, jsonify, current_app
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
    
    # Variation tentatives par rapport à hier
    yesterday = today - timedelta(days=1)
    attempts_yesterday = LogAcces.query.filter(
        LogAcces.date_heure >= yesterday,
        LogAcces.date_heure < today
    ).count()

    variation = 0
    if attempts_yesterday > 0:
        variation = round(
            ((attempts_today - attempts_yesterday) / attempts_yesterday) * 100, 1
        )

    # Variation employés par rapport au mois dernier
    last_month = today - timedelta(days=30)
    employees_last_month = User.query.filter(
        User.is_active == True,
        User.role == 'employe',
        User.date_creation <= last_month
    ).count()
    employees_variation = total_employees - employees_last_month

    # Variation alertes par rapport à hier
    alerts_yesterday = Alerte.query.filter(
        Alerte.date_creation >= yesterday,
        Alerte.date_creation < today,
        Alerte.traitee == False
    ).count()
    alerts_today_new = Alerte.query.filter(
        Alerte.date_creation >= today,
        Alerte.traitee == False
    ).count()
    alerts_variation = alerts_today_new - alerts_yesterday

    return jsonify({
        'total_employees': total_employees,
        'employees_variation': f"{employees_variation:+d}",
        'attempts_today': attempts_today,
        'attempts_variation': f"{variation:+.1f}%",
        'success_rate': success_rate,
        'success_target': 95,
        'pending_alerts': pending_alerts,
        'alerts_variation': f"{alerts_variation:+d}"
    })

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
    
    return jsonify([a.to_dict() for a in alerts])

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
    
    return jsonify(result)

@dashboard_bp.route('/health', methods=['GET'])
@token_required
def get_system_health():
    """Statut des différents composants système"""
    
    # Vérifier la base de données
    db_status = 'healthy'
    try:
        db.session.execute(db.text('SELECT 1'))
    except:
        db_status = 'unhealthy'
    
    # Simuler les autres composants
    return jsonify([
        {'name': 'Serveur', 'status': 'healthy', 'color': 'green'},
        {'name': 'Base données', 'status': db_status, 'color': 'green' if db_status == 'healthy' else 'red'},
        {'name': 'API', 'status': 'healthy', 'color': 'green'},
        {'name': 'Borne 1', 'status': 'unknown', 'color': 'gray'},
    ])

@dashboard_bp.route('/recent-logins', methods=['GET'])
@admin_required
def get_recent_admin_logins():
    """Dernières connexions admin"""
    try:
        recent = LoginLog.query.filter(
            LoginLog.success.is_(True)
        ).order_by(
            desc(LoginLog.timestamp)
        ).limit(5).all()

        result = []
        for log in recent:
            user = db.session.get(User, log.user_id) if log.user_id else None
            result.append({
                'admin': user.full_name if user else (log.email or 'Inconnu'),
                'date': log.timestamp.isoformat() if log.timestamp else None,
                'ip': log.ip_address or '',
                'status': 'success'
            })

        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Erreur recent-logins: {e}", exc_info=True)
        return jsonify([])