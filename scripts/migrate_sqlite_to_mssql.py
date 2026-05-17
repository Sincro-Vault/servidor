"""Migra datos desde server.db (SQLite) hacia SQL Server.

Uso:
    python -m scripts.migrate_sqlite_to_mssql \
        --source sqlite:///./server.db \
        --target "mssql+pyodbc://sa:SincroVault2026!@localhost:1433/secretsdb?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"

Si no se pasan flags, usa SQLite local + el DATABASE_URL del .env como target.
"""
from __future__ import annotations

import argparse
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.database import Base
from src.models.fragment import Fragment
from src.models.user import User


def _make_session(url: str):
    engine = create_engine(
        url,
        connect_args={"check_same_thread": False} if url.startswith("sqlite") else {},
    )
    return engine, sessionmaker(bind=engine)()


def migrate(source_url: str, target_url: str) -> None:
    print(f"[*] Origen : {source_url}")
    print(f"[*] Destino: {target_url}")

    src_engine, src_session = _make_session(source_url)
    tgt_engine, tgt_session = _make_session(target_url)

    print("[*] Creando esquema en destino...")
    Base.metadata.create_all(bind=tgt_engine)

    print("[*] Copiando usuarios...")
    users = src_session.query(User).all()
    for u in users:
        tgt_session.merge(User(
            id=u.id,
            username=u.username,
            email=u.email,
            password_hash=u.password_hash,
            rsa_public_key_pem=u.rsa_public_key_pem,
            rsa_fingerprint=u.rsa_fingerprint,
            created_at=u.created_at,
        ))
    print(f"    -> {len(users)} usuarios")

    print("[*] Copiando fragmentos...")
    fragments = src_session.query(Fragment).all()
    for f in fragments:
        tgt_session.merge(Fragment(
            id=f.id,
            secret_id=f.secret_id,
            user_id=f.user_id,
            fragment_index=f.fragment_index,
            encrypted_fragment=f.encrypted_fragment,
            checksum=f.checksum,
            created_at=f.created_at,
            updated_at=f.updated_at,
        ))
    print(f"    -> {len(fragments)} fragmentos")

    tgt_session.commit()
    src_session.close()
    tgt_session.close()
    print("[OK] Migracion completada.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Migra SQLite -> SQL Server")
    parser.add_argument("--source", default="sqlite:///./server.db", help="URL SQLAlchemy origen")
    parser.add_argument("--target", default=settings.database_url, help="URL SQLAlchemy destino")
    args = parser.parse_args()

    try:
        migrate(args.source, args.target)
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
