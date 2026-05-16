# =====================================================
# Dockerfile multi-stage para el SecretsServer
# =====================================================
# Stage 1 (builder): instala dependencias y compila stubs gRPC
# Stage 2 (runtime): imagen final liviana

# ----------- Stage 1: builder ------------------------
FROM python:3.11-slim AS builder

# Dependencias del SO para compilar wheels (cryptography, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Instalar dependencias Python en directorio local (cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir --user --upgrade pip \
 && pip install --no-cache-dir --user -r requirements.txt

# Generar stubs gRPC desde el .proto
COPY proto/ ./proto/
COPY scripts/generate_grpc.py ./scripts/
RUN mkdir -p src/grpc_server/generated \
 && touch src/grpc_server/generated/__init__.py \
 && /root/.local/bin/python -m grpc_tools.protoc \
    -Iproto \
    --python_out=src/grpc_server/generated \
    --grpc_python_out=src/grpc_server/generated \
    proto/secrets.proto \
 && sed -i 's/^import secrets_pb2/from . import secrets_pb2/' src/grpc_server/generated/secrets_pb2_grpc.py

# ----------- Stage 2: runtime ------------------------
FROM python:3.11-slim

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
    DATABASE_URL=sqlite:////app/data/server.db \
    BLOCKCHAIN_LEDGER_PATH=/app/data/ledger.json

CMD ["python", "-m", "src.main"]
