"""
Routes API pour l'administration biométrique
Endpoints pour gérer: utilisateurs, enregistrement, logs, alertes d'erreurs
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
from datetime import datetime, timedelta
import logging

from core.errors import ValidationError, AuthenticationError
from core.logger import log_audit
from api.middlewares.auth_middleware import token_required
from services.biometric_authentication_service import BiometricAuthenticationService
from services.biometric_enrollment_service import BiometricEnrollmentService
from services.audit_service import AuditService
from models.user import User
from models.biometric import AuthenticationAttempt, BiometricErrorLog
from core.database import db

logger = logging.getLogger(__name__)

# Create blueprint
admin_biometric_bp = Blueprint('admin_biometric', __name__, url_prefix='/admin/biometric')

# Services
auth_service = BiometricAuthenticationService()
enrollment_service = BiometricEnrollmentService()
audit_service = AuditService()


def admin_required(f):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.get('is_admin'):
            return jsonify({'success': False, 'message': 'Admin required'}), 403
        return f(*args, **kwargs)
    return decorated_function


# ============================================================
# DASHBOARD - Stats et Métriques
# ============================================================

@admin_biometric_bp.route('/dashboard', methods=['GET'])
@token_required
@admin_required
def get_dashboard_stats():
    """
    GET /api/v1/admin/biometric/dashboard
    Récupère les statistiques du dashboard admin
    """
    try:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count users
        total_users = User.query.filter_by(active=True).count()
        
        # Auth stats (last 24h)
        auth_24h = AuthenticationAttempt.query.filter(
            AuthenticationAttempt.timestamp >= datetime.now() - timedelta(hours=24)
        ).count()
        
        successful_24h = AuthenticationAttempt.query.filter(
            AuthenticationAttempt.timestamp >= datetime.now() - timedelta(hours=24),
            AuthenticationAttempt.success == True
        ).count()
        
        failed_24h = auth_24h - successful_24h
        success_rate = (successful_24h / auth_24h * 100) if auth_24h > 0 else 0
        
        # Error logs (last 24h)
        error_24h = BiometricErrorLog.query.filter(
            BiometricErrorLog.timestamp >= datetime.now() - timedelta(hours=24)
        ).count()

        return jsonify({
            'success': True,
            'admin_name': g.user_name or 'Administrator',
            'stats': {
                'total_users': total_users,
                'auth_24h': auth_24h,
                'successful_24h': successful_24h,
                'failed_24h': failed_24h,
                'errors_24h': error_24h,
                'success_rate': round(success_rate, 1)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# ENROLLMENT - Enregistrement utilisateur
# ============================================================

@admin_biometric_bp.route('/enroll-user', methods=['POST'])
@token_required
@admin_required
def enroll_new_user():
    """
    POST /api/v1/admin/biometric/enroll-user
    Enregistre un nouvel utilisateur avec données biométriques
    
    Body:
        {
            "email": "user@example.com",
            "first_name": "Jean",
            "last_name": "Dupont",
            "role": "user|admin|desktop_user",
            "face_image_base64": "data:image/jpeg;base64,...",
            "enrollment_mode": "upload|live",
            "require_biometric": true
        }
    """
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        email = data.get('email', '').strip().lower()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        role = data.get('role', 'user').lower()
        face_image = data.get('face_image_base64')
        enrollment_mode = data.get('enrollment_mode', 'upload')
        require_biometric = data.get('require_biometric', True)

        if not email or '@' not in email:
            return jsonify({'success': False, 'message': 'Email invalide'}), 400
        
        if role not in ['user', 'admin', 'desktop_user']:
            return jsonify({'success': False, 'message': 'Rôle invalide'}), 400
        
        if not face_image:
            return jsonify({'success': False, 'message': 'Image biométrique requise'}), 400

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Utilisateur déjà existant'}), 409

        # Create user
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            require_biometric=require_biometric,
            active=True
        )
        
        db.session.add(new_user)
        db.session.flush()  # Get the ID without committing

        # Enroll biometric
        enroll_result = enrollment_service.enroll_face_from_upload(
            user_id=str(new_user.id),
            image_data=face_image,
            label=f"Enregistrement admin - {datetime.now().strftime('%d/%m/%Y')}",
            check_duplicate=True
        )

        if not enroll_result.success:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': enroll_result.error or 'Erreur enregistrement facial'
            }), 400

        db.session.commit()

        # Log action
        audit_service.log_action(
            action='USER_BIOMETRIC_ENROLLED',
            user_id=str(new_user.id),
            details={
                'email': email,
                'role': role,
                'enrollment_mode': enrollment_mode,
                'enrolled_by': g.user_id
            }
        )

        return jsonify({
            'success': True,
            'message': f'Utilisateur {email} enregistré avec succès',
            'user_id': str(new_user.id),
            'template_count': 1
        }), 201
        
    except Exception as e:
        logger.error(f"User enrollment error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erreur serveur'}), 500


# ============================================================
# DESKTOP USERS - Gestion utilisateurs Desktop
# ============================================================

@admin_biometric_bp.route('/desktop-users', methods=['GET'])
@token_required
@admin_required
def get_desktop_users():
    """
    GET /api/v1/admin/biometric/desktop-users
    Liste tous les utilisateurs Desktop avec leurs stats
    """
    try:
        users = User.query.filter_by(role='desktop_user', active=True).all()
        
        result = []
        for user in users:
            last_auth = AuthenticationAttempt.query.filter_by(
                user_id=str(user.id), success=True
            ).order_by(AuthenticationAttempt.timestamp.desc()).first()
            
            template_count = len(user.biometric_templates) if hasattr(user, 'biometric_templates') else 0
            
            result.append({
                'id': str(user.id),
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'email': user.email,
                'is_active': user.active,
                'template_count': template_count,
                'last_auth': last_auth.timestamp.isoformat() if last_auth else None,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })

        return jsonify({
            'success': True,
            'users': result,
            'total': len(result)
        }), 200
        
    except Exception as e:
        logger.error(f"Desktop users error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# AUTH LOGS - Logs d'authentification
# ============================================================

@admin_biometric_bp.route('/auth-logs', methods=['GET'])
@token_required
@admin_required
def get_auth_logs():
    """
    GET /api/v1/admin/biometric/auth-logs
    Récupère les logs d'authentification avec filtres
    
    Query params:
        - email: Filter by user email
        - result: success|failed
        - auth_type: admin|desktop|web
        - page: Page number (default: 0)
        - per_page: Items per page (default: 25)
    """
    try:
        email_filter = request.args.get('email', '').strip().lower()
        result_filter = request.args.get('result', '').strip().lower()
        auth_type_filter = request.args.get('auth_type', '').strip().lower()
        page = int(request.args.get('page', 0))
        per_page = int(request.args.get('per_page', 25))

        query = AuthenticationAttempt.query
        
        # Apply filters
        if email_filter:
            query = query.filter(AuthenticationAttempt.user_email.ilike(f"%{email_filter}%"))
        
        if result_filter == 'success':
            query = query.filter_by(success=True)
        elif result_filter == 'failed':
            query = query.filter_by(success=False)
        
        if auth_type_filter and auth_type_filter in ['admin', 'desktop', 'web']:
            query = query.filter_by(auth_type=auth_type_filter)

        # Pagination
        total = query.count()
        logs = query.order_by(
            AuthenticationAttempt.timestamp.desc()
        ).limit(per_page).offset(page * per_page).all()

        result = []
        for log in logs:
            result.append({
                'id': str(log.id),
                'timestamp': log.timestamp.isoformat(),
                'user_email': log.user_email,
                'success': log.success,
                'similarity_score': log.similarity_score,
                'auth_type': log.auth_type,
                'client_ip': log.client_ip,
                'error_message': log.error_message
            })

        return jsonify({
            'success': True,
            'logs': result,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
            'has_next': (page + 1) * per_page < total
        }), 200
        
    except Exception as e:
        logger.error(f"Auth logs error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# ERROR ALERTS - Alertes d'erreurs Client Desktop
# ============================================================

@admin_biometric_bp.route('/error-alerts', methods=['GET'])
@token_required
@admin_required
def get_error_alerts():
    """
    GET /api/v1/admin/biometric/error-alerts
    Récupère les alertes d'erreurs d'authentification
    """
    try:
        # Critical errors (last 24h)
        critical_errors = BiometricErrorLog.query.filter(
            BiometricErrorLog.timestamp >= datetime.now() - timedelta(hours=24)
        ).order_by(
            BiometricErrorLog.timestamp.desc()
        ).limit(10).all()

        critical_list = []
        seen_error_types = {}
        
        for error in critical_errors:
            error_type = error.error_type
            if error_type not in seen_error_types:
                seen_error_types[error_type] = {
                    'error_type': error_type,
                    'message': error.error_message,
                    'severity': 'HIGH' if error.severity > 7 else ('MEDIUM' if error.severity > 4 else 'LOW'),
                    'occurrence_count': 0,
                    'last_timestamp': error.timestamp.isoformat()
                }
            seen_error_types[error_type]['occurrence_count'] += 1

        critical_list = list(seen_error_types.values())

        # Recent errors (all, paginated)
        recent_errors = BiometricErrorLog.query.filter(
            BiometricErrorLog.timestamp >= datetime.now() - timedelta(days=7)
        ).order_by(
            BiometricErrorLog.timestamp.desc()
        ).limit(50).all()

        recent_list = []
        for error in recent_errors:
            recent_list.append({
                'id': str(error.id),
                'timestamp': error.timestamp.isoformat(),
                'user_email': error.user_email,
                'error_type': error.error_type,
                'error_message': error.error_message,
                'client_info': error.client_info if isinstance(error.client_info, dict) else {},
                'resolved': error.resolved
            })

        return jsonify({
            'success': True,
            'critical_errors': critical_list,
            'recent_errors': recent_list
        }), 200
        
    except Exception as e:
        logger.error(f"Error alerts error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_biometric_bp.route('/log-client-error', methods=['POST'])
def log_client_error():
    """
    POST /api/v1/admin/biometric/log-client-error
    Enregistre une erreur d'authentification du Client Desktop
    (Pas besoin d'authentification pour permettre aux clients de signaler les erreurs)
    """
    try:
        data = request.get_json() or {}
        
        error_log = BiometricErrorLog(
            user_email=data.get('email', 'unknown'),
            error_type=data.get('error_type', 'UNKNOWN'),
            error_message=data.get('error_message', 'No message'),
            auth_type=data.get('auth_type', 'unknown'),
            client_info=data.get('client_info', {}),
            severity=5,  # Default severity
            timestamp=datetime.now()
        )
        
        db.session.add(error_log)
        db.session.commit()

        # Send alert to admin if critical
        if data.get('error_type') in ['CAMERA_ACCESS_DENIED', 'FACE_NOT_RECOGNIZED', 'CONNECTION_ERROR']:
            # TODO: Implement real-time notification to admin (WebSocket, Email, etc.)
            logger.warning(f"Critical biometric error: {data.get('error_type')} from {data.get('email')}")

        return jsonify({
            'success': True,
            'message': 'Erreur enregistrée'
        }), 201
        
    except Exception as e:
        logger.error(f"Error logging failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@admin_biometric_bp.route('/log-auth-attempt', methods=['POST'])
def log_auth_attempt():
    """
    POST /api/v1/admin/biometric/log-auth-attempt
    Enregistre une tentative d'authentification
    """
    try:
        data = request.get_json() or {}
        
        # This is logged automatically by the auth service,
        # but we accept it here for compatibility
        return jsonify({
            'success': True,
            'message': 'Tentative enregistrée'
        }), 201
        
    except Exception as e:
        logger.error(f"Attempt logging failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# ANALYTICS - Statistiques et analyses
# ============================================================

@admin_biometric_bp.route('/analytics', methods=['GET'])
@token_required
@admin_required
def get_analytics():
    """
    GET /api/v1/admin/biometric/analytics
    Récupère les statistiques détaillées et analyses
    """
    try:
        # Last 7 days data
        days_data = {}
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            date_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            date_end = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            success_count = AuthenticationAttempt.query.filter(
                AuthenticationAttempt.timestamp.between(date_start, date_end),
                AuthenticationAttempt.success == True
            ).count()
            
            failed_count = AuthenticationAttempt.query.filter(
                AuthenticationAttempt.timestamp.between(date_start, date_end),
                AuthenticationAttempt.success == False
            ).count()
            
            days_data[i] = {'success': success_count, 'failed': failed_count}

        # Error frequency
        error_analysis = db.session.query(
            BiometricErrorLog.error_type,
            db.func.count(BiometricErrorLog.id).label('count')
        ).group_by(BiometricErrorLog.error_type).all()

        total_success = sum(d['success'] for d in days_data.values())
        total_failed = sum(d['failed'] for d in days_data.values())

        return jsonify({
            'success': True,
            'trend_labels': [f"J-{i}" for i in range(7)],
            'trend_success': [days_data[i]['success'] for i in range(7)],
            'trend_failed': [days_data[i]['failed'] for i in range(7)],
            'success_count': total_success,
            'failed_count': total_failed,
            'error_analysis': [
                {'error_type': e[0], 'count': e[1]} for e in error_analysis
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# QUALITY ANALYSIS - Analyse qualité image
# ============================================================

@admin_biometric_bp.route('/analyze-quality', methods=['POST'])
@token_required
def analyze_image_quality():
    """
    POST /api/v1/admin/biometric/analyze-quality
    Analyse la qualité d'une image biométrique
    """
    try:
        data = request.get_json() or {}
        image_base64 = data.get('image_base64')

        if not image_base64:
            return jsonify({'success': False, 'message': 'Image requise'}), 400

        # Use biometric service to analyze
        quality_score = enrollment_service.analyze_image_quality(image_base64)

        return jsonify({
            'success': True,
            'quality_score': quality_score,
            'acceptable': quality_score > 0.6
        }), 200
        
    except Exception as e:
        logger.error(f"Quality analysis error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================
# ERROR MANAGEMENT
# ============================================================

@admin_biometric_bp.route('/alert-error', methods=['POST'])
@token_required
def alert_error():
    """
    POST /api/v1/admin/biometric/alert-error
    Notify user of a critical error
    """
    try:
        data = request.get_json() or {}
        error_id = data.get('error_id')
        
        if not error_id:
            return jsonify({'success': False, 'message': 'error_id requis'}), 400
        
        error_log = BiometricErrorLog.query.get(error_id)
        if not error_log:
            return jsonify({'success': False, 'message': 'Erreur non trouvée'}), 404
        
        # Send notification to user
        from services.email_service import EmailService
        email_service = EmailService()
        
        try:
            email_service.send_error_alert(
                error_log.user_email,
                error_log.error_type,
                error_log.error_message
            )
        except Exception as e:
            logger.error(f"Error sending alert: {str(e)}")
        
        # Log action
        log_audit('error_alert_sent', g.user.id, request.remote_addr, 
                 {'error_id': error_id, 'user_email': error_log.user_email})
        
        return jsonify({
            'success': True,
            'message': 'Alerte envoyée à l\'utilisateur'
        }), 200
        
    except Exception as e:
        logger.error(f"Alert error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_biometric_bp.route('/resolve-error', methods=['POST'])
@token_required
def resolve_error():
    """
    POST /api/v1/admin/biometric/resolve-error
    Mark error as resolved
    """
    try:
        data = request.get_json() or {}
        error_id = data.get('error_id')
        admin_notes = data.get('admin_notes', '')
        
        if not error_id:
            return jsonify({'success': False, 'message': 'error_id requis'}), 400
        
        error_log = BiometricErrorLog.query.get(error_id)
        if not error_log:
            return jsonify({'success': False, 'message': 'Erreur non trouvée'}), 404
        
        # Mark as resolved
        error_log.resolved = True
        error_log.resolved_at = datetime.utcnow()
        error_log.admin_notes = admin_notes
        db.session.commit()
        
        # Log action
        log_audit('error_resolved', g.user.id, request.remote_addr, 
                 {'error_id': error_id, 'notes': admin_notes})
        
        return jsonify({
            'success': True,
            'message': 'Erreur marquée comme résolue',
            'error': error_log.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Resolve error: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
