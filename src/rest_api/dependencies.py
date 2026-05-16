"""Dependencias compartidas: extracción de JWT desde header Authorization."""
from fastapi import Depends, Header, HTTPException, status

from src.auth.jwt_handler import decode_token


def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token requerido")
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido o expirado")
    return payload
