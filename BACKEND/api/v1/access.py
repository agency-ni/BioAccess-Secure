"""
Routes API pour le contrôle d'accès
GET    /api/v1/access/permissions/<user_id>
POST   /api/v1/access/check
GET    /api/v1/access/doors
GET    /api/v1/access/workstations
"""

from flask import Blueprint, request, g
import logging

from core.database import db
from core.errors import ValidationError, NotFoundError
from api.middlewares.auth_middleware import token_required, admin_required
from api.response_handler import APIResponse

from models.user import User
from models.access_point import Porte, PosteTravail

logger = logging.getLogger(__name__)

access_bp = Blueprint('access', __name__)


@access_bp.route('/permissions/<user_id>', methods=['GET'])
@token_required
def get_user_permissions(user_id):
    """
    Récupérer les permissions d'accès d'un utilisateur
    
    GET /api/v1/access/permissions/<user_id>
    Response: { status, code, timestamp, message, data: {permissions...} }
    """
    try:
        # Vérifier permissions (self ou admin)
        if g.user_id != user_id and g.user_role not in ['admin', 'super_admin']:
            return APIResponse.error(
                "Accès refusé",
                error_code="ACCESS_DENIED",
                status_code=403
            )
        
        user = User.query.get(user_id)
        if not user:
            return APIResponse.error(
                "Utilisateur non trouvé",
                error_code="USER_NOT_FOUND",
                status_code=404
            )
        
        # Construire les permissions
        permissions = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active,
            'can_access_system': user.is_active,
            'can_use_biometric': user.is_active,
            'department': user.departement,
            'timestamp': None
        }
        
        return APIResponse.success(
            permissions,
            "Permissions récupérées avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur récupération permissions {user_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="GET_PERMISSIONS_ERROR",
            status_code=500
        )


@access_bp.route('/check', methods=['POST'])
@token_required
def check_access():
    """
    Vérifier l'accès à une ressource
    
    POST /api/v1/access/check
    Body: { resource: "door|workstation", resource_id: "..." }
    Response: { status, code, timestamp, message, data: {access_allowed, reason} }
    """
    try:
        data = request.get_json() or {}
        resource = data.get('resource')
        resource_id = data.get('resource_id')
        
        if not resource or not resource_id:
            return APIResponse.error(
                "resource et resource_id requis",
                error_code="MISSING_PARAMS",
                status_code=400
            )
        
        user = User.query.get(g.user_id)
        if not user or not user.is_active:
            return APIResponse.success(
                {'access_allowed': False, 'reason': 'Utilisateur inactif'},
                "Vérification d'accès complétée"
            )
        
        # Vérifier selon le type de ressource
        if resource == 'door':
            door = Porte.query.get(resource_id)
            if not door:
                return APIResponse.error(
                    "Porte non trouvée",
                    error_code="RESOURCE_NOT_FOUND",
                    status_code=404
                )
            
            allowed, reason = door.check_access(user)
            return APIResponse.success(
                {'access_allowed': allowed, 'reason': reason},
                "Vérification d'accès complétée"
            )
        
        elif resource == 'workstation':
            workstation = PosteTravail.query.get(resource_id)
            if not workstation:
                return APIResponse.error(
                    "Poste de travail non trouvé",
                    error_code="RESOURCE_NOT_FOUND",
                    status_code=404
                )
            
            # Vérification simple pour workstation
            allowed = workstation.statut == 'actif'
            return APIResponse.success(
                {'access_allowed': allowed, 'reason': 'Poste de travail accessible' if allowed else 'Poste de travail indisponible'},
                "Vérification d'accès complétée"
            )
        
        else:
            return APIResponse.error(
                "Type de ressource invalide",
                error_code="INVALID_RESOURCE_TYPE",
                status_code=400
            )
    
    except Exception as e:
        logger.error(f"Erreur vérification accès: {e}")
        return APIResponse.error(
            "Erreur lors de la vérification",
            error_code="CHECK_ACCESS_ERROR",
            status_code=500
        )


@access_bp.route('/doors', methods=['GET'])
@admin_required
def list_doors():
    """
    Lister toutes les portes
    
    GET /api/v1/access/doors
    Response: { status, code, timestamp, message, data: [doors...] }
    """
    try:
        doors = Porte.query.all()
        doors_data = [d.to_dict() for d in doors]
        
        return APIResponse.success(
            doors_data,
            "Portes récupérées avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur listage portes: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="LIST_DOORS_ERROR",
            status_code=500
        )


@access_bp.route('/workstations', methods=['GET'])
@admin_required
def list_workstations():
    """
    Lister tous les postes de travail
    
    GET /api/v1/access/workstations
    Response: { status, code, timestamp, message, data: [workstations...] }
    """
    try:
        workstations = PosteTravail.query.all()
        workstations_data = [w.to_dict() for w in workstations]
        
        return APIResponse.success(
            workstations_data,
            "Postes de travail récupérés avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur listage postes: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="LIST_WORKSTATIONS_ERROR",
            status_code=500
        )
