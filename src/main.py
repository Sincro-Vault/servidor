"""Punto de entrada del servidor.

Levanta:
- FastAPI en uvicorn (REST) en `REST_PORT` (default 9000)
- gRPC server en thread separado en `GRPC_PORT` (default 50051)
"""
import logging
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.database import init_db
from src.grpc_server.server import serve_grpc
from src.rest_api import routes_audit, routes_auth, routes_fragments, routes_health, routes_internal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="SecretsServer — Backend Servidor",
        description="Servidor distribuido de fragmentos de secretos con blockchain audit ledger",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(routes_health.router)
    app.include_router(routes_auth.router)
    app.include_router(routes_fragments.router)
    app.include_router(routes_audit.router)
    app.include_router(routes_internal.router)

    @app.on_event("startup")
    def _startup():
        logger.info("Inicializando base de datos...")
        init_db()
        logger.info("Lanzando servidor gRPC en thread separado...")
        thread = threading.Thread(target=serve_grpc, daemon=True)
        thread.start()
        logger.info("Servidor REST listo en http://%s:%d", settings.rest_host, settings.rest_port)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.rest_host,
        port=settings.rest_port,
        reload=False,
        log_level="info",
    )
