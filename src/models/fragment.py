"""Modelo del fragmento B (almacenado en el servidor)."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, LargeBinary, String

from src.database import Base


class Fragment(Base):
    __tablename__ = "fragments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    secret_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    fragment_index = Column(Integer, nullable=False)
    encrypted_fragment = Column(LargeBinary, nullable=False)
    checksum = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
