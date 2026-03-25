"""
Routes API pour la gestion des permissions biométriques
Endpoint pour contrôler l'accès aux périphériques
"""

from flask import Blueprint, request, jsonify
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

logger = logging.getLogger(__name__)

# Blueprint
biometric_blueprint = Blueprint('biometric', __name__, url_prefix='/api/v1/biometric')


def require_admin(f):
    """Décorateur pour vérifier que l'utilisateur est admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = request.headers.get('X-User-Role', '').lower()
        
        if user_role not in ['admin', 'super_admin']:
            return jsonify({'error': 'Admin required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


# ============════════════════════════════════════════════════════════════
# PERMISSIONS - GET
# ============════════════════════════════════════════════════════════════

@biometric_blueprint.route('/permissions/<user_id>', methods=['GET'])
def get_user_permissions(user_id: str) -> Tuple[Dict, int]:
    """
    Récupérer les permissions d'un utilisateur
    
    GET /api/v1/biometric/permissions/<user_id>
    
    Response:
        {
            "success": true,
            "data": {
                "use_camera": true,
                "use_microphone": true,
                "record_face": true,
                "record_voice": true,
                "access_biometric_data": false,
                "view_biometric_logs": false
            }
        }
    """
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


@biometric_blueprint.route('/check-permission', methods=['POST'])
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

@biometric_blueprint.route('/permissions/<user_id>/grant', methods=['POST'])
@require_admin
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


@biometric_blueprint.route('/permissions/<user_id>/revoke', methods=['POST'])
@require_admin
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


@biometric_blueprint.route('/permissions/<user_id>/setup-default', methods=['POST'])
@require_admin
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

@biometric_blueprint.route('/access-log', methods=['GET'])
@require_admin
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


@biometric_blueprint.route('/export-config', methods=['GET'])
@require_admin
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

@biometric_blueprint.route('/device-access-level', methods=['GET'])
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


@biometric_blueprint.route('/health', methods=['GET'])
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


# Enregistrer le blueprint
def register_biometric_routes(app):
    """Enregistrer les routes biométriques"""
    app.register_blueprint(biometric_blueprint)
    logger.info("Routes biométriques enregistrées")
