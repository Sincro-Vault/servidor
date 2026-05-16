"""Endpoints REST para consultar el ledger blockchain de auditoría."""
from fastapi import APIRouter, Depends

from src.blockchain.ledger import ledger
from src.rest_api.dependencies import get_current_user

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("")
def list_events(limit: int = 100, user_id: str | None = None, _: dict = Depends(get_current_user)):
    """Lista los eventos del ledger, en orden cronológico inverso."""
    return {
        "valid": ledger.is_valid(),
        "total_blocks": len(ledger.chain),
        "events": ledger.get_events(limit=limit, user_id=user_id),
    }


@router.get("/validate")
def validate_chain(_: dict = Depends(get_current_user)):
    """Recorre toda la cadena y verifica su integridad."""
    return {"valid": ledger.is_valid(), "total_blocks": len(ledger.chain)}
