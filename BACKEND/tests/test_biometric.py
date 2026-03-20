"""
Tests unitaires pour le service biométrique
"""

import pytest
import io
from app import create_app
from core.database import db
from models.user import User
from models.biometric import TemplateBiometrique
from services.biometric_service import BiometricService

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user(app):
    user = User(
        email='test@bioaccess.com',
        nom='Test',
        prenom='User',
        role='employe'
    )
    user.set_password('Test123!')
    db.session.add(user)
    db.session.commit()
    return user

def test_face_template_creation(test_user):
    """Test création template facial"""
    # Créer une image factice
    import cv2
    import numpy as np
    
    # Image noire de 100x100
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.jpg', img)
    image_data = buffer.tobytes()
    
    template = BiometricService.process_face_image(
        image_data, test_user.id
    )
    
    assert template is not None
    assert template.type == 'facial'
    assert template.utilisateur_id == test_user.id

def test_face_verification(test_user):
    """Test vérification faciale"""
    # Simuler la vérification
    result, score, error = BiometricService.verify_face(
        'fake_id', b'fake_image'
    )
    
    assert result is False
    assert score == 0.0
    assert error is not None