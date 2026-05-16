"""Endpoints REST de autenticación."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from src.auth.jwt_handler import generate_token
from src.auth.password import hash_password, verify_password
from src.auth.rsa_validator import compute_fingerprint, import_public_key_pem
from src.blockchain.block import AuditEvent
from src.blockchain.ledger import ledger
from src.config import settings
from src.database import get_db
from src.models.user import User
from src.rest_api.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=400, detail=f"Usuario '{request.username}' ya existe")

    fingerprint = None
    pem_text = None
    if request.rsa_public_key_pem:
        try:
            import_public_key_pem(request.rsa_public_key_pem)
            pem_text = request.rsa_public_key_pem
            fingerprint = compute_fingerprint(request.rsa_public_key_pem)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    user = User(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        rsa_public_key_pem=pem_text,
        rsa_fingerprint=fingerprint,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    ledger.add_event(AuditEvent(user_id=user.id, action="register", result="success"))

    return RegisterResponse(user_id=user.id, username=user.username, fingerprint=fingerprint)


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, http_request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()

    ip = http_request.client.host if http_request.client else None

    if not user or not verify_password(request.password, user.password_hash):
        ledger.add_event(AuditEvent(
            user_id=request.username,
            action="login",
            result="denied",
            reason="credenciales incorrectas",
            ip_address=ip,
        ))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    # Validación opcional del certificado RSA
    if request.rsa_public_key_pem and user.rsa_fingerprint:
        provided_fp = compute_fingerprint(request.rsa_public_key_pem)
        if provided_fp != user.rsa_fingerprint:
            ledger.add_event(AuditEvent(
                user_id=user.id,
                action="login",
                result="denied",
                reason="certificado RSA no coincide",
                ip_address=ip,
            ))
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Certificado RSA no coincide")

    token = generate_token(user.id, user.username)
    ledger.add_event(AuditEvent(user_id=user.id, action="login", result="success", ip_address=ip))

    return LoginResponse(
        access_token=token,
        expires_in_seconds=settings.jwt_expiration_minutes * 60,
        user_id=user.id,
        username=user.username,
    )
