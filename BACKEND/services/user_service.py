"""
Service de gestion des utilisateurs
"""

from models.user import User, Employe, Admin
from models.biometric import TemplateBiometrique, PhraseAleatoire
from core.database import db
from core.security import SecurityManager
from core.errors import NotFoundError, ValidationError, ConflictError
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger(__name__)

class UserService:
    """Service pour la gestion des utilisateurs"""
    
    @staticmethod
    def get_all_users(filters=None, page=1, per_page=20):
        """Récupère tous les utilisateurs avec pagination"""
        query = User.query
        
        if filters:
            if filters.get('departement'):
                query = query.filter_by(departement=filters['departement'])
            if filters.get('role'):
                query = query.filter_by(role=filters['role'])
            if filters.get('is_active') is not None:
                query = query.filter_by(is_active=filters['is_active'])
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query = query.filter(
                    db.or_(
                        User.nom.ilike(search),
                        User.prenom.ilike(search),
                        User.email.ilike(search)
                    )
                )
        
        pagination = query.order_by(User.date_creation.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return {
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages,
            'users': [u.to_dict() for u in pagination.items]
        }
    
    @staticmethod
    def get_user(user_id):
        """Récupère un utilisateur par son ID"""
        user = User.query.get(user_id)
        if not user:
            raise NotFoundError("Utilisateur")
        return user
    
    @staticmethod
    def create_user(data, creator_id=None):
        """Crée un nouvel utilisateur"""
        # Vérifier email unique
        if User.query.filter_by(email=data['email'].lower()).first():
            raise ConflictError("Email déjà utilisé")
        
        # Créer selon le rôle
        if data.get('role') == 'admin':
            user = Admin(
                email=data['email'].lower(),
                nom=data['nom'],
                prenom=data['prenom'],
                departement=data.get('departement'),
                niveau_habilitation=data.get('niveau_habilitation', 'standard')
            )
        else:
            user = Employe(
                email=data['email'].lower(),
                nom=data['nom'],
                prenom=data['prenom'],
                departement=data.get('departement'),
                date_embauche=data.get('date_embauche'),
                poste_occupe=data.get('poste_occupe')
            )
        
        user.set_password(data['password'])
        
        if 'role' in data and data['role'] in ['admin', 'super_admin']:
            user.role = data['role']
        
        try:
            db.session.add(user)
            db.session.commit()
            logger.info(f"✅ Utilisateur créé: {user.email} par {creator_id}")
            
            # Log d'audit
            from services.audit_service import AuditService
            AuditService.log_action(
                'user_create',
                creator_id,
                details={'user_id': user.id, 'email': user.email}
            )
            
            return user
        except IntegrityError:
            db.session.rollback()
            raise ConflictError("Erreur lors de la création")
    
    @staticmethod
    def update_user(user_id, data, updater_id=None):
        """Met à jour un utilisateur"""
        user = UserService.get_user(user_id)
        
        # Vérifier email unique si modifié
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email'].lower()).first():
                raise ConflictError("Email déjà utilisé")
            user.email = data['email'].lower()
        
        # Mettre à jour les champs
        updatable = ['nom', 'prenom', 'departement', 'is_active']
        for field in updatable:
            if field in data:
                setattr(user, field, data[field])
        
        # Mettre à jour mot de passe si fourni
        if 'password' in data:
            user.set_password(data['password'])
        
        # Changer rôle (attention!)
        if 'role' in data and data['role'] != user.role:
            if updater_id:
                from services.audit_service import AuditService
                AuditService.log_action(
                    'role_change',
                    updater_id,
                    details={
                        'user_id': user_id,
                        'old_role': user.role,
                        'new_role': data['role']
                    }
                )
            user.role = data['role']
        
        user.date_modification = datetime.utcnow()
        db.session.commit()
        
        return user
    
    @staticmethod
    def delete_user(user_id, deleter_id=None):
        """Supprime un utilisateur (soft delete)"""
        user = UserService.get_user(user_id)
        
        # Soft delete (désactiver)
        user.is_active = False
        user.email = f"deleted_{user.id}@bioaccess.com"
        db.session.commit()
        
        # Log d'audit
        from services.audit_service import AuditService
        AuditService.log_action(
            'user_delete',
            deleter_id,
            details={'user_id': user_id, 'email': user.email}
        )
        
        return True
    
    @staticmethod
    def get_user_stats(user_id):
        """Récupère les statistiques d'un utilisateur"""
        user = UserService.get_user(user_id)
        
        from models.log import LogAcces
        from models.biometric import TentativeAuth
        
        total_logins = LogAcces.query.filter_by(
            utilisateur_id=user_id,
            type_acces='auth'
        ).count()
        
        failed_logins = LogAcces.query.filter_by(
            utilisateur_id=user_id,
            type_acces='auth',
            statut='echec'
        ).count()
        
        success_rate = 0
        if total_logins > 0:
            success_rate = round((total_logins - failed_logins) / total_logins * 100, 1)
        
        tentatives = TentativeAuth.query.filter_by(
            utilisateur_id=user_id
        ).order_by(TentativeAuth.date_heure.desc()).limit(10).all()
        
        return {
            'total_logins': total_logins,
            'failed_logins': failed_logins,
            'success_rate': success_rate,
            'last_login': user.last_login_at.isoformat() if user.last_login_at else None,
            'tentatives': [t.to_dict() for t in tentatives]
        }