import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.auth_schema import LoginRequest, SignupRequest
from app.models.user import User

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
http_bearer = HTTPBearer(auto_error=False)


class AuthServiceError(Exception):
    pass


class AuthService:
    secret_key = os.getenv("JWT_SECRET_KEY", "change-this-in-env")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expires_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=AuthService.expires_minutes)
        payload = {"sub": str(user_id), "exp": expire}
        return jwt.encode(payload, AuthService.secret_key, algorithm=AuthService.algorithm)

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_device_key(db: Session, device_api_key: str) -> User | None:
        return db.query(User).filter(User.device_api_key == device_api_key).first()

    @staticmethod
    def create_user(db: Session, payload: SignupRequest) -> User:
        existing = AuthService.get_user_by_email(db, payload.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email is already registered.")

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=AuthService.hash_password(payload.password),
            device_api_key=secrets.token_urlsafe(24),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, payload: LoginRequest) -> User:
        user = AuthService.get_user_by_email(db, payload.email)
        if not user or not AuthService.verify_password(payload.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password.")
        return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, AuthService.secret_key, algorithms=[AuthService.algorithm])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token.") from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    return user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            AuthService.secret_key,
            algorithms=[AuthService.algorithm],
        )
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None

    return db.query(User).filter(User.id == user_id).first()
