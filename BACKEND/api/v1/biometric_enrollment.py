"""
Routes API pour enregistrement biométrique (upload + live)
Endpoints pour Admin Dashboard et Client Desktop
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
from datetime import datetime
import logging
import base64

from core.errors import ValidationError, AuthenticationError
from core.logger import log_audit
from api.middlewares.auth_middleware import token_required, optional_token
from services.biometric_enrollment_service import BiometricEnrollmentService
from services.biometric_authentication_service import BiometricAuthenticationService

logger = logging.getLogger(__name__)

# Create blueprint
enrollment_bp = Blueprint('biometric_enrollment', __name__, url_prefix='/auth/biometric')

# Services
enrollment_service = BiometricEnrollmentService()
auth_service = BiometricAuthenticationService()


# ============================================================
# ENREGISTREMENT FACIAL
# ============================================================

@enrollment_bp.route('/enroll/upload', methods=['POST'])
@token_required
def enroll_face_upload():
    """
    Enregistrer un visage par photo upload
    
    POST /api/v1/auth/biometric/enroll/upload
    Header: Authorization: Bearer <token>
    Form:
        - image: fichier image (JPG/PNG)
        - label: label optionnel (ex: "Bureau")
    
    Response:
        {
            "success": true,
            "template_id": "uuid",
            "quality_score": 0.85,
            "templates_count": 2,
            "message": "Visage enregistré..."
        }
    """
    try:
        user_id = g.user_id
        
        # Récupérer image
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Image requise'
            }), 400
        
        file = request.files['image']
        if not file.filename:
            return jsonify({
                'success': False,
                'error': 'Fichier image vide'
            }), 400
        
        # Valider type fichier
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        if not ('.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({
                'success': False,
                'error': 'Format image invalide (JPG, PNG acceptés)'
            }), 400
        
        # Lire image
        image_data = file.read()
        label = request.form.get('label', None)
        
        # Enregistrer
        result = enrollment_service.enroll_face_from_upload(
            user_id=user_id,
            image_data=image_data,
            label=label,
            check_duplicate=True
        )
        
        if result.success:
            log_audit(
                user_id=user_id,
                action='BIOMETRIC_ENROLL',
                resource='template_biometrique',
                resource_id=result.template_id,
                details={'mode': 'upload', 'quality': result.quality_score},
                status='SUCCESS'
            )
            
            return jsonify({
                'success': True,
                'template_id': result.template_id,
                'quality_score': result.quality_score,
                'templates_count': result.templates_count,
                'message': result.message
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result.error
            }), 400
    
    except Exception as e:
        logger.error(f"Erreur enregistrement upload: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


@enrollment_bp.route('/enroll/live', methods=['POST'])
@token_required
def enroll_face_live():
    """
    Enregistrer un visage par capture live
    
    POST /api/v1/auth/biometric/enroll/live
    Header: Authorization: Bearer <token>
    Body:
        {
            "image_base64": "data:image/jpeg;base64,...",
            "label": "label optionnel"
        }
    
    Response:
        {
            "success": true,
            "template_id": "uuid",
            "quality_score": 0.85,
            "templates_count": 2,
            "message": "Visage enregistré..."
        }
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        if not data or 'image_base64' not in data:
            return jsonify({
                'success': False,
                'error': 'image_base64 requise'
            }), 400
        
        image_base64 = data['image_base64']
        label = data.get('label', 'Capture live')
        
        # Gérer data URI
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]
        
        # Enregistrer
        result = enrollment_service.enroll_face_from_live(
            user_id=user_id,
            image_base64=image_base64,
            label=label
        )
        
        if result.success:
            log_audit(
                user_id=user_id,
                action='BIOMETRIC_ENROLL',
                resource='template_biometrique',
                resource_id=result.template_id,
                details={'mode': 'live', 'quality': result.quality_score},
                status='SUCCESS'
            )
            
            return jsonify({
                'success': True,
                'template_id': result.template_id,
                'quality_score': result.quality_score,
                'templates_count': result.templates_count,
                'message': result.message
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result.error
            }), 400
    
    except Exception as e:
        logger.error(f"Erreur enregistrement live: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


@enrollment_bp.route('/templates', methods=['GET'])
@token_required
def get_templates():
    """
    Récupère les templates d'un utilisateur
    
    GET /api/v1/auth/biometric/templates
    Header: Authorization: Bearer <token>
    
    Response:
        {
            "success": true,
            "templates": [
                {
                    "id": "uuid",
                    "label": "Bureau",
                    "quality_score": 0.85,
                    "created": "2024-01-01T...",
                    "last_used": "2024-01-15T..."
                }
            ]
        }
    """
    try:
        user_id = g.user_id
        
        templates = enrollment_service.get_user_templates(user_id)
        
        return jsonify({
            'success': True,
            'templates': templates,
            'count': len(templates)
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur récupération templates: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


@enrollment_bp.route('/templates/<template_id>', methods=['DELETE'])
@token_required
def delete_template(template_id):
    """
    Supprime un template
    
    DELETE /api/v1/auth/biometric/templates/{template_id}
    Header: Authorization: Bearer <token>
    
    Response:
        { "success": true, "message": "Template supprimé" }
    """
    try:
        user_id = g.user_id
        
        success = enrollment_service.delete_template(user_id, template_id)
        
        if success:
            log_audit(
                user_id=user_id,
                action='BIOMETRIC_DELETE',
                resource='template_biometrique',
                resource_id=template_id,
                status='SUCCESS'
            )
            
            return jsonify({
                'success': True,
                'message': 'Template supprimé'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Template non trouvé'
            }), 404
    
    except Exception as e:
        logger.error(f"Erreur suppression template: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


# ============================================================
# AUTHENTIFICATION FACIALE
# ============================================================

@enrollment_bp.route('/authenticate', methods=['POST'])
def authenticate():
    """
    Authentifie un utilisateur par visage
    
    POST /api/v1/auth/biometric/authenticate
    Body:
        {
            "email": "user@example.com",
            "image_base64": "data:image/jpeg;base64,...",
            "source": "admin|desktop"  // optionnel
        }
    
    Response:
        {
            "success": true,
            "token": "jwt_token",
            "user": {
                "id": "uuid",
                "email": "user@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "admin"
            },
            "similarity_score": 0.95,
            "message": "Authentification réussie"
        }
    """
    try:
        data = request.get_json()
        
        if not data or 'email' not in data or 'image_base64' not in data:
            return jsonify({
                'success': False,
                'error': 'email et image_base64 requises'
            }), 400
        
        email = data['email'].lower()
        image_base64 = data['image_base64']
        source = data.get('source', 'unknown')
        is_admin = source == 'admin'
        
        # Gérer data URI
        if image_base64.startswith('data:image'):
            image_base64 = image_base64.split(',')[1]
        
        # Obtenir IP client
        client_ip = request.remote_addr
        client_user_agent = request.headers.get('User-Agent')
        
        # Authentifier
        result = auth_service.authenticate_by_face(
            email=email,
            image_base64=image_base64,
            client_ip=client_ip,
            client_user_agent=client_user_agent,
            is_admin=is_admin
        )
        
        if result.success:
            from models.user import User
            user = User.query.get(result.user_id)
            
            log_audit(
                user_id=result.user_id,
                action='AUTHENTICATION',
                resource='user_session',
                details={'method': 'FACE_BIOMETRIC', 'source': source},
                status='SUCCESS'
            )
            
            return jsonify({
                'success': True,
                'token': result.token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role
                },
                'similarity_score': round(result.similarity_score, 4),
                'message': result.message
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': result.error,
                'similarity_score': result.similarity_score
            }), 401
    
    except Exception as e:
        logger.error(f"Erreur authentification: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


# ============================================================
# LOGS & STATISTIQUES ADMIN
# ============================================================

@enrollment_bp.route('/admin/logs', methods=['GET'])
@token_required
def get_admin_logs():
    """
    Récupère les logs d'authentification (admin seulement)
    
    GET /api/v1/auth/biometric/admin/logs?limit=50&offset=0
    Header: Authorization: Bearer <token>
    Query:
        - limit: nombre de résultats (défaut 50)
        - offset: pagination (défaut 0)
        - user_id: filtrer par utilisateur
    
    Response:
        {
            "success": true,
            "logs": [...],
            "total": 250
        }
    """
    try:
        # Vérifier permissions admin
        from models.user import User
        user = User.query.get(g.user_id)
        
        if user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Accès non autorisé'
            }), 403
        
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        user_id = request.args.get('user_id', None)
        
        logs = auth_service.get_authentication_logs(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'logs': logs,
            'limit': limit,
            'offset': offset
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur récupération logs admin: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500


@enrollment_bp.route('/admin/stats', methods=['GET'])
@token_required
def get_admin_stats():
    """
    Récupère statistiques dashboard admin
    
    GET /api/v1/auth/biometric/admin/stats
    Header: Authorization: Bearer <token>
    
    Response:
        {
            "success": true,
            "total_attempts": 1250,
            "successful": 1190,
            "failed": 60,
            "success_rate": 95.2,
            "critical_errors": 2,
            "date": "2024-01-15"
        }
    """
    try:
        # Vérifier permissions admin
        from models.user import User
        user = User.query.get(g.user_id)
        
        if user.role != 'admin':
            return jsonify({
                'success': False,
                'error': 'Accès non autorisé'
            }), 403
        
        stats = auth_service.get_admin_dashboard_stats()
        
        return jsonify({
            'success': True,
            **stats
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur stats dashboard: {e}")
        return jsonify({
            'success': False,
            'error': 'Erreur serveur'
        }), 500
