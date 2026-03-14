"""
Tests unitaires pour l'authentification
"""

import pytest
from app import create_app
from core.database import db
from models.user import User

@pytest.fixture
def client():
    app = create_app('testing')
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

def test_login_success(client):
    """Test connexion réussie"""
    # Créer un utilisateur de test
    user = User(
        email='test@bioaccess.com',
        nom='Test',
        prenom='User',
        role='admin'
    )
    user.set_password('Test123!')
    db.session.add(user)
    db.session.commit()
    
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@bioaccess.com',
        'password': 'Test123!'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'access_token' in data
    assert data['user']['email'] == 'test@bioaccess.com'

def test_login_invalid_password(client):
    """Test mot de passe incorrect"""
    user = User(
        email='test@bioaccess.com',
        nom='Test',
        prenom='User'
    )
    user.set_password('Test123!')
    db.session.add(user)
    db.session.commit()
    
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@bioaccess.com',
        'password': 'WrongPass123!'
    })
    
    assert response.status_code == 401

def test_login_invalid_email(client):
    """Test email inexistant"""
    response = client.post('/api/v1/auth/login', json={
        'email': 'nobody@bioaccess.com',
        'password': 'Test123!'
    })
    
    assert response.status_code == 401