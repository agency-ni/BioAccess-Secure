"""
Tests pour le core - Database
"""

import pytest
from app import create_app
from core.database import db, health_check, init_db
from models.user import User
from datetime import datetime

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

class TestDatabase:
    """Tests pour la base de données"""
    
    def test_db_connection(self, app):
        """Test connexion à la base de données"""
        with app.app_context():
            result = health_check()
            assert result is True
    
    def test_db_create_user(self, app):
        """Test création utilisateur en DB"""
        with app.app_context():
            user = User(
                email='test@bioaccess.com',
                nom='Test',
                prenom='User'
            )
            user.set_password('Test123!')
            db.session.add(user)
            db.session.commit()
            
            fetched = User.query.filter_by(email='test@bioaccess.com').first()
            assert fetched is not None
            assert fetched.email == 'test@bioaccess.com'
    
    def test_db_user_duplicate_email(self, app):
        """Test impossibilité emails dupliqués"""
        with app.app_context():
            user1 = User(email='test@bioaccess.com', nom='Test', prenom='User')
            user1.set_password('Test123!')
            db.session.add(user1)
            db.session.commit()
            
            user2 = User(email='test@bioaccess.com', nom='Another', prenom='User')
            db.session.add(user2)
            
            with pytest.raises(Exception):  # IntegrityError
                db.session.commit()
    
    def test_db_user_update(self, app):
        """Test mise à jour utilisateur"""
        with app.app_context():
            user = User(email='test@bioaccess.com', nom='Test', prenom='User')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            user.nom = 'Updated'
            db.session.commit()
            
            fetched = User.query.get(user_id)
            assert fetched.nom == 'Updated'
    
    def test_db_user_delete(self, app):
        """Test suppression utilisateur"""
        with app.app_context():
            user = User(email='test@bioaccess.com', nom='Test', prenom='User')
            db.session.add(user)
            db.session.commit()
            user_id = user.id
            
            db.session.delete(user)
            db.session.commit()
            
            fetched = User.query.get(user_id)
            assert fetched is None
    
    def test_db_pagination(self, app):
        """Test pagination"""
        with app.app_context():
            for i in range(25):
                user = User(email=f'test{i}@bioaccess.com', nom='Test', prenom=f'User{i}')
                db.session.add(user)
            db.session.commit()
            
            page1 = User.query.paginate(page=1, per_page=10)
            assert len(page1.items) == 10
            assert page1.total == 25
            assert page1.pages == 3
