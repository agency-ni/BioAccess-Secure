"""
Routes API pour la gestion des utilisateurs
GET    /api/v1/users
GET    /api/v1/users/<user_id>
PUT    /api/v1/users/<user_id>
DELETE /api/v1/users/<user_id>
POST   /api/v1/users
"""

from flask import Blueprint, request, g, jsonify
from functools import wraps
from datetime import datetime
import logging
import uuid

from core.database import db
from core.errors import ValidationError, AuthenticationError, NotFoundError, AuthorizationError
from api.middlewares.auth_middleware import token_required, admin_required
from api.response_handler import APIResponse

from models.user import User

logger = logging.getLogger(__name__)

users_bp = Blueprint('users', __name__)

# ============================================================
# USERS ENDPOINTS
# ============================================================

@users_bp.route('', methods=['POST'])
@admin_required
def create_user():
    """
    Créer un nouvel utilisateur avec statut PENDING
    
    POST /api/v1/users
    Header: X-Admin-Token: token_admin
    Body: {
        "nom": "Dupont",
        "prenom": "Jean",
        "email": "jean.dupont@example.com",
        "role": "employe|admin|super_admin (défaut: employe)",
        "departement": "TI"
    }
    
    Response: {
        "status": "success",
        "code": 201,
        "message": "Utilisateur créé avec succès",
        "data": {
            "user_id": "uuid-xxxxxxxx",
            "statut": "PENDING",
            "email": "jean.dupont@example.com",
            "created_at": "2024-01-01T..."
        }
    }
    """
    try:
        data = request.get_json() or {}
        
        # Validation données requises
        nom = data.get('nom', '').strip()
        prenom = data.get('prenom', '').strip()
        email = data.get('email', '').strip().lower()
        role = data.get('role', 'employe').lower()
        departement = data.get('departement', '').strip()
        
        if not nom or not prenom or not email:
            return APIResponse.error(
                "nom, prenom, email requis",
                error_code="MISSING_FIELDS",
                status_code=400
            )
        
        # Validation email
        if '@' not in email or len(email) < 5:
            return APIResponse.error(
                "Email invalide",
                error_code="INVALID_EMAIL",
                status_code=400
            )
        
        # Validation rôle
        valid_roles = ['employe', 'admin', 'super_admin']
        if role not in valid_roles:
            return APIResponse.error(
                f"Rôle invalide. Valeurs: {', '.join(valid_roles)}",
                error_code="INVALID_ROLE",
                status_code=400
            )
        
        # Vérifier email unique
        existing = User.query.filter_by(email=email).first()
        if existing:
            return APIResponse.error(
                "Email déjà utilisé",
                error_code="EMAIL_ALREADY_EXISTS",
                status_code=409
            )
        
        # Créer nouvel utilisateur
        new_user = User(
            id=str(uuid.uuid4()),
            nom=nom,
            prenom=prenom,
            email=email,
            role=role,
            departement=departement,
            is_active=False,  # PENDING → is_active=False
            email_verified=False,
            date_creation=datetime.utcnow(),
            date_modification=datetime.utcnow()
        )
        
        # Générer mot de passe temporaire (admin doit le changer)
        temporary_password = str(uuid.uuid4())[:12]
        new_user.set_password(temporary_password)
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"Utilisateur créé: {new_user.id} ({email})")
        
        return APIResponse.success(
            {
                'user_id': new_user.id,
                'statut': 'PENDING',
                'nom': nom,
                'prenom': prenom,
                'email': email,
                'role': role,
                'departement': departement,
                'created_at': new_user.date_creation.isoformat()
            },
            "Utilisateur créé avec succès (statut PENDING)",
            status_code=201
        )
    
    except Exception as e:
        logger.error(f"Erreur création utilisateur: {e}")
        db.session.rollback()
        return APIResponse.error(
            "Erreur lors de la création",
            error_code="CREATE_USER_ERROR",
            status_code=500
        )


@users_bp.route('', methods=['GET'])
@admin_required
def list_users():
    """
    Lister tous les utilisateurs (admin seulement)
    
    GET /api/v1/users
    Response: { status, code, timestamp, message, data: [users...] }
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Limiter per_page
        per_page = min(per_page, 100)
        
        # Query
        query = User.query
        
        # Filters
        role = request.args.get('role')
        if role:
            query = query.filter_by(role=role)
        
        is_active = request.args.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() in ['true', '1', 'yes']
            query = query.filter_by(is_active=is_active_bool)
        
        # Pagination
        paginated = query.paginate(page=page, per_page=per_page)
        
        users_data = [u.getInfos() for u in paginated.items]
        
        return APIResponse.paginated(
            users_data,
            paginated.total,
            page,
            per_page,
            "Utilisateurs récupérés avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur listage utilisateurs: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération des utilisateurs",
            error_code="LIST_USERS_ERROR",
            status_code=500
        )


@users_bp.route('/<user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    """
    Récupérer les informations d'un utilisateur
    
    GET /api/v1/users/<user_id>
    Response: { status, code, timestamp, message, data: {user...} }
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
        
        return APIResponse.success(
            user.getInfos(),
            "Utilisateur récupéré avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur récupération utilisateur {user_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la récupération",
            error_code="GET_USER_ERROR",
            status_code=500
        )


@users_bp.route('/<user_id>', methods=['PUT'])
@token_required
def update_user(user_id):
    """
    Mettre à jour les informations d'un utilisateur
    
    PUT /api/v1/users/<user_id>
    Body: { nom?, prenom?, email?, departement? }
    Response: { status, code, timestamp, message, data: {user...} }
    """
    try:
        # Vérifier permissions
        if g.user_id != user_id and g.user_role != 'super_admin':
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
        
        data = request.get_json() or {}
        
        # Champs autorisés à modifier
        allowed_fields = ['nom', 'prenom', 'email', 'departement']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        user.date_modification = datetime.utcnow()
        db.session.commit()
        
        return APIResponse.success(
            user.getInfos(),
            "Utilisateur mis à jour avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur mise à jour utilisateur {user_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la mise à jour",
            error_code="UPDATE_USER_ERROR",
            status_code=500
        )


@users_bp.route('/<user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    Supprimer un utilisateur (admin seulement)
    
    DELETE /api/v1/users/<user_id>
    Response: { status, code, timestamp, message, data: {deleted_user} }
    """
    try:
        # Empêcher de supprimer super_admin
        user = User.query.get(user_id)
        if not user:
            return APIResponse.error(
                "Utilisateur non trouvé",
                error_code="USER_NOT_FOUND",
                status_code=404
            )
        
        if user.role == 'super_admin':
            return APIResponse.error(
                "Impossible de supprimer un super_admin",
                error_code="CANNOT_DELETE_SUPER_ADMIN",
                status_code=403
            )
        
        user_data = user.getInfos()
        db.session.delete(user)
        db.session.commit()
        
        return APIResponse.success(
            user_data,
            "Utilisateur supprimé avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur suppression utilisateur {user_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la suppression",
            error_code="DELETE_USER_ERROR",
            status_code=500
        )


@users_bp.route('/<user_id>/roles', methods=['PUT'])
@admin_required
def update_user_role(user_id):
    """
    Mettre à jour le rôle d'un utilisateur (admin seulement)
    
    PUT /api/v1/users/<user_id>/roles
    Body: { role: "admin|employe|auditeur" }
    Response: { status, code, timestamp, message, data: {user...} }
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return APIResponse.error(
                "Utilisateur non trouvé",
                error_code="USER_NOT_FOUND",
                status_code=404
            )
        
        data = request.get_json() or {}
        role = data.get('role')
        
        valid_roles = ['admin', 'employe', 'auditeur', 'super_admin']
        if not role or role not in valid_roles:
            return APIResponse.error(
                f"Rôle invalide. Valeurs: {', '.join(valid_roles)}",
                error_code="INVALID_ROLE",
                status_code=400
            )
        
        user.role = role
        db.session.commit()
        
        return APIResponse.success(
            user.getInfos(),
            "Rôle utilisateur mis à jour avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur mise à jour rôle {user_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la mise à jour du rôle",
            error_code="UPDATE_ROLE_ERROR",
            status_code=500
        )


@users_bp.route('/<user_id>/activate', methods=['POST'])
@admin_required
def activate_user(user_id):
    """
    Activer un utilisateur désactivé
    
    POST /api/v1/users/<user_id>/activate
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return APIResponse.error(
                "Utilisateur non trouvé",
                error_code="USER_NOT_FOUND",
                status_code=404
            )
        
        user.is_active = True
        db.session.commit()
        
        return APIResponse.success(
            user.getInfos(),
            "Utilisateur activé avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur activation utilisateur {user_id}: {e}")
        return APIResponse.error(
            "Erreur lors de l'activation",
            error_code="ACTIVATE_USER_ERROR",
            status_code=500
        )


@users_bp.route('/<user_id>/deactivate', methods=['POST'])
@admin_required
def deactivate_user(user_id):
    """
    Désactiver un utilisateur
    
    POST /api/v1/users/<user_id>/deactivate
    """
    try:
        user = User.query.get(user_id)
        if not user:
            return APIResponse.error(
                "Utilisateur non trouvé",
                error_code="USER_NOT_FOUND",
                status_code=404
            )
        
        user.is_active = False
        db.session.commit()
        
        return APIResponse.success(
            user.getInfos(),
            "Utilisateur désactivé avec succès"
        )
    
    except Exception as e:
        logger.error(f"Erreur désactivation utilisateur {user_id}: {e}")
        return APIResponse.error(
            "Erreur lors de la désactivation",
            error_code="DEACTIVATE_USER_ERROR",
            status_code=500
        )
