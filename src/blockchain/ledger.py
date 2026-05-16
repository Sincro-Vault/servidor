"""Singleton del ledger blockchain compartido entre REST y gRPC."""
from src.blockchain.chain import Blockchain
from src.config import settings

ledger = Blockchain(
    ledger_path=settings.blockchain_ledger_path,
    difficulty=settings.blockchain_difficulty,
)
