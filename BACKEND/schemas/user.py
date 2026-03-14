"""
Schémas Pydantic pour la gestion des utilisateurs
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    """Base pour les utilisateurs"""
    email: EmailStr
    nom: str = Field(..., min_length=1, max_length=100)
    prenom: str = Field(..., min_length=1, max_length=100)
    departement: Optional[str] = None
    role: str = "employe"

class UserCreate(UserBase):
    """Création d'utilisateur"""
    password: str = Field(..., min_length=8)
    
    @validator('password')
    def validate_password(cls, v):
        import re
        if not re.search(r'[A-Z]', v):
            raise ValueError('Doit contenir une majuscule')
        if not re.search(r'[0-9]', v):
            raise ValueError('Doit contenir un chiffre')
        if not re.search(r'[@$!%*?&]', v):
            raise ValueError('Doit contenir un caractère spécial')
        return v

class UserUpdate(BaseModel):
    """Mise à jour d'utilisateur"""
    nom: Optional[str] = Field(None, min_length=1)
    prenom: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    departement: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """Réponse utilisateur (sans données sensibles)"""
    id: str
    is_active: bool
    email_verified: bool
    twofa_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    full_name: str
    
    class Config:
        orm_mode = True

class UserListResponse(BaseModel):
    """Liste paginée d'utilisateurs"""
    total: int
    page: int
    per_page: int
    users: List[UserResponse]

class UserStats(BaseModel):
    """Statistiques d'un utilisateur"""
    total_logins: int
    failed_logins: int
    success_rate: float
    last_login: Optional[datetime]
    last_failed: Optional[datetime]