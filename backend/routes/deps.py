"""Shared FastAPI dependencies — primarily JWT verification."""
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()


def require_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """Verify Bearer JWT token on protected endpoints.

    FastAPI calls this automatically when a route lists it in Depends().
    If the token is missing, expired, or tampered with, it returns 401
    before the route handler even runs.
    """
    token = credentials.credentials
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
