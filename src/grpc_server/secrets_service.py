"""Implementación de los métodos gRPC del SecretsServer.

Refleja el .proto en `proto/secrets.proto`. Los stubs Python se generan
ejecutando `python scripts/generate_grpc.py` (crea `secrets_pb2.py` y
`secrets_pb2_grpc.py` en `src/grpc_server/generated/`).
"""
import base64

import grpc

from src.auth.jwt_handler import decode_token, generate_token
from src.auth.password import hash_password, verify_password
from src.auth.rsa_validator import compute_fingerprint, import_public_key_pem
from src.blockchain.block import AuditEvent
from src.blockchain.ledger import ledger
from src.config import settings
from src.database import SessionLocal
from src.models.fragment import Fragment
from src.models.user import User

# Imports de los stubs generados (existirán tras correr scripts/generate_grpc.py)
try:
    from src.grpc_server.generated import secrets_pb2, secrets_pb2_grpc
except ImportError:
    secrets_pb2 = None
    secrets_pb2_grpc = None


def _validate_jwt(token: str) -> dict | None:
    return decode_token(token)


def _geo_to_kwargs(geo) -> dict:
    if geo is None:
        return {}
    return {
        "latitude": geo.latitude if geo.latitude else None,
        "longitude": geo.longitude if geo.longitude else None,
        "ip_address": geo.ip_address or None,
    }


if secrets_pb2_grpc is not None:

    class SecretsServerImpl(secrets_pb2_grpc.SecretsServerServicer):

        def Login(self, request, context):
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.username == request.username).first()
                if not user or not verify_password(request.password, user.password_hash):
                    ledger.add_event(AuditEvent(
                        user_id=request.username, action="login",
                        result="denied", reason="credenciales incorrectas",
                    ))
                    context.abort(grpc.StatusCode.UNAUTHENTICATED, "Credenciales incorrectas")

                if request.rsa_public_key_pem and user.rsa_fingerprint:
                    fp = compute_fingerprint(bytes(request.rsa_public_key_pem))
                    if fp != user.rsa_fingerprint:
                        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Certificado RSA no coincide")

                token = generate_token(user.id, user.username)
                ledger.add_event(AuditEvent(user_id=user.id, action="login", result="success"))
                return secrets_pb2.LoginResponse(
                    access_token=token,
                    expires_in_seconds=settings.jwt_expiration_minutes * 60,
                    user_id=user.id,
                )
            finally:
                db.close()

        def Register(self, request, context):
            db = SessionLocal()
            try:
                if db.query(User).filter(User.username == request.username).first():
                    context.abort(grpc.StatusCode.ALREADY_EXISTS, "Usuario ya existe")

                fingerprint = None
                pem_text = None
                if request.rsa_public_key_pem:
                    pem_bytes = bytes(request.rsa_public_key_pem)
                    try:
                        import_public_key_pem(pem_bytes)
                        pem_text = pem_bytes.decode("utf-8")
                        fingerprint = compute_fingerprint(pem_bytes)
                    except ValueError as exc:
                        context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))

                user = User(
                    username=request.username,
                    email=request.email or None,
                    password_hash=hash_password(request.password),
                    rsa_public_key_pem=pem_text,
                    rsa_fingerprint=fingerprint,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                ledger.add_event(AuditEvent(user_id=user.id, action="register", result="success"))
                return secrets_pb2.RegisterResponse(user_id=user.id, username=user.username)
            finally:
                db.close()

        def StoreFragment(self, request, context):
            payload = _validate_jwt(request.jwt_token)
            if payload is None:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token inválido o expirado")

            db = SessionLocal()
            try:
                fragment = Fragment(
                    secret_id=request.secret_id,
                    user_id=payload["sub"],
                    fragment_index=request.fragment_index,
                    encrypted_fragment=bytes(request.encrypted_fragment),
                    checksum=request.checksum,
                )
                db.add(fragment)
                db.commit()
                db.refresh(fragment)

                block = ledger.add_event(AuditEvent(
                    user_id=payload["sub"],
                    action="store_fragment",
                    secret_id=request.secret_id,
                    result="success",
                    **_geo_to_kwargs(request.geo_context),
                ))
                return secrets_pb2.StoreFragmentResponse(
                    success=True, fragment_id=fragment.id, ledger_block_hash=block.hash,
                )
            finally:
                db.close()

        def GetFragment(self, request, context):
            payload = _validate_jwt(request.jwt_token)
            if payload is None:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token inválido o expirado")

            db = SessionLocal()
            try:
                fragment = (
                    db.query(Fragment)
                    .filter(Fragment.secret_id == request.secret_id, Fragment.user_id == payload["sub"])
                    .first()
                )
                if not fragment:
                    block = ledger.add_event(AuditEvent(
                        user_id=payload["sub"], action="get_fragment",
                        secret_id=request.secret_id, result="denied",
                        reason="fragmento no encontrado",
                        **_geo_to_kwargs(request.geo_context),
                    ))
                    return secrets_pb2.GetFragmentResponse(
                        success=False, ledger_block_hash=block.hash, deny_reason="no encontrado",
                    )

                block = ledger.add_event(AuditEvent(
                    user_id=payload["sub"], action="get_fragment",
                    secret_id=request.secret_id, result="success",
                    **_geo_to_kwargs(request.geo_context),
                ))
                return secrets_pb2.GetFragmentResponse(
                    success=True,
                    fragment_index=fragment.fragment_index,
                    encrypted_fragment=fragment.encrypted_fragment,
                    checksum=fragment.checksum,
                    ledger_block_hash=block.hash,
                )
            finally:
                db.close()

        def DeleteFragment(self, request, context):
            payload = _validate_jwt(request.jwt_token)
            if payload is None:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token inválido o expirado")

            db = SessionLocal()
            try:
                deleted = (
                    db.query(Fragment)
                    .filter(Fragment.secret_id == request.secret_id, Fragment.user_id == payload["sub"])
                    .delete()
                )
                db.commit()
                block = ledger.add_event(AuditEvent(
                    user_id=payload["sub"], action="delete_fragment",
                    secret_id=request.secret_id,
                    result="success" if deleted else "denied",
                    reason=None if deleted else "no encontrado",
                ))
                return secrets_pb2.DeleteFragmentResponse(
                    success=bool(deleted), ledger_block_hash=block.hash,
                )
            finally:
                db.close()

        def ListFragments(self, request, context):
            payload = _validate_jwt(request.jwt_token)
            if payload is None:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token inválido o expirado")

            db = SessionLocal()
            try:
                fragments = db.query(Fragment).filter(Fragment.user_id == payload["sub"]).all()
                return secrets_pb2.ListFragmentsResponse(
                    secret_ids=[f.secret_id for f in fragments],
                )
            finally:
                db.close()

        def Heartbeat(self, request, context):
            import time
            return secrets_pb2.HeartbeatResponse(status="ok", server_time_unix=int(time.time()))

else:

    class SecretsServerImpl:  # type: ignore[no-redef]
        """Stub temporal hasta que se compilen los .proto."""
        pass
