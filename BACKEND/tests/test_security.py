"""
Tests de sécurité
"""

import pytest
from app import create_app
from core.security import SecurityManager

def test_password_hashing():
    """Test hash et vérification de mot de passe"""
    password = "Test123!@#"
    hashed = SecurityManager.hash_password(password)
    
    assert hashed != password
    assert SecurityManager.check_password(password, hashed) is True
    assert SecurityManager.check_password("wrong", hashed) is False

def test_jwt_tokens():
    """Test génération et validation JWT"""
    token = SecurityManager.generate_jwt_token(
        'user123', 'admin', token_type='access'
    )
    
    assert token is not None
    
    payload = SecurityManager.decode_jwt_token(token)
    assert payload is not None
    assert payload['sub'] == 'user123'
    assert payload['role'] == 'admin'

def test_csrf_token():
    """Test génération CSRF"""
    token1 = SecurityManager.generate_csrf_token()
    token2 = SecurityManager.generate_csrf_token()
    
    assert token1 != token2
    assert len(token1) > 20

def test_sanitization():
    """Test sanitization XSS"""
    dirty = "<script>alert('xss')</script>"
    clean = SecurityManager.sanitize_input(dirty)
    
    assert '<' not in clean
    assert '>' not in clean
    assert 'script' not in clean