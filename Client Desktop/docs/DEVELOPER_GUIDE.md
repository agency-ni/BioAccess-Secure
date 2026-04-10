# 👨‍💻 Guide de Développement - Intégration des Permissions Biométriques

## 📋 Vue d'ensemble

Ce guide explique comment intégrer la gestion des permissions biométriques dans votre application BioAccess Secure.

---

## 🎯 Architecture

```
┌─────────────────────────────────────────────┐
│        Application Frontend/Desktop         │
├─────────────────────────────────────────────┤
│  device_diagnostic.py    device_setup.py   │
│  permissions_manager.py                    │
├─────────────────────────────────────────────┤
│             API REST Backend                │
├─────────────────────┬───────────────────────┤
│ core/biometric_permissions.py       |       │
│ api/v1/biometric.py (routes)        |       │
│                                      |       │
│ BiometricPermissionsManager          │       │
│  ├─ check_permission()               │       │
│  ├─ has_permission()                 │       │
│  ├─ grant_permission()               │       │
│  └─ revoke_permission()              │       │
└─────────────────────┴───────────────────────┘
```

---

## 🔧 Configuration du Backend

### 1. Initialiser le gestionnaire

```python
# Dans app.py ou config.py
from core.biometric_permissions import (
    BiometricPermissionsManager,
    BiometricPermission,
    setup_default_permissions
)

# Créer l'instance globale
permissions_manager = BiometricPermissionsManager(cache_ttl_minutes=5)

# Configurer les permissions par défaut pour les nouveaux utilisateurs
def init_user_permissions(user_id: str, role: str):
    """Appelée lors de la création d'un utilisateur"""
    setup_default_permissions(user_id, role)
```

### 2. Intégrer dans la route de création d'utilisateur

```python
# services/user_service.py
from core.biometric_permissions import setup_default_permissions

def create_user(user_data: dict):
    """Créer un nouvel utilisateur"""
    # ... logique de création ...
    
    # Initialiser les permissions biométriques
    setup_default_permissions(user.id, user.role)
    
    return user
```

---

## 🔐 Utilisation des Permissions

### Méthode 1: Vérification directe

```python
from core.biometric_permissions import biometric_permissions, BiometricPermission

def capture_face(user_id: str, role: str):
    """Exemple: Capture faciale"""
    
    # Vérifier la permission
    if not biometric_permissions.has_permission(
        user_id,
        role,
        BiometricPermission.USE_CAMERA
    ):
        raise PermissionError("Accès caméra refusé")
    
    # Procéder avec la capture
    # ...
```

### Méthode 2: Avec vérification détaillée

```python
def record_voice(user_id: str, role: str):
    """Exemple: Enregistrement vocal"""
    
    check = biometric_permissions.check_permission(
        user_id,
        role,
        BiometricPermission.USE_MICROPHONE
    )
    
    if not check['allowed']:
        return {
            'error': 'Microphone access denied',
            'requires_consent': check['requires_consent']
        }, 403
    
    # Enregistrer
    # ...
    
    return {'status': 'recorded'}, 200
```

### Méthode 3: Décorateurs (pour Flask)

```python
from core.biometric_permissions import (
    require_camera_permission,
    require_microphone_permission,
    biometric_permissions
)

@app.route('/api/biometric/capture', methods=['POST'])
@require_camera_permission()
def capture_face():
    """Capture faciale (nécessite permission caméra)"""
    user_id = request.json['user_id']
    role = request.json['role']
    
    # La permission est déjà vérifiée par le décorateur
    # Procéder directement
    # ...
    
    return {'status': 'success'}, 200


@app.route('/api/biometric/voice', methods=['POST'])
@require_microphone_permission()
def record_voice():
    """Enregistrement vocal (nécessite permission microphone)"""
    # ...
    pass
```

---

## 📡 Routes API

### GET `/api/biometric/permissions/<user_id>`

Récupère les permissions d'un utilisateur.

```python
@app.route('/api/biometric/permissions/<user_id>', methods=['GET'])
def get_permissions(user_id):
    role = request.args.get('role', 'employee')
    
    perms = biometric_permissions.get_user_permissions(user_id, role)
    
    return {
        'user_id': user_id,
        'role': role,
        'permissions': perms
    }, 200
```

