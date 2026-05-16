"""DTOs Pydantic para la API REST."""
from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str
    rsa_public_key_pem: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    expires_in_seconds: int
    user_id: str
    username: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None
    rsa_public_key_pem: str | None = None


class RegisterResponse(BaseModel):
    user_id: str
    username: str
    fingerprint: str | None = None


class StoreFragmentRequest(BaseModel):
    secret_id: str
    fragment_index: int
    encrypted_fragment_b64: str  # base64 del fragmento cifrado
    checksum: str
    latitude: float | None = None
    longitude: float | None = None
    ip_address: str | None = None


class StoreFragmentResponse(BaseModel):
    success: bool
    fragment_id: str
    ledger_block_hash: str


class GetFragmentResponse(BaseModel):
    success: bool
    fragment_index: int | None = None
    encrypted_fragment_b64: str | None = None
    checksum: str | None = None
    ledger_block_hash: str
    deny_reason: str | None = None


class FragmentMetadata(BaseModel):
    secret_id: str
    fragment_index: int
    checksum: str
    created_at: datetime


class AuditEntry(BaseModel):
    index: int
    timestamp: str
    user_id: str
    action: str
    secret_id: str | None
    ip_address: str | None
    result: str
    hash: str
    previous_hash: str
