"""
Gestionnaire des permissions biométriques
Module serveur pour valider et gérer les permissions d'accès
"""

from enum import Enum
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class BiometricPermission(Enum):
    """Permissions biométriques disponibles"""
    USE_CAMERA = "use_camera"
    USE_MICROPHONE = "use_microphone"
    RECORD_FACE = "record_face"
    RECORD_VOICE = "record_voice"
    ACCESS_BIOMETRIC_DATA = "access_biometric_data"
    VIEW_BIOMETRIC_LOGS = "view_biometric_logs"


class DeviceAccessLevel(Enum):
    """Niveaux d'accès aux périphériques"""
    DENIED = 0
    ALLOWED = 1
    ALLOWED_WITH_CONSENT = 2
    ADMIN_ONLY = 3


class BiometricPermissionsManager:
    """Gestionnaire des permissions biométriques"""

    def __init__(self):
        """Initialiser le gestionnaire"""
        self.user_permissions: Dict[str, Dict[str, bool]] = {}
        self.device_access_log: List[Dict] = []
        self.permission_cache: Dict[str, Dict] = {}
        self.cache_ttl = 300  # 5 minutes

    def grant_permission(self, user_id: str, permission: BiometricPermission) -> bool:
        """
        Accorder une permission à un utilisateur
        
        Args:
            user_id: ID de l'utilisateur
            permission: Permission BiometricPermission
            
        Returns:
            True si succès
        """
        if user_id not in self.user_permissions:
            self.user_permissions[user_id] = {}
        
        self.user_permissions[user_id][permission.value] = True
        self._log_permission_change(user_id, permission, "GRANT")
        self._invalidate_cache(user_id)
        
        logger.info(f"Permission accordée: {user_id} - {permission.value}")
        return True

    def revoke_permission(self, user_id: str, permission: BiometricPermission) -> bool:
        """
        Révoquer une permission
        
        Args:
            user_id: ID de l'utilisateur
            permission: Permission BiometricPermission
            
        Returns:
            True si succès
        """
        if user_id in self.user_permissions:
            self.user_permissions[user_id][permission.value] = False
            self._log_permission_change(user_id, permission, "REVOKE")
            self._invalidate_cache(user_id)
            
            logger.info(f"Permission révoquée: {user_id} - {permission.value}")
            return True
        
        return False

    def has_permission(self, user_id: str, permission: BiometricPermission) -> bool:
        """
        Vérifier si un utilisateur a une permission
        
        Args:
            user_id: ID de l'utilisateur
            permission: Permission BiometricPermission
            
        Returns:
            True si l'utilisateur a la permission
        """
        # Vérifier le cache
        if self._is_cache_valid(user_id):
            return self.permission_cache[user_id].get(permission.value, False)
        
        # Vérifier la permission
        if user_id not in self.user_permissions:
            return False
        
        has_perm = self.user_permissions[user_id].get(permission.value, False)
        
        # Mettre en cache
        self._cache_permission(user_id, permission.value, has_perm)
        
        return has_perm

    def get_user_permissions(self, user_id: str) -> Dict[str, bool]:
        """
        Obtenir toutes les permissions d'un utilisateur
        
        Returns:
            Dict des permissions
        """
        if user_id not in self.user_permissions:
            return {}
        
        return self.user_permissions[user_id].copy()

    def set_device_access_level(self, device_type: str, access_level: DeviceAccessLevel) -> None:
        """
        Définir le niveau d'accès pour un périphérique
        
        Args:
            device_type: Type de périphérique ('camera', 'microphone')
            access_level: Niveau d'accès
        """
        logger.info(f"Niveau d'accès défini: {device_type} = {access_level.name}")

    def get_device_access_level(self, device_type: str, user_role: str) -> DeviceAccessLevel:
        """
        Obtenir le niveau d'accès pour un périphérique selon le rôle
        
        Args:
            device_type: Type de périphérique
            user_role: Rôle de l'utilisateur
            
        Returns:
            DeviceAccessLevel
        """
        # Logique par défaut selon le rôle
        if user_role == "super_admin":
            return DeviceAccessLevel.ALLOWED
        elif user_role == "admin":
            return DeviceAccessLevel.ALLOWED
        elif user_role == "employé":
            return DeviceAccessLevel.ALLOWED_WITH_CONSENT
        else:
            return DeviceAccessLevel.DENIED

    def require_camera_permission(self):
        """Décorateur pour nécessiter la permission d'utiliser la caméra"""
        def decorator(func):
            @wraps(func)
            def wrapper(self, user_id=None, *args, **kwargs):
                if not user_id:
                    raise PermissionError("user_id requis")
                
                if not self.has_permission(user_id, BiometricPermission.USE_CAMERA):
                    logger.warning(f"Tentative non autorisée d'accès caméra: {user_id}")
                    raise PermissionError("Permission d'accès caméra refusée")
                
                self._log_device_access(user_id, "camera", "GRANTED")
                return func(self, user_id, *args, **kwargs)
            
            return wrapper
        return decorator

    def require_microphone_permission(self):
        """Décorateur pour nécessiter la permission d'utiliser le microphone"""
        def decorator(func):
            @wraps(func)
            def wrapper(self, user_id=None, *args, **kwargs):
                if not user_id:
                    raise PermissionError("user_id requis")
                
                if not self.has_permission(user_id, BiometricPermission.USE_MICROPHONE):
                    logger.warning(f"Tentative non autorisée d'accès microphone: {user_id}")
                    raise PermissionError("Permission d'accès microphone refusée")
                
                self._log_device_access(user_id, "microphone", "GRANTED")
                return func(self, user_id, *args, **kwargs)
            
            return wrapper
        return decorator

    def _log_permission_change(self, user_id: str, permission: BiometricPermission, action: str):
        """Log les changements de permission"""
        self.device_access_log.append({
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'permission': permission.value,
            'action': action
        })

    def _log_device_access(self, user_id: str, device: str, status: str):
        """Log l'accès aux périphériques"""
        self.device_access_log.append({
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'device': device,
            'status': status
        })

    def _cache_permission(self, user_id: str, permission: str, value: bool):
        """Mettre en cache une permission"""
        if user_id not in self.permission_cache:
            self.permission_cache[user_id] = {
                'permissions': {},
                'timestamp': datetime.now()
            }
        
        self.permission_cache[user_id]['permissions'][permission] = value
        self.permission_cache[user_id]['timestamp'] = datetime.now()

    def _is_cache_valid(self, user_id: str) -> bool:
        """Vérifier si le cache est valide"""
        if user_id not in self.permission_cache:
            return False
        
        cache_time = self.permission_cache[user_id]['timestamp']
        if datetime.now() - cache_time > timedelta(seconds=self.cache_ttl):
            return False
        
        return True

    def _invalidate_cache(self, user_id: str):
        """Invalider le cache pour un utilisateur"""
        if user_id in self.permission_cache:
            del self.permission_cache[user_id]

    def get_access_log(self, user_id: Optional[str] = None, 
                       device: Optional[str] = None,
                       limit: int = 100) -> List[Dict]:
        """
        Obtenir le log d'accès
        
        Args:
            user_id: Filtrer par utilisateur
            device: Filtrer par périphérique
            limit: Nombre maximum d'entrées
            
        Returns:
            Liste des logs filtrés
        """
        logs = self.device_access_log
        
        if user_id:
            logs = [log for log in logs if log.get('user_id') == user_id]
        
        if device:
            logs = [log for log in logs if log.get('device') == device]
        
        return logs[-limit:]

    def export_permissions(self) -> Dict:
        """
        Exporter la configuration actuelle
        
        Returns:
            Dict avec toutes les permissions
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'user_permissions': self.user_permissions,
            'access_log_count': len(self.device_access_log)
        }


# Instance globale
biometric_permissions = BiometricPermissionsManager()


# Fonctions utilitaires pour la configuration par défaut
def setup_default_permissions(user_id: str, role: str):
    """
    Configurer les permissions par défaut selon le rôle
    
    Args:
        user_id: ID de l'utilisateur
        role: Rôle de l'utilisateur
    """
    if role == "super_admin":
        biometric_permissions.grant_permission(user_id, BiometricPermission.USE_CAMERA)
        biometric_permissions.grant_permission(user_id, BiometricPermission.USE_MICROPHONE)
        biometric_permissions.grant_permission(user_id, BiometricPermission.RECORD_FACE)
        biometric_permissions.grant_permission(user_id, BiometricPermission.RECORD_VOICE)
        biometric_permissions.grant_permission(user_id, BiometricPermission.ACCESS_BIOMETRIC_DATA)
        biometric_permissions.grant_permission(user_id, BiometricPermission.VIEW_BIOMETRIC_LOGS)
    
    elif role == "admin":
        biometric_permissions.grant_permission(user_id, BiometricPermission.USE_CAMERA)
        biometric_permissions.grant_permission(user_id, BiometricPermission.USE_MICROPHONE)
        biometric_permissions.grant_permission(user_id, BiometricPermission.RECORD_FACE)
        biometric_permissions.grant_permission(user_id, BiometricPermission.RECORD_VOICE)
        biometric_permissions.grant_permission(user_id, BiometricPermission.ACCESS_BIOMETRIC_DATA)
        biometric_permissions.revoke_permission(user_id, BiometricPermission.VIEW_BIOMETRIC_LOGS)
    
    elif role == "employé":
        biometric_permissions.grant_permission(user_id, BiometricPermission.USE_CAMERA)
        biometric_permissions.grant_permission(user_id, BiometricPermission.USE_MICROPHONE)
        biometric_permissions.grant_permission(user_id, BiometricPermission.RECORD_FACE)
        biometric_permissions.grant_permission(user_id, BiometricPermission.RECORD_VOICE)
        biometric_permissions.revoke_permission(user_id, BiometricPermission.ACCESS_BIOMETRIC_DATA)
        biometric_permissions.revoke_permission(user_id, BiometricPermission.VIEW_BIOMETRIC_LOGS)


if __name__ == '__main__':
    # Test
    logging.basicConfig(level=logging.INFO)
    
    # Créer des permissions de test
    setup_default_permissions("user1", "employé")
    setup_default_permissions("admin1", "admin")
    
    # Vérifier les permissions
    print("Permissions de user1:")
    print(biometric_permissions.get_user_permissions("user1"))
    
    print("\nPermissions de admin1:")
    print(biometric_permissions.get_user_permissions("admin1"))
    
    # Tester les décorateurs
    print("\nLogs d'accès:")
    print(biometric_permissions.get_access_log(limit=5))