### POST `/api/biometric/check-permission`

Vérifie une permission spécifique.

```python
@app.route('/api/biometric/check-permission', methods=['POST'])
def check_permission():
    data = request.json
    
    check = biometric_permissions.check_permission(
        data['user_id'],
        data['role'],
        BiometricPermission[data['permission'].upper()]
    )
    
    return check, 200 if check['allowed'] else 403
```

### POST `/api/biometric/permissions/<user_id>/grant`

Accorde une permission personnalisée.

```python
@app.route('/api/biometric/permissions/<user_id>/grant', methods=['POST'])
def grant_permission(user_id):
    # Vérifier que c'est un admin
    if not is_admin(request.user):
        return {'error': 'Not authorized'}, 403
    
    data = request.json
    permission = BiometricPermission[data['permission'].upper()]
    
    biometric_permissions.grant_permission(user_id, permission)
    
    return {'status': 'granted'}, 200
```

### POST `/api/biometric/permissions/<user_id>/revoke`

Révoque une permission personnalisée.

```python
@app.route('/api/biometric/permissions/<user_id>/revoke', methods=['POST'])
def revoke_permission(user_id):
    if not is_admin(request.user):
        return {'error': 'Not authorized'}, 403
    
    data = request.json
    permission = BiometricPermission[data['permission'].upper()]
    
    biometric_permissions.revoke_permission(user_id, permission)
    
    return {'status': 'revoked'}, 200
```

### GET `/api/biometric/access-log`

Récupère le log d'accès (admin uniquement).

```python
@app.route('/api/biometric/access-log', methods=['GET'])
def get_access_log():
    if not is_admin(request.user):
        return {'error': 'Not authorized'}, 403
    
    user_id = request.args.get('user_id')
    permission = request.args.get('permission')
    limit = int(request.args.get('limit', 100))
    
    logs = biometric_permissions.get_access_log(user_id, permission, limit)
    
    return {'logs': logs, 'count': len(logs)}, 200
```

### GET `/api/biometric/export-config`

Exporte la configuration (admin uniquement).

```python
@app.route('/api/biometric/export-config', methods=['GET'])
def export_config():
    if not is_admin(request.user):
        return {'error': 'Not authorized'}, 403
    
    config = biometric_permissions.export_config()
    
    return config, 200
```

---

## 👥 Gestion des Rôles

### Structure des rôles

```python
ROLE_HIERARCHY = {
    'super_admin': {
        'permissions': 6,  # Toutes les permissions
        'description': 'Accès illimité'
    },
    'admin': {
        'permissions': 6,
        'description': 'Gestion complète'
    },
    'manager': {
        'permissions': 4,
        'description': 'Gestion restreinte'
    },
    'employee': {
        'permissions': 2,
        'description': 'Accès de base'
    },
    'guest': {
        'permissions': 0,
        'description': 'Pas d\'accès'
    }
}
```

### Permissions par rôle

| Permission | super_admin | admin | manager | employee | guest |
|-----------|-----------|-------|---------|----------|-------|
| USE_CAMERA | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| USE_MICROPHONE | ✅ | ✅ | ✅ | ⚠️ | ❌ |
| RECORD_FACE | ✅ | ✅ | ✅ | ✅ | ❌ |
| RECORD_VOICE | ✅ | ✅ | ⚠️ | ❌ | ❌ |
| ACCESS_BIOMETRIC_DATA | ✅ | ✅ | ✅ | ❌ | ❌ |
| VIEW_BIOMETRIC_LOGS | ✅ | ✅ | ❌ | ❌ | ❌ |

Légende: ✅ Autorisé | ⚠️ Avec consentement | ❌ Refusé

---

## 💾 Supprimer Persistance avec Base de Données

### Créer une table de permissions

```sql
CREATE TABLE biometric_permissions (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(255) NOT NULL,
    permission VARCHAR(50) NOT NULL,
    level INTEGER DEFAULT 2,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by VARCHAR(255),
    UNIQUE KEY unique_permission (user_id, permission),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE biometric_access_log (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(255) NOT NULL,
    permission VARCHAR(50),
    device VARCHAR(50),
    action VARCHAR(20),
    status VARCHAR(20),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### Intégrer avec la base de données

```python
from models.user import User
from core.database import db

