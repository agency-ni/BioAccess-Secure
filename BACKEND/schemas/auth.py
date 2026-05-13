from pydantic import BaseModel

class LoginRequest(BaseModel):
    email: str
    password: str
    remember: bool = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict = {}

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    pass

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

class BiometricEnrollmentRequest(BaseModel):
    user_id: int
    template_type: str
    template_data: str