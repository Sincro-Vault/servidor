"""Validación e identificación de certificados RSA del cliente."""
import hashlib

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def import_public_key_pem(pem_data: bytes | str) -> rsa.RSAPublicKey:
    """Importa una clave pública RSA desde PEM. Lanza ValueError si es inválida."""
    if isinstance(pem_data, str):
        pem_data = pem_data.encode("utf-8")
    try:
        key = serialization.load_pem_public_key(pem_data)
    except Exception as exc:
        raise ValueError(f"PEM RSA inválido: {exc}") from exc

    if not isinstance(key, rsa.RSAPublicKey):
        raise ValueError("La clave no es RSA")

    if key.key_size < 2048:
        raise ValueError(f"Tamaño de clave RSA insuficiente: {key.key_size} bits (mínimo 2048)")

    return key


def compute_fingerprint(pem_data: bytes | str) -> str:
    """SHA-256 del PEM, en formato `AA:BB:CC:...`."""
    if isinstance(pem_data, str):
        pem_data = pem_data.encode("utf-8")
    digest = hashlib.sha256(pem_data).hexdigest().upper()
    return ":".join(digest[i : i + 2] for i in range(0, len(digest), 2))
