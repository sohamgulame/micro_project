from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth_schema import AuthResponse, LoginRequest, SignupRequest, UserProfile
from app.services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/signup", response_model=AuthResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = AuthService.create_user(db, payload)
    token = AuthService.create_access_token(user.id)
    return AuthResponse(access_token=token, user=UserProfile.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = AuthService.authenticate_user(db, payload)
    token = AuthService.create_access_token(user.id)
    return AuthResponse(access_token=token, user=UserProfile.model_validate(user))


@router.get("/me", response_model=UserProfile)
def me(user=Depends(get_current_user)) -> UserProfile:
    return UserProfile.model_validate(user)
