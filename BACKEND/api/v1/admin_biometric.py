"""
Routes API pour l'administration biométrique
Endpoints pour gérer: utilisateurs, enregistrement, logs, alertes d'erreurs
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
from datetime import datetime, timedelta
import logging

from core.logger import log_audit
from api.middlewares.auth_middleware import token_required
from api.middlewares.rate_limiter import limiter
from services.biometric_authentication_service import BiometricAuthenticationService
from services.biometric_enrollment_service import BiometricEnrollmentService
from services.audit_service import AuditService
from models.user import User
from models.biometric import AuthenticationAttempt, BiometricErrorLog, TemplateBiometrique
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
        if g.get('user_role') not in ['admin', 'super_admin']:
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
        total_users = User.query.filter_by(is_active=True).count()
        
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
            'admin_name': g.user.full_name if g.get('user') else 'Administrator',
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

        # Create user (champs conformes au modèle User)
        new_user = User(
            email=email,
            prenom=first_name,
            nom=last_name,
            role=role,
            is_active=True
        )
        new_user.set_password(User.generate_employee_id())  # mot de passe temporaire
        new_user.employee_id = User.generate_employee_id()
        new_user.employee_id_created_at = datetime.now()
        
        db.session.add(new_user)
        db.session.flush()  # Get the ID without committing

        # Enroll biometric (face_image est une chaîne base64)
        enroll_result = enrollment_service.enroll_face_from_base64(
            user_id=str(new_user.id),
            image_base64=face_image,
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
# ENROLL FACIAL - Enrôlement facial pour utilisateur existant
# ============================================================

@admin_biometric_bp.route('/enroll/face', methods=['POST'])
@token_required
@admin_required
def enroll_face():
    """
    POST /api/v1/admin/enroll/face
    Enrôle un utilisateur avec donnée faciale
    
    Body:
        {
            "user_id": "uuid-of-user",
            "image_b64": "base64-encoded-jpeg"
        }
    """
    try:
        data = request.get_json() or {}
        user_id   = data.get('user_id', '').strip()
        image_b64 = data.get('image_b64', '').strip()
        liveness_confirmed = bool(data.get('liveness_confirmed', True))
        ear_min            = data.get('ear_min', None)

        # Validation
        if not user_id or not image_b64:
            return jsonify({
                'success': False,
                'error': 'user_id et image_b64 obligatoires',
                'code': 'MISSING_FIELDS'
            }), 400
        
        # Vérifier que l'utilisateur existe
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Utilisateur non trouvé',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # Vérifier liveness avant enrôlement
        from services.biometric_service import BiometricService as _BS
        alive, liveness_err = _BS.verify_liveness(liveness_confirmed, ear_min)
        if not alive:
            return jsonify({
                'success': False,
                'error': liveness_err or 'Détection de vivant échouée',
                'code': 'LIVENESS_FAILED'
            }), 400

        # Enrôler le visage (image_b64 = chaîne base64 → méthode dédiée)
        enroll_result = enrollment_service.enroll_face_from_base64(
            user_id=user_id,
            image_base64=image_b64,
            label=f"Enrôlement facial admin - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            check_duplicate=True
        )
        
        if not enroll_result.success:
            return jsonify({
                'success': False,
                'error': enroll_result.error or 'Erreur enrôlement facial',
                'code': 'ENROLLMENT_FAILED'
            }), 400
        
        # Journaliser
        audit_service.log_action(
            action='FACE_ENROLLED',
            user_id=user_id,
            details={
                'email': user.email,
                'enrolled_by': g.user_id,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Enrôlement facial réussi pour {user.email}',
            'user_id': user_id,
            'quality_score': enroll_result.quality_score if hasattr(enroll_result, 'quality_score') else None
        }), 200

    except Exception as e:
        logger.error(f"Face enrollment error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur: ' + str(e),
            'code': 'SERVER_ERROR'
        }), 500


# ============================================================
# ENROLL VOCAL - Enrôlement vocal pour utilisateur existant
# ============================================================

@admin_biometric_bp.route('/enroll/voice', methods=['POST'])
@token_required
@admin_required
def enroll_voice():
    """
    POST /api/v1/admin/enroll/voice
    Enrôle un utilisateur avec donnée vocale
    
    Body:
        {
            "user_id": "uuid-of-user",
            "audio_b64": "base64-encoded-wav"
        }
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id', '').strip()
        audio_b64 = data.get('audio_b64', '').strip()
        
        # Validation
        if not user_id or not audio_b64:
            return jsonify({
                'success': False,
                'error': 'user_id et audio_b64 obligatoires',
                'code': 'MISSING_FIELDS'
            }), 400
        
        # Vérifier que l'utilisateur existe
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({
                'success': False,
                'error': 'Utilisateur non trouvé',
                'code': 'USER_NOT_FOUND'
            }), 404
        
        # Enrôler la voix (utiliser BiometricService directement)
        from services.biometric_service import BiometricService
        import base64

        try:
            # Décoder le base64 audio
            audio_data = base64.b64decode(audio_b64)
            
            # Créer et persister le template vocal (process_voice_sample commit en interne)
            vocal_template = BiometricService.process_voice_sample(
                audio_data=audio_data,
                user_id=user_id,
                phrase_text=None
            )

            if not vocal_template:
                return jsonify({
                    'success': False,
                    'error': "Impossible de traiter l'audio",
                    'code': 'AUDIO_PROCESSING_FAILED'
                }), 400
            
        except Exception as e:
            logger.error(f"Voice template creation error: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Erreur création template vocal: ' + str(e),
                'code': 'TEMPLATE_CREATION_FAILED'
            }), 400
        
        # Journaliser
        audit_service.log_action(
            action='VOICE_ENROLLED',
            user_id=user_id,
            details={
                'email': user.email,
                'enrolled_by': g.user_id,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return jsonify({
            'success': True,
            'message': f'Enrôlement vocal réussi pour {user.email}',
            'user_id': user_id,
            'quality_score': None
        }), 200
        
    except Exception as e:
        logger.error(f"Voice enrollment error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur: ' + str(e),
            'code': 'SERVER_ERROR'
        }), 500


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
        users = User.query.filter_by(role='desktop_user', is_active=True).all()

        result = []
        for user in users:
            last_auth = AuthenticationAttempt.query.filter_by(
                user_id=str(user.id), success=True
            ).order_by(AuthenticationAttempt.timestamp.desc()).first()

            template_count = user.templates.count() if hasattr(user, 'templates') else 0

            result.append({
                'id': str(user.id),
                'full_name': user.full_name,
                'email': user.email,
                'is_active': user.is_active,
                'template_count': template_count,
                'last_auth': last_auth.timestamp.isoformat() if last_auth else None,
                'created_at': user.date_creation.isoformat() if user.date_creation else None
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
            query = query.filter(AuthenticationAttempt.email.ilike(f"%{email_filter}%"))

        if result_filter == 'success':
            query = query.filter_by(success=True)
        elif result_filter == 'failed':
            query = query.filter_by(success=False)

        if auth_type_filter == 'admin':
            query = query.filter_by(is_admin_attempt=True)
        elif auth_type_filter in ['desktop', 'web']:
            query = query.filter_by(is_admin_attempt=False)

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
                'user_email': log.email,
                'success': log.success,
                'similarity_score': log.similarity_score,
                'auth_type': 'admin' if log.is_admin_attempt else 'user',
                'client_ip': log.ip_address,
                'reason': log.reason
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
@limiter.limit("10 per minute")
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
        
        error_log = db.session.get(BiometricErrorLog, error_id)
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
        
        error_log = db.session.get(BiometricErrorLog, error_id)
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


@admin_biometric_bp.route('/<user_id>/templates', methods=['DELETE'])
@token_required
@admin_required
def delete_user_templates(user_id):
    """
    DELETE /api/v1/admin/biometric/<user_id>/templates
    Supprime tous les templates biométriques d'un utilisateur (action admin)
    """
    try:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'success': False, 'message': 'Utilisateur non trouvé'}), 404

        deleted = TemplateBiometrique.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        log_audit('admin_delete_templates', g.user.id, request.remote_addr,
                 {'target_user_id': user_id, 'templates_deleted': deleted})

        return jsonify({
            'success': True,
            'message': f'{deleted} template(s) supprimé(s)',
            'user_id': user_id
        }), 200

    except Exception as e:
        logger.error(f"Delete user templates: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
