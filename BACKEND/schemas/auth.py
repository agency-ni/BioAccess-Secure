"""
Schémas Pydantic pour la validation des données d'authentification
"""

from pydantic import BaseModel, EmailStr, Field, validator
import re

class LoginRequest(BaseModel):
    """Schéma de requête de connexion"""
    email: EmailStr = Field(..., description="Email de l'utilisateur")
    password: str = Field(..., min_length=8, max_length=128, description="Mot de passe")
    remember: bool = Field(False, description="Se souvenir de moi")
    
    @validator('password')
    def validate_password(cls, v):
        """Validation supplémentaire du mot de passe"""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Le mot de passe doit contenir au moins une majuscule')
        if not re.search(r'[0-9]', v):
            raise ValueError('Le mot de passe doit contenir au moins un chiffre')
        if not re.search(r'[@$!%*?&]', v):
            raise ValueError('Le mot de passe doit contenir au moins un caractère spécial')
        return v

class LoginResponse(BaseModel):
    """Schéma de réponse de connexion"""
    access_token: str
    refresh_token: str = None
    token_type: str = "bearer"
    expires_in: int
    user: dict

class RefreshTokenRequest(BaseModel):
    """Schéma pour rafraîchir un token"""
    refresh_token: str

class LogoutRequest(BaseModel):
    """Schéma pour déconnexion"""
    refresh_token: str = None

class ChangePasswordRequest(BaseModel):
    """Changement de mot de passe"""
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)
    confirm_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Doit contenir une majuscule')
        if not re.search(r'[0-9]', v):
            raise ValueError('Doit contenir un chiffre')
        if not re.search(r'[@$!%*?&]', v):
            raise ValueError('Doit contenir un caractère spécial')
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Les mots de passe ne correspondent pas')
        return v

class ForgotPasswordRequest(BaseModel):
    """Demande de réinitialisation"""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Réinitialisation avec token"""
    token: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str