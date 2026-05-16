"""Cadena de bloques con persistencia en JSON.

Garantiza:
- Inmutabilidad: cada bloque referencia el hash del anterior.
- Verificabilidad: `is_valid()` recorre toda la cadena.
- Proof-of-work simple: difficulty configurable.
"""
import json
import threading
from pathlib import Path

from src.blockchain.block import AuditEvent, Block, now_iso


class Blockchain:
    def __init__(self, ledger_path: str, difficulty: int = 2) -> None:
        self.ledger_path = Path(ledger_path)
        self.difficulty = difficulty
        self._lock = threading.Lock()
        self.chain: list[Block] = []
        self._load_or_create_genesis()

    def _load_or_create_genesis(self) -> None:
        if self.ledger_path.exists():
            with self.ledger_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.chain = [Block.from_dict(b) for b in data]
        else:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            genesis_event = AuditEvent(user_id="system", action="genesis", result="success")
            genesis = Block(index=0, timestamp=now_iso(), event=genesis_event, previous_hash="0")
            genesis.mine(self.difficulty)
            self.chain = [genesis]
            self._persist()

    def add_event(self, event: AuditEvent) -> Block:
        with self._lock:
            previous = self.chain[-1]
            block = Block(
                index=previous.index + 1,
                timestamp=now_iso(),
                event=event,
                previous_hash=previous.hash,
            )
            block.mine(self.difficulty)
            self.chain.append(block)
            self._persist()
            return block

    def is_valid(self) -> bool:
        prefix = "0" * self.difficulty
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.previous_hash != previous.hash:
                return False
            if current.hash != current.compute_hash():
                return False
            if not current.hash.startswith(prefix):
                return False
        return True

    def get_events(self, limit: int = 100, user_id: str | None = None) -> list[dict]:
        blocks = self.chain[-limit:] if limit else self.chain
        result = [b.to_dict() for b in blocks]
        if user_id:
            result = [b for b in result if b["event"]["user_id"] == user_id]
        return list(reversed(result))

    def _persist(self) -> None:
        with self.ledger_path.open("w", encoding="utf-8") as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=2)
