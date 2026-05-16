"""Configuración global del servidor. Carga desde .env o variables de entorno."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # JWT
    jwt_secret_key: str = "EstaEsUnaClaveSuperSecretaServidor2026!"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 10

    # Database
    database_url: str = "sqlite:///./server.db"

    # Server
    rest_host: str = "0.0.0.0"
    rest_port: int = 9000
    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051

    # TLS
    tls_enabled: bool = False
    tls_cert_path: str = "./certs/server.crt"
    tls_key_path: str = "./certs/server.key"

    # Blockchain
    blockchain_difficulty: int = 2
    blockchain_ledger_path: str = "./data/ledger.json"


settings = Settings()
