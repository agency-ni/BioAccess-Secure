"""
Routes API pour la gestion des permissions biométriques
Endpoint pour contrôler l'accès aux périphériques
"""

from flask import Blueprint, request, jsonify, g
from functools import wraps
from typing import Dict, Tuple
from datetime import datetime
import logging

from core.biometric_permissions import (
    biometric_permissions,
    BiometricPermission,
    DeviceAccessLevel,
    setup_default_permissions
)
from api.middlewares.auth_middleware import token_required, admin_required

logger = logging.getLogger(__name__)

# Blueprint
biometric_bp = Blueprint('biometric', __name__)  # url_prefix défini dans app.py → register_blueprint


# ============════════════════════════════════════════════════════════════
# PERMISSIONS - GET
# ============════════════════════════════════════════════════════════════

@biometric_bp.route('/permissions/<user_id>', methods=['GET'])
@token_required
def get_user_permissions(user_id: str) -> Tuple[Dict, int]:
    """
    Récupérer les permissions d'un utilisateur
    Accès : l'utilisateur lui-même OU un admin/super_admin.

    GET /api/v1/biometric/permissions/<user_id>
    """
    # Self/admin check
    caller_id = str(g.user_id)
    caller_role = g.user_role
    if caller_id != str(user_id) and caller_role not in ['admin', 'super_admin']:
        return jsonify({'success': False, 'error': 'Accès non autorisé'}), 403

    try:
        permissions = biometric_permissions.get_user_permissions(user_id)
        
        if not permissions:
            return jsonify({
                'success': False,
                'message': f'Utilisateur {user_id} n\'a pas de permissions configurées'
            }), 404
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'permissions': permissions,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des permissions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@biometric_bp.route('/check-permission', methods=['POST'])
@token_required
def check_permission() -> Tuple[Dict, int]:
    """
    Vérifier une permission spécifique
    
    POST /api/v1/biometric/check-permission
    Body:
        {
            "user_id": "user123",
            "permission": "use_camera"
        }
    
    Response:
        {
            "success": true,
            "has_permission": true
        }
    """
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        permission = data.get('permission')
        
        if not user_id or not permission:
            return jsonify({
                'success': False,
                'error': 'user_id et permission requis'
            }), 400
        
        # Convertir en BiometricPermission
        try:
            perm = BiometricPermission[permission.upper()]
        except KeyError:
            return jsonify({
                'success': False,
                'error': f'Permission invalide: {permission}'
            }), 400
        
        has_perm = biometric_permissions.has_permission(user_id, perm)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'permission': permission,
            'has_permission': has_perm
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors de la vérification: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============════════════════════════════════════════════════════════════
# PERMISSIONS - SET/GRANT/REVOKE
# ============════════════════════════════════════════════════════════════

