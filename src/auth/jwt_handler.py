"""Generación y validación de JWT (10 min de expiración)."""
from datetime import datetime, timedelta, timezone

import jwt

from src.config import settings


def generate_token(user_id: str, username: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expiration_minutes),
        "iss": "sincrovault-servidor",
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict | None:
    """Devuelve el payload si el token es válido, None si expiró o es inválido."""
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
