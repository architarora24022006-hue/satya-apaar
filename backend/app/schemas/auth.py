from typing import Optional
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    otp_code: Optional[str] = None

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    full_name: str
    email: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None

class TokenPayload(BaseModel):
    sub: str
    role: str
    email: str
    institution_id: Optional[str] = None
    exp: Optional[int] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str
    institution_id: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None
    is_active: bool
    mfa_enabled: bool

    class Config:
        from_attributes = True

class OTPRequest(BaseModel):
    email: EmailStr
    purpose: str = "LOGIN_MFA"

class OTPVerifyResponse(BaseModel):
    success: bool
    message: str
    simulated_otp: Optional[str] = None
