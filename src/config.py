"""Configuración global del servidor. Carga desde .env o variables de entorno."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # JWT
    jwt_secret_key: str = "EstaEsUnaClaveSuperSecretaServidor2026!"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 10

    # Database (SQL Server por defecto; sobreescribir via DATABASE_URL en .env / docker-compose)
    database_url: str = (
        "mssql+pyodbc://sa:SincroVault2026!@localhost:1433/secretsdb"
        "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )

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
