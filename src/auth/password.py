"""Hashing de contraseñas con PBKDF2-SHA256 (100k iteraciones)."""
import base64
import hashlib
import hmac
import os


_ITERATIONS = 100_000
_SALT_BYTES = 16
_HASH_BYTES = 32


def hash_password(password: str) -> str:
    """Devuelve `base64(salt):base64(hash)`."""
    salt = os.urandom(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS, dklen=_HASH_BYTES)
    return f"{base64.b64encode(salt).decode()}:{base64.b64encode(dk).decode()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        salt_b64, hash_b64 = stored_hash.split(":")
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS, dklen=_HASH_BYTES)
        return hmac.compare_digest(expected, actual)
    except (ValueError, TypeError):
        return False
