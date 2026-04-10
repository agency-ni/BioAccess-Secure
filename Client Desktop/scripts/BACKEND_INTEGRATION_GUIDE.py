"""
GUIDE D'INTÉGRATION - Permissions Biométriques dans le Backend

Ce fichier explique comment intégrer les permissions biométriques
dans votre application Flask existante.
"""

# ============================================================
# 1. INTÉGRATION DANS app.py
# ============================================================

"""
Modifiez votre app.py pour enregistrer les routes biométriques:

    from api.v1.biometric import register_biometric_routes
    
    # Dans create_app() ou __main__:
    register_biometric_routes(app)
    
    # Les routes seront disponibles à /api/v1/biometric/*
"""

# ============================================================
# 2. UTILISER LES PERMISSIONS DANS AUTH
# ============================================================

"""
Modifiez votre middleware d'authentification pour initialiser
les permissions lors de la connexion:

    from core.biometric_permissions import biometric_permissions, setup_default_permissions
    
    # Après authentification réussie (auth_service.py):
    
    def login(username, password):
        user = authenticate_user(username, password)
        if user:
            # Initialiser les permissions par défaut
            setup_default_permissions(user.id, user.role)
            
            # Retourner le token
            return create_token(user)
"""

# ============================================================
# 3. PROTÉGER LES ENDPOINTS BIOMÉTRIQUES
# ============================================================

"""
Utilisez les décorateurs dans vos services:

    from core.biometric_permissions import biometric_permissions, BiometricPermission
    
    class BiometricService:
        
        @biometric_permissions.require_camera_permission()
        def capture_face(self, user_id):
            # Vérification automatique de la permission
            # Code de capture...
            pass
        
        @biometric_permissions.require_microphone_permission()
        def record_voice(self, user_id):
            # Vérification automatique de la permission
            # Code d'enregistrement...
            pass
"""

# ============================================================
# 4. EXEMPLE D'INTÉGRATION COMPLÈTE
# ============================================================

"""
FICHIER: api/v1/auth.py (Avant)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password(user.password_hash, data['password']):
        token = create_token(user)
        return jsonify({'token': token}), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401


FICHIER: api/v1/auth.py (Après)

from core.biometric_permissions import setup_default_permissions

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password(user.password_hash, data['password']):
        # Initialiser les permissions biométriques
        setup_default_permissions(user.id, user.role)
        
        token = create_token(user)
        return jsonify({
            'token': token,
            'user_id': user.id,
            'role': user.role
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401
"""

# ============================================================
# 5. EXEMPLE - SERVICE BIOMÉTRIQUE
# ============================================================

"""
FICHIER: services/biometric_service.py

from core.biometric_permissions import biometric_permissions, BiometricPermission

class BiometricService:
    
    def capture_face(self, user_id):
        '''Capturer et enregistrer un visage'''
        
        # Vérifier la permission (peut aussi lever une exception)
        if not biometric_permissions.has_permission(user_id, BiometricPermission.RECORD_FACE):
            raise PermissionError(f"User {user_id} cannot record faces")
        
        # Capturer le visage
        face_data = self._capture_face_data()
        
        # Enregistrer en base de données
        biometric = Biometric(
            user_id=user_id,
            type='face',
            data=face_data,
            timestamp=datetime.now()
        )
        db.session.add(biometric)
        db.session.commit()
        
        return biometric
    
    def record_voice(self, user_id):
        '''Enregistrer et stocker la voix'''
        
        # Vérifier la permission
        if not biometric_permissions.has_permission(user_id, BiometricPermission.RECORD_VOICE):
            raise PermissionError(f"User {user_id} cannot record voice")
        
        # Enregistrer l'audio
        voice_data = self._record_audio_data()
        
        # Enregistrer en base de données
        biometric = Biometric(
            user_id=user_id,
            type='voice',
            data=voice_data,
            timestamp=datetime.now()
        )
        db.session.add(biometric)
        db.session.commit()
        
        return biometric
    
    def _capture_face_data(self):
        '''Implémenter la capture faciale'''
        pass
    
    def _record_audio_data(self):
        '''Implémenter l'enregistrement audio'''
        pass
"""

# ============================================================
# 6. EXEMPLE - ENDPOINT BIOMÉTRIQUE
# ============================================================

"""
FICHIER: api/v1/dashboard.py

from services.biometric_service import BiometricService
from core.biometric_permissions import biometric_permissions

biometric_service = BiometricService()

@dashboard_bp.route('/biometric/capture-face', methods=['POST'])
def capture_face():
    '''Capturer un visage'''
    
    user_id = request.headers.get('X-User-Id')
    
    try:
        # Vérifier la permission
        if not biometric_permissions.has_permission(user_id, 'use_camera'):
            return jsonify({
                'error': 'Camera access permission denied'
            }), 403
        
        # Capturer le visage
        result = biometric_service.capture_face(user_id)
        
        return jsonify({
            'success': True,
            'biometric_id': result.id,
            'timestamp': result.timestamp.isoformat()
        }), 200
    
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f"Error capturing face: {e}")
        return jsonify({'error': 'Capture failed'}), 500


@dashboard_bp.route('/biometric/record-voice', methods=['POST'])
def record_voice():
    '''Enregistrer la voix'''
    
    user_id = request.headers.get('X-User-Id')
    
    try:
        # Vérifier la permission
        if not biometric_permissions.has_permission(user_id, 'use_microphone'):
            return jsonify({
                'error': 'Microphone access permission denied'
            }), 403
        
        # Enregistrer la voix
        result = biometric_service.record_voice(user_id)
        
        return jsonify({
            'success': True,
            'biometric_id': result.id,
            'timestamp': result.timestamp.isoformat()
        }), 200
    
    except PermissionError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f"Error recording voice: {e}")
        return jsonify({'error': 'Recording failed'}), 500
"""

