"""Endpoints REST de fragmentos. Equivalente a los métodos gRPC."""
import base64

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from src.blockchain.block import AuditEvent
from src.blockchain.ledger import ledger
from src.database import get_db
from src.models.fragment import Fragment
from src.rest_api.dependencies import get_current_user
from src.rest_api.schemas import (
    FragmentMetadata,
    GetFragmentResponse,
    StoreFragmentRequest,
    StoreFragmentResponse,
)

router = APIRouter(prefix="/api/fragments", tags=["fragments"])


@router.post("", response_model=StoreFragmentResponse, status_code=201)
def store_fragment(
    request: StoreFragmentRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        encrypted_bytes = base64.b64decode(request.encrypted_fragment_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="encrypted_fragment_b64 inválido")

    fragment = Fragment(
        secret_id=request.secret_id,
        user_id=user["sub"],
        fragment_index=request.fragment_index,
        encrypted_fragment=encrypted_bytes,
        checksum=request.checksum,
    )
    db.add(fragment)
    db.commit()
    db.refresh(fragment)

    block = ledger.add_event(AuditEvent(
        user_id=user["sub"],
        action="store_fragment",
        secret_id=request.secret_id,
        ip_address=http_request.client.host if http_request.client else None,
        latitude=request.latitude,
        longitude=request.longitude,
        result="success",
    ))

    return StoreFragmentResponse(success=True, fragment_id=fragment.id, ledger_block_hash=block.hash)


@router.get("/{secret_id}", response_model=GetFragmentResponse)
def get_fragment(
    secret_id: str,
    http_request: Request,
    latitude: float | None = None,
    longitude: float | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    fragment = (
        db.query(Fragment)
        .filter(Fragment.secret_id == secret_id, Fragment.user_id == user["sub"])
        .first()
    )
    ip = http_request.client.host if http_request.client else None

    if not fragment:
        block = ledger.add_event(AuditEvent(
            user_id=user["sub"],
            action="get_fragment",
            secret_id=secret_id,
            ip_address=ip,
            result="denied",
            reason="fragmento no encontrado",
        ))
        return GetFragmentResponse(success=False, ledger_block_hash=block.hash, deny_reason="no encontrado")

    block = ledger.add_event(AuditEvent(
        user_id=user["sub"],
        action="get_fragment",
        secret_id=secret_id,
        ip_address=ip,
        latitude=latitude,
        longitude=longitude,
        result="success",
    ))

    return GetFragmentResponse(
        success=True,
        fragment_index=fragment.fragment_index,
        encrypted_fragment_b64=base64.b64encode(fragment.encrypted_fragment).decode(),
        checksum=fragment.checksum,
        ledger_block_hash=block.hash,
    )


@router.delete("/{secret_id}")
def delete_fragment(
    secret_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    deleted = (
        db.query(Fragment)
        .filter(Fragment.secret_id == secret_id, Fragment.user_id == user["sub"])
        .delete()
    )
    db.commit()

    block = ledger.add_event(AuditEvent(
        user_id=user["sub"],
        action="delete_fragment",
        secret_id=secret_id,
        result="success" if deleted else "denied",
        reason=None if deleted else "fragmento no encontrado",
    ))
    return {"success": bool(deleted), "ledger_block_hash": block.hash}


@router.get("", response_model=list[FragmentMetadata])
def list_fragments(
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    fragments = db.query(Fragment).filter(Fragment.user_id == user["sub"]).all()
    return [
        FragmentMetadata(
            secret_id=f.secret_id,
            fragment_index=f.fragment_index,
            checksum=f.checksum,
            created_at=f.created_at,
        )
        for f in fragments
    ]
