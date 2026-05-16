"""Arranque del servidor gRPC en thread separado."""
import logging
from concurrent import futures
from pathlib import Path

import grpc

from src.config import settings

logger = logging.getLogger(__name__)


def serve_grpc():
    """Inicia el servidor gRPC bloqueando el thread actual."""
    try:
        from src.grpc_server.generated import secrets_pb2_grpc
        from src.grpc_server.secrets_service import SecretsServerImpl
    except ImportError:
        logger.warning(
            "Stubs gRPC no generados. Ejecuta: python scripts/generate_grpc.py "
            "(el servidor REST seguirá funcionando)."
        )
        return

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    secrets_pb2_grpc.add_SecretsServerServicer_to_server(SecretsServerImpl(), server)

    address = f"{settings.grpc_host}:{settings.grpc_port}"

    if settings.tls_enabled:
        cert_path = Path(settings.tls_cert_path)
        key_path = Path(settings.tls_key_path)
        if not cert_path.exists() or not key_path.exists():
            logger.error("TLS habilitado pero faltan certificados. Ejecuta: python scripts/generate_certs.py")
            return
        with key_path.open("rb") as f:
            private_key = f.read()
        with cert_path.open("rb") as f:
            certificate = f.read()
        credentials = grpc.ssl_server_credentials([(private_key, certificate)])
        server.add_secure_port(address, credentials)
        logger.info("gRPC server escuchando con TLS en %s", address)
    else:
        server.add_insecure_port(address)
        logger.info("gRPC server escuchando (sin TLS) en %s", address)

    server.start()
    server.wait_for_termination()