# ============================================================
# 7. MIDDLEWARE DE VÉRIFICATION
# ============================================================

"""
Optionnel: Créer un middleware pour vérifier les permissions automatiquement

FICHIER: api/middlewares/biometric_permissions_middleware.py

from functools import wraps
from flask import request, jsonify
from core.biometric_permissions import biometric_permissions

def require_biometric_permission(permission_name):
    '''Middleware pour vérifier les permissions biométriques'''
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = request.headers.get('X-User-Id')
            
            if not user_id:
                return jsonify({'error': 'User ID required'}), 401
            
            if not biometric_permissions.has_permission(user_id, permission_name):
                return jsonify({'error': 'Permission denied'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Utilisation:
@dashboard_bp.route('/biometric/capture-face', methods=['POST'])
@require_biometric_permission('use_camera')
def capture_face():
    '''Capturer un visage - Permission vérifiée automatiquement'''
    pass
"""

# ============================================================
# 8. TESTS
# ============================================================

"""
FICHIER: tests/test_biometric_permissions.py

import pytest
from core.biometric_permissions import biometric_permissions, BiometricPermission

def test_grant_permission():
    user_id = "test_user"
    biometric_permissions.grant_permission(user_id, BiometricPermission.USE_CAMERA)
    
    assert biometric_permissions.has_permission(user_id, BiometricPermission.USE_CAMERA)

def test_revoke_permission():
    user_id = "test_user"
    biometric_permissions.grant_permission(user_id, BiometricPermission.USE_CAMERA)
    biometric_permissions.revoke_permission(user_id, BiometricPermission.USE_CAMERA)
    
    assert not biometric_permissions.has_permission(user_id, BiometricPermission.USE_CAMERA)

def test_setup_default_permissions():
    from core.biometric_permissions import setup_default_permissions
    
    user_id = "test_employé"
    setup_default_permissions(user_id, "employé")
    
    perms = biometric_permissions.get_user_permissions(user_id)
    assert perms[BiometricPermission.USE_CAMERA.value]
    assert perms[BiometricPermission.USE_MICROPHONE.value]
    assert not perms[BiometricPermission.VIEW_BIOMETRIC_LOGS.value]

def test_api_check_permission(client):
    response = client.post('/api/v1/biometric/check-permission', json={
        'user_id': 'test_user',
        'permission': 'use_camera'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'has_permission' in data
"""

# ============================================================
# 9. CONFIGURATION RECOMMANDÉE
# ============================================================

"""
Dans votre app.py ou config.py, ajouter:

# Configuration des permissions biométriques
BIOMETRIC_PERMISSIONS_ENABLED = True
BIOMETRIC_CACHE_TTL = 300  # 5 minutes
BIOMETRIC_LOG_RETENTION = 30  # 30 jours

# Rôles et permissions par défaut
BIOMETRIC_DEFAULT_PERMISSIONS = {
    'super_admin': [
        'use_camera',
        'use_microphone', 
        'record_face',
        'record_voice',
        'access_biometric_data',
        'view_biometric_logs'
    ],
    'admin': [
        'use_camera',
        'use_microphone',
        'record_face',
        'record_voice', 
        'access_biometric_data'
    ],
    'employé': [
        'use_camera',
        'use_microphone',
        'record_face',
        'record_voice'
    ]
}
"""

# ============================================================
# 10. CHECKLIST D'INTÉGRATION
# ============================================================

"""
□ Importer biometric_permissions dans app.py
□ Enregistrer les routes biométriques
□ Mettre à jour le service d'authentification
□ Ajouter la vérification des permissions aux endpoints biométriques
□ Créer les tests unitaires
□ Documenter les permissions requises pour chaque endpoint
□ Configurer les logs d'accès
□ Tester avec différents rôles
□ Vérifier les rapports d'accès
□ Former les administrateurs à gérer les permissions
"""

# ============================================================
# 11. COMMANDES UTILES
# ============================================================

"""
# Vérifier les permissions d'un utilisateur
python -c "
from core.biometric_permissions import biometric_permissions
perms = biometric_permissions.get_user_permissions('user123')
for perm, value in perms.items():
    print(f'{perm}: {value}')
"

# Accorder une permission
python -c "
from core.biometric_permissions import biometric_permissions
from core.biometric_permissions import BiometricPermission
biometric_permissions.grant_permission('user123', BiometricPermission.USE_CAMERA)
print('Permission accordée')
"

# Voir les logs d'accès
python -c "
from core.biometric_permissions import biometric_permissions
logs = biometric_permissions.get_access_log()
for log in logs:
    print(log)
"
"""

print("✓ Guide d'intégration chargé avec succès")
