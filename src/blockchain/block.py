"""Bloque individual del ledger blockchain de auditoría."""
import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


@dataclass
class AuditEvent:
    """Evento que se registra en un bloque (intento de acceso/operación)."""
    user_id: str
    action: str  # "login" | "store_fragment" | "get_fragment" | "delete_fragment" | "denied"
    secret_id: str | None = None
    ip_address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    result: str = "success"  # "success" | "denied" | "error"
    reason: str | None = None


@dataclass
class Block:
    index: int
    timestamp: str
    event: AuditEvent
    previous_hash: str
    nonce: int = 0
    hash: str = field(default="")

    def __post_init__(self) -> None:
        if not self.hash:
            self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        """SHA-256 sobre los campos serializados (excluyendo el propio hash)."""
        payload = {
            "index": self.index,
            "timestamp": self.timestamp,
            "event": asdict(self.event),
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }
        serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def mine(self, difficulty: int) -> None:
        """Proof-of-work simple: encuentra nonce tal que el hash empiece con `difficulty` ceros."""
        prefix = "0" * difficulty
        while not self.hash.startswith(prefix):
            self.nonce += 1
            self.hash = self.compute_hash()

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "event": asdict(self.event),
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Block":
        event_data = data["event"]
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            event=AuditEvent(**event_data),
            previous_hash=data["previous_hash"],
            nonce=data.get("nonce", 0),
            hash=data["hash"],
        )


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
