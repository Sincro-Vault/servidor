# =====================================================
# Dockerfile multi-stage para el SecretsServer
# =====================================================
# Stage 1 (builder): instala dependencias y compila stubs gRPC
# Stage 2 (runtime): imagen final liviana

# ----------- Stage 1: builder ------------------------
FROM python:3.11-slim AS builder

# Dependencias del SO para compilar wheels (cryptography, pyodbc, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Instalar dependencias Python en directorio local (cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir --user --upgrade pip \
 && pip install --no-cache-dir --user -r requirements.txt

# Generar stubs gRPC desde el .proto
COPY proto/ ./proto/
COPY scripts/generate_grpc.py ./scripts/
ENV PATH=/root/.local/bin:$PATH
RUN mkdir -p src/grpc_server/generated \
 && touch src/grpc_server/generated/__init__.py \
 && python -m grpc_tools.protoc \
    -Iproto \
    --python_out=src/grpc_server/generated \
    --grpc_python_out=src/grpc_server/generated \
    proto/secrets.proto \
 && sed -i 's/^import secrets_pb2/from . import secrets_pb2/' src/grpc_server/generated/secrets_pb2_grpc.py

# ----------- Stage 2: runtime ------------------------
FROM python:3.11-slim

# Instalar ODBC Driver 18 para SQL Server + runtime de unixodbc
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg ca-certificates apt-transport-https unixodbc libgssapi-krb5-2 \
 && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
 && echo "deb [arch=amd64,arm64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
        > /etc/apt/sources.list.d/mssql-release.list \
 && apt-get update \
 && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
 && apt-get purge -y curl gnupg apt-transport-https \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root para mejor seguridad
RUN useradd --create-home --shell /bin/bash secretsserver

WORKDIR /app

# Copiar dependencias instaladas desde el builder
COPY --from=builder /root/.local /home/secretsserver/.local
ENV PATH=/home/secretsserver/.local/bin:$PATH \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

# Copiar stubs gRPC ya generados
COPY --from=builder /build/src/grpc_server/generated ./src/grpc_server/generated

# Copiar codigo fuente
COPY proto/ ./proto/
COPY scripts/ ./scripts/
COPY src/ ./src/

# Crear directorio data/ persistente para ledger y BD
RUN mkdir -p /app/data /app/certs \
 && chown -R secretsserver:secretsserver /app

USER secretsserver

EXPOSE 9000 50051

# Defaults configurables via -e
ENV REST_HOST=0.0.0.0 \
    REST_PORT=9000 \
    GRPC_HOST=0.0.0.0 \
    GRPC_PORT=50051 \
    DATABASE_URL="mssql+pyodbc://sa:SincroVault2026!@sqlserver:1433/secretsdb?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes" \
    BLOCKCHAIN_LEDGER_PATH=/app/data/ledger.json

CMD ["python", "-m", "src.main"]
