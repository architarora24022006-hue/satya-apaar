from enum import Enum
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

class UserRole(str, Enum):
    AICTE_ADMIN = "AICTE_ADMIN"
    REGIONAL_OFFICER = "REGIONAL_OFFICER"
    INSTITUTION_ADMIN = "INSTITUTION_ADMIN"
    UNIVERSITY_REGULATOR = "UNIVERSITY_REGULATOR"
    EMPLOYER_VERIFIER = "EMPLOYER_VERIFIER"
    STUDENT = "STUDENT"

# Define permission matrices / descriptions
ROLE_DESCRIPTIONS = {
    UserRole.AICTE_ADMIN: "Full national oversight, policy management, audit verification, and Sentinel control",
    UserRole.REGIONAL_OFFICER: "Regional monitoring, case escalations, institution inspections",
    UserRole.INSTITUTION_ADMIN: "Upload student batch, view error grid, fix data, request supernumerary exceptions",
    UserRole.UNIVERSITY_REGULATOR: "Affiliation monitoring, cross-college degree checks",
    UserRole.EMPLOYER_VERIFIER: "Selective disclosure background verification via signed claims/QR",
    UserRole.STUDENT: "Consent wallet management, view access history, download signed verifiable credential"
}

def get_db():
    # Deferred import to prevent circular dependencies
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_payload(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload

def get_current_user(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    from app.models.user import User
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return user

class RoleChecker:
    def __init__(self, allowed_roles: List[UserRole]):
        self.allowed_roles = allowed_roles

    def __call__(self, user = Depends(get_current_user)):
        if user.role not in [role.value for role in self.allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Requires one of {[r.value for r in self.allowed_roles]} privileges"
            )
        return user

def require_roles(*roles: UserRole):
    return RoleChecker(list(roles))