class BiometricPermissionsManagerDB(BiometricPermissionsManager):
    """Version avec persistance DB"""
    
    def __init__(self):
        super().__init__()
        self.load_from_db()
    
    def load_from_db(self):
        """Charger les permissions depuis DB"""
        # SELECT * FROM biometric_permissions WHERE user_id = ?
        # ... charger depuis la base de données
        pass
    
    def grant_permission(self, user_id: str, permission: BiometricPermission):
        """Accorder et sauvegarder dans DB"""
        # Appel parent
        super().grant_permission(user_id, permission)
        
        # Sauvegarder dans DB
        # INSERT INTO biometric_permissions ...
        db.session.add(...)
        db.session.commit()
```

---

## 🧪 Tests

### Test unitaire

```python
import pytest
from core.biometric_permissions import (
    BiometricPermissionsManager,
    BiometricPermission
)

@pytest.fixture
def manager():
    return BiometricPermissionsManager()

def test_grant_permission(manager):
    manager.grant_permission('user1', BiometricPermission.USE_CAMERA)
    
    assert manager.has_permission('user1', BiometricPermission.USE_CAMERA)

def test_revoke_permission(manager):
    manager.grant_permission('user1', BiometricPermission.USE_MICROPHONE)
    manager.revoke_permission('user1', BiometricPermission.USE_MICROPHONE)
    
    assert not manager.has_permission('user1', BiometricPermission.USE_MICROPHONE)

def test_check_permission_returns_details(manager):
    manager.grant_permission('user1', BiometricPermission.RECORD_FACE)
    
    check = manager.check_permission('user1', 'employee', BiometricPermission.RECORD_FACE)
    
    assert check['allowed']
    assert check['user_id'] == 'user1'
    assert check['permission'] == BiometricPermission.RECORD_FACE.value
```

### Test d'intégration pour le client

```python
# test_client_permissions.py
from device_diagnostic import DeviceDiagnostic
from permissions_manager import PermissionsManager

def test_diagnostic_runs():
    diagnostic = DeviceDiagnostic()
    results = diagnostic.run_full_diagnostic()
    
    assert 'cameras' in results
    assert 'microphones' in results
    assert 'permissions' in results

def test_permissions_manager():
    manager = PermissionsManager()
    perms = manager.check_all_permissions()
    
    assert isinstance(perms, dict)
```

---

## 📊 Monitoring et Logs

### Configuration du logging

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging pour les permissions
logger = logging.getLogger('biometric_permissions')
logger.setLevel(logging.INFO)

handler = RotatingFileHandler(
    'logs/biometric_permissions.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)
```

### Extraction des métriques

```python
def get_permission_stats():
    """Statistiques sur les permissions"""
    logs = biometric_permissions.get_access_log(limit=10000)
    
    stats = {
        'total_checks': len(logs),
        'denied': len([l for l in logs if not l.get('allowed')]),
        'allowed': len([l for l in logs if l.get('allowed')]),
        'permissions': {},
        'users': set()
    }
    
    for log in logs:
        perm = log.get('permission', 'unknown')
        stats['permissions'][perm] = stats['permissions'].get(perm, 0) + 1
        stats['users'].add(log.get('user_id'))
    
    stats['users'] = len(stats['users'])
    
    return stats
```

---

## 🚀 Déploiement

### Configuration production

```python
# config.py
class ProductionConfig:
    # Cache plus long en production
    BIOMETRIC_CACHE_TTL = 30  # 30 minutes
    
    # Logs détaillés
    LOGGING_LEVEL = logging.INFO
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
```

### Variables d'environnement

```bash
# .env
BIOMETRIC_CACHE_TTL=30
BIOMETRIC_LOG_RETENTION=90  # jours
DATABASE_URL=postgresql://user:pass@host/db
```

---

## 📚 Ressources

- [BiometricPermissionsManager API](../core/biometric_permissions.py)
- [Device Diagnostic](./device_diagnostic.py)
- [Permissions Manager Client](./permissions_manager.py)
- [Guide d'utilisation](./DEVICE_SETUP_GUIDE.md)

---

**Version:** 1.0  
**Dernière mise à jour:** Mars 2026
