import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from jose import jwt
from passlib.context import CryptContext

router = APIRouter()

# bcrypt context for verifying the hashed password stored in the env var.
# The Streamlit app used a plaintext password — here we require the admin to
# set APP_PASSWORD_HASH (a bcrypt hash). See README for how to generate one.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def create_access_token(data: dict, expires_delta: timedelta) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload.update({"exp": expire})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    password_hash = os.getenv("APP_PASSWORD_HASH", "")

    # Fallback: if no hash is set, accept the plaintext APP_PASSWORD directly.
    # This lets the app work without re-hashing during migration.
    plaintext_password = os.getenv("APP_PASSWORD", "")

    if password_hash:
        valid = pwd_context.verify(body.password, password_hash)
    elif plaintext_password:
        valid = body.password == plaintext_password
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No password configured on server.",
        )

    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
        )

    token = create_access_token(
        data={"sub": "user"},
        expires_delta=timedelta(hours=TOKEN_EXPIRE_HOURS),
    )
    return TokenResponse(access_token=token)
