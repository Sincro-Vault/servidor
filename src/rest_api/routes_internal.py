"""Endpoints internos para comunicación servidor-a-servidor.

El backend cliente (.NET) llama a estos endpoints para almacenar y recuperar
el Fragmento B de cada secreto. En producción esto sería gRPC + TLS 1.3.

Autenticación por API key compartida en header X-Internal-Token.
"""
import base64
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.blockchain.block import AuditEvent
from src.blockchain.ledger import ledger
from src.database import get_db
from src.models.fragment import Fragment
from src.models.user import User

router = APIRouter(prefix="/api/internal", tags=["internal"])

# En producción, leer de env var
INTERNAL_API_KEY = "shared-secret-cliente-servidor-2026"


def verify_internal_token(x_internal_token: str = Header(default="")):
    if x_internal_token != INTERNAL_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token interno inválido")


class FragmentPayload(BaseModel):
    user_id: str
    username: str
    secret_id: str
    fragment_index: int
    encrypted_fragment_b64: str
    checksum: str


@router.post("/fragments", status_code=201)
def store_fragment_internal(
    payload: FragmentPayload,
    http_request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_internal_token),
):
    # Crear usuario puente si no existe (asociado al ID del cliente .NET)
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        # Si ya existe otro user con ese username (cliente fue recreado, IDs cambiaron)
        # actualizamos el ID para reflejar el del cliente actual.
        existing_by_name = db.query(User).filter(User.username == payload.username).first()
        if existing_by_name:
            existing_by_name.id = payload.user_id
            db.commit()
            user = existing_by_name
        else:
            user = User(
                id=payload.user_id,
                username=payload.username,
                password_hash="bridge-account",
            )
            db.add(user)
            db.commit()

    try:
        encrypted_bytes = base64.b64decode(payload.encrypted_fragment_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="encrypted_fragment_b64 inválido")

    fragment = Fragment(
        id=str(uuid.uuid4()),
        secret_id=payload.secret_id,
        user_id=payload.user_id,
        fragment_index=payload.fragment_index,
        encrypted_fragment=encrypted_bytes,
        checksum=payload.checksum,
    )
    db.add(fragment)
    db.commit()

    block = ledger.add_event(AuditEvent(
        user_id=payload.user_id,
        action="store_fragment",
        secret_id=payload.secret_id,
        ip_address=http_request.client.host if http_request.client else None,
        result="success",
    ))

    return {"success": True, "fragment_id": fragment.id, "ledger_block_hash": block.hash}


@router.get("/fragments/{user_id}/{secret_id}")
def get_fragment_internal(
    user_id: str,
    secret_id: str,
    http_request: Request,
    db: Session = Depends(get_db),
    _=Depends(verify_internal_token),
):
    fragment = (
        db.query(Fragment)
        .filter(Fragment.secret_id == secret_id, Fragment.user_id == user_id)
        .first()
    )
    if not fragment:
        block = ledger.add_event(AuditEvent(
            user_id=user_id, action="get_fragment",
            secret_id=secret_id, result="denied",
            reason="fragmento no encontrado",
        ))
        raise HTTPException(status_code=404, detail={"deny_reason": "no encontrado", "ledger_block_hash": block.hash})

    block = ledger.add_event(AuditEvent(
        user_id=user_id, action="get_fragment",
        secret_id=secret_id, result="success",
        ip_address=http_request.client.host if http_request.client else None,
    ))

    return {
        "success": True,
        "fragment_index": fragment.fragment_index,
        "encrypted_fragment_b64": base64.b64encode(fragment.encrypted_fragment).decode(),
        "checksum": fragment.checksum,
        "ledger_block_hash": block.hash,
    }


@router.delete("/fragments/{user_id}/{secret_id}")
def delete_fragment_internal(
    user_id: str,
    secret_id: str,
    db: Session = Depends(get_db),
    _=Depends(verify_internal_token),
):
    deleted = (
        db.query(Fragment)
        .filter(Fragment.secret_id == secret_id, Fragment.user_id == user_id)
        .delete()
    )
    db.commit()

    block = ledger.add_event(AuditEvent(
        user_id=user_id, action="delete_fragment",
        secret_id=secret_id,
        result="success" if deleted else "denied",
    ))
    return {"success": bool(deleted), "ledger_block_hash": block.hash}