@biometric_bp.route('/permissions/<user_id>/grant', methods=['POST'])
@admin_required
def grant_permission(user_id: str) -> Tuple[Dict, int]:
    """
    Accorder une permission
    
    POST /api/v1/biometric/permissions/<user_id>/grant
    Header: X-User-Role: admin|super_admin
    Body:
        {
            "permission": "use_camera"
        }
    """
    try:
        data = request.get_json() or {}
        permission = data.get('permission')
        
        if not permission:
            return jsonify({
                'success': False,
                'error': 'permission requise'
            }), 400
        
        # Convertir en BiometricPermission
        try:
            perm = BiometricPermission[permission.upper()]
        except KeyError:
            return jsonify({
                'success': False,
                'error': f'Permission invalide: {permission}'
            }), 400
        
        biometric_permissions.grant_permission(user_id, perm)
        
        return jsonify({
            'success': True,
            'message': f'Permission accordée: {user_id} - {permission}',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors de l'octroi de permission: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@biometric_bp.route('/permissions/<user_id>/revoke', methods=['POST'])
@admin_required
def revoke_permission(user_id: str) -> Tuple[Dict, int]:
    """
    Révoquer une permission
    
    POST /api/v1/biometric/permissions/<user_id>/revoke
    Header: X-User-Role: admin|super_admin
    Body:
        {
            "permission": "use_camera"
        }
    """
    try:
        data = request.get_json() or {}
        permission = data.get('permission')
        
        if not permission:
            return jsonify({
                'success': False,
                'error': 'permission requise'
            }), 400
        
        # Convertir en BiometricPermission
        try:
            perm = BiometricPermission[permission.upper()]
        except KeyError:
            return jsonify({
                'success': False,
                'error': f'Permission invalide: {permission}'
            }), 400
        
        biometric_permissions.revoke_permission(user_id, perm)
        
        return jsonify({
            'success': True,
            'message': f'Permission révoquée: {user_id} - {permission}',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors de la révocation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@biometric_bp.route('/permissions/<user_id>/setup-default', methods=['POST'])
@admin_required
def setup_default_perms(user_id: str) -> Tuple[Dict, int]:
    """
    Configurer les permissions par défaut selon le rôle
    
    POST /api/v1/biometric/permissions/<user_id>/setup-default
    Header: X-User-Role: admin|super_admin
    Body:
        {
            "role": "employé|admin|super_admin"
        }
    """
    try:
        data = request.get_json() or {}
        role = data.get('role', '').lower()
        
        if role not in ['employé', 'admin', 'super_admin']:
            return jsonify({
                'success': False,
                'error': f'Rôle invalide: {role}'
            }), 400
        
        setup_default_permissions(user_id, role)
        
        permissions = biometric_permissions.get_user_permissions(user_id)
        
        return jsonify({
            'success': True,
            'message': f'Permissions par défaut configurées pour {role}',
            'user_id': user_id,
            'role': role,
            'permissions': permissions,
            'timestamp': datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors de la configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============════════════════════════════════════════════════════════════
# LOGS
# ============════════════════════════════════════════════════════════════

@biometric_bp.route('/access-log', methods=['GET'])
@admin_required
def get_access_log() -> Tuple[Dict, int]:
    """
    Récupérer le log d'accès aux périphériques
    
    GET /api/v1/biometric/access-log?user_id=...&device=...&limit=100
    Header: X-User-Role: admin|super_admin
    """
    try:
        user_id = request.args.get('user_id')
        device = request.args.get('device')
        limit = int(request.args.get('limit', 100))
        
        logs = biometric_permissions.get_access_log(user_id, device, limit)
        
        return jsonify({
            'success': True,
            'count': len(logs),
            'logs': logs
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des logs: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@biometric_bp.route('/export-config', methods=['GET'])
@admin_required
def export_config() -> Tuple[Dict, int]:
    """
    Exporter la configuration actuelle
    
    GET /api/v1/biometric/export-config
    Header: X-User-Role: super_admin
    """
    try:
        config = biometric_permissions.export_permissions()
        return jsonify({
            'success': True,
            'config': config
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur lors de l'export: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============════════════════════════════════════════════════════════════
# DEVICE STATUS
# ============════════════════════════════════════════════════════════════

@biometric_bp.route('/device-access-level', methods=['GET'])
def get_device_access_level() -> Tuple[Dict, int]:
    """
    Obtenir le niveau d'accès pour un périphérique
    
    GET /api/v1/biometric/device-access-level?device=camera&role=employé
    """
    try:
        device = request.args.get('device', 'camera')
        role = request.args.get('role', 'employé').lower()
        
        if role not in ['employé', 'admin', 'super_admin']:
            return jsonify({
                'success': False,
                'error': f'Rôle invalide: {role}'
            }), 400
        
        level = biometric_permissions.get_device_access_level(device, role)
        
        return jsonify({
            'success': True,
            'device': device,
            'role': role,
            'access_level': level.name,
            'access_level_value': level.value
        }), 200
    
    except Exception as e:
        logger.error(f"Erreur: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@biometric_bp.route('/health', methods=['GET'])
def biometric_health() -> Tuple[Dict, int]:
    """
    Vérifier l'état des services biométriques
    
    GET /api/v1/biometric/health
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


@biometric_bp.route('/analyze-quality', methods=['POST'])
def analyze_quality_public() -> Tuple[Dict, int]:
    """
    Analyze image quality (PUBLIC - no auth required)
    Used by authentication pages for real-time quality detection
    
    POST /api/v1/biometric/analyze-quality
    {
        "image_base64": "data:image/jpeg;base64,..."
    }
    """
    try:
        data = request.get_json() or {}
        image_base64 = data.get('image_base64')
        
        if not image_base64:
            return jsonify({'success': False, 'message': 'Image requise'}), 400
        
        from services.biometric_enrollment_service import BiometricEnrollmentService
        enrollment_service = BiometricEnrollmentService()
        
        quality_score = enrollment_service.analyze_image_quality(image_base64)
        
        return jsonify({
            'success': True,
            'quality_score': quality_score,
            'acceptable': quality_score > 0.6
        }), 200
        
    except Exception as e:
        logger.error(f"Quality analysis error: {e}")
        return jsonify({'success': False, 'message': 'Erreur analyse qualité'}), 500


# Enregistrer le blueprint
def register_biometric_routes(app):
    """Enregistrer les routes biométriques"""
    app.register_blueprint(biometric_bp)
    logger.info("Routes biométriques enregistrées")
