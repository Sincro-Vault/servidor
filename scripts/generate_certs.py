"""Genera certificados TLS auto-firmados para desarrollo del servidor gRPC.

Ejecutar: python scripts/generate_certs.py
Salida: certs/server.crt y certs/server.key
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

ROOT = Path(__file__).resolve().parent.parent
CERTS_DIR = ROOT / "certs"


def main():
    CERTS_DIR.mkdir(parents=True, exist_ok=True)
    cert_path = CERTS_DIR / "server.crt"
    key_path = CERTS_DIR / "server.key"

    if cert_path.exists() and key_path.exists():
        print(f"Certificados ya existen en {CERTS_DIR}. Borra los archivos para regenerar.")
        return

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CO"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Bogota"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "SincroVault"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("localhost")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    with key_path.open("wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    with cert_path.open("wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    print(f"Certificados generados:\n  {cert_path}\n  {key_path}")
    print("Recuerda poner TLS_ENABLED=true en tu .env para activar TLS en gRPC.")


if __name__ == "__main__":
    main()
