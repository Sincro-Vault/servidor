"""Modelo de usuario del servidor."""
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from src.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), nullable=True)
    password_hash = Column(String(255), nullable=False)
    rsa_public_key_pem = Column(Text, nullable=True)
    rsa_fingerprint = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
