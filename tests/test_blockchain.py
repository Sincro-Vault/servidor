"""Pruebas del blockchain ledger."""
import tempfile
from pathlib import Path

from src.blockchain.block import AuditEvent
from src.blockchain.chain import Blockchain


def test_genesis_block_created():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = Blockchain(ledger_path=str(Path(tmpdir) / "ledger.json"), difficulty=1)
        assert len(ledger.chain) == 1
        assert ledger.chain[0].event.action == "genesis"
        assert ledger.is_valid()


def test_add_event_links_correctly():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = Blockchain(ledger_path=str(Path(tmpdir) / "ledger.json"), difficulty=1)
        block1 = ledger.add_event(AuditEvent(user_id="u1", action="login", result="success"))
        block2 = ledger.add_event(AuditEvent(user_id="u1", action="store_fragment", result="success"))

        assert block1.previous_hash == ledger.chain[0].hash
        assert block2.previous_hash == block1.hash
        assert ledger.is_valid()


def test_tampering_invalidates_chain():
    with tempfile.TemporaryDirectory() as tmpdir:
        ledger = Blockchain(ledger_path=str(Path(tmpdir) / "ledger.json"), difficulty=1)
        ledger.add_event(AuditEvent(user_id="u1", action="login", result="success"))
        ledger.add_event(AuditEvent(user_id="u1", action="get_fragment", result="success"))

        # Manipular un evento sin recalcular hashes
        ledger.chain[1].event.user_id = "atacante"
        assert not ledger.is_valid()


def test_persistence_roundtrip():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir) / "ledger.json")
        ledger1 = Blockchain(ledger_path=path, difficulty=1)
        ledger1.add_event(AuditEvent(user_id="u1", action="login", result="success"))
        size1 = len(ledger1.chain)

        # Crear nueva instancia que cargue desde disco
        ledger2 = Blockchain(ledger_path=path, difficulty=1)
        assert len(ledger2.chain) == size1
        assert ledger2.is_valid()
