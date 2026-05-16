# SecretsServer — Backend Servidor

Servidor distribuido en **Python / FastAPI + gRPC** para el Sistema Distribuido de Gestión de Secretos.
Almacena el **Fragmento B (F2)** de cada secreto y mantiene un **ledger blockchain inmutable** de auditoría.

> Parte del proyecto **Sincro-Vault** — Universidad Manuela Beltrán, Sistemas Distribuidos UMB 2026-1.
> Cliente real: **Aldeamo S.A.S.** (Bogotá D.C.)

---

## Instalación (3 minutos)

### Requisito previo

[Python 3.11 o superior](https://www.python.org/downloads/) instalado.

### Setup automático

```powershell
.\setup.ps1
```

Eso hace **TODO** por ti:
1. Crea el entorno virtual `.venv/`
2. Instala las dependencias (`pip install -r requirements.txt`)
3. Genera los stubs gRPC desde `proto/secrets.proto`
4. Copia `.env.example` a `.env`

### Levantar el servidor

```powershell
.\.venv\Scripts\activate
python -m src.main
```

Listo. El servidor está corriendo en:
- **REST API:** http://localhost:9000/docs (Swagger UI interactivo)
- **gRPC:** `localhost:50051`
- **Health check:** http://localhost:9000/api/health

---

## Arquitectura

```
                ┌─────────────────────────────────────┐
   gRPC + TLS   │   SecretsServer                     │
  ◀────────────▶│   ┌──────────┐  ┌──────────┐        │
                │   │ FastAPI  │  │ gRPC     │        │
                │   │  :9000   │  │  :50051  │        │
                │   └──────────┘  └──────────┘        │
                │           │            │            │
                │           ▼            ▼            │
                │       ┌──────────────────┐          │
                │       │ SQLite + JWT     │          │
                │       │ Blockchain Ledger│          │
                │       └──────────────────┘          │
                └─────────────────────────────────────┘
```

---

## Endpoints REST principales

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/auth/register` | Crear cuenta (con cert RSA opcional) |
| `POST` | `/api/auth/login` | Login → JWT 10 min |
| `POST` | `/api/fragments` | Guardar fragmento (requiere JWT) |
| `GET` | `/api/fragments/{secret_id}` | Recuperar fragmento (requiere JWT) |
| `DELETE` | `/api/fragments/{secret_id}` | Eliminar fragmento |
| `POST` | `/api/internal/fragments` | **Para comunicación con backend cliente** (token compartido) |
| `GET` | `/api/audit` | Consultar blockchain audit ledger |
| `GET` | `/api/audit/validate` | Validar integridad de toda la cadena |
| `GET` | `/api/health` | Health check (público) |

---

## Características técnicas

- **JWT 10 min** con PyJWT (PBKDF2-SHA256 100k iteraciones para passwords)
- **Validación RSA 2048+** de certificados de cliente
- **TLS 1.3 opcional** para gRPC (`python scripts/generate_certs.py` para crear certs auto-firmados)
- **Blockchain audit ledger** con proof-of-work (dificultad configurable)
- **CORS abierto** para LAN
- **Escucha en `0.0.0.0`** — accesible desde otras PCs en la misma red

---

## Docker (opcional — para deploy en AWS / Cloud Run / cualquier servidor)

Si prefieres correrlo en un container en lugar de instalar Python local:

```bash
# Build + run con docker-compose (mas simple)
docker compose up -d --build

# Ver logs
docker compose logs -f server

# Detener
docker compose down

# Detener y borrar la BD persistente
docker compose down -v
```

El servidor queda escuchando en `localhost:9000` (REST) y `localhost:50051` (gRPC).
Los datos (BD SQLite + blockchain ledger) se persisten en un volumen Docker llamado `server-data`.

**Variables de entorno disponibles** (override con `-e` o en compose):
- `JWT_SECRET_KEY` — clave de firma JWT (cambiar en produccion)
- `JWT_EXPIRATION_MINUTES` (default `10`)
- `DATABASE_URL` (default `sqlite:////app/data/server.db`)
- `BLOCKCHAIN_DIFFICULTY` (default `2`)
- `TLS_ENABLED` (default `false`)

**Imagen mas chica:** el Dockerfile usa multi-stage build, la imagen final pesa ~150MB.

## Tests

```powershell
.\.venv\Scripts\activate
pytest tests/
```

---

## Estructura

```
servidor/
├── proto/secrets.proto          # Definición gRPC
├── src/
│   ├── main.py                  # Entry point (FastAPI + gRPC en threads)
│   ├── config.py                # Settings desde .env
│   ├── auth/                    # JWT, PBKDF2, RSA validator
│   ├── blockchain/              # Block, Chain, Ledger
│   ├── models/                  # User, Fragment (SQLAlchemy)
│   ├── rest_api/                # FastAPI routers
│   └── grpc_server/             # Implementación gRPC
├── scripts/
│   ├── generate_grpc.py         # Compila .proto a Python
│   └── generate_certs.py        # Genera certs TLS dev
├── tests/
├── requirements.txt
├── .env.example
└── setup.ps1                    # Setup con un solo comando
```

---

## Deploy en otra PC

Para conectar este servidor a un cliente .NET que está en otra máquina:
1. Asegúrate de que esta PC tiene IP estática o conocida (`ipconfig` en Windows)
2. Abre el firewall puertos 9000 y 50051:
   ```powershell
   New-NetFirewallRule -DisplayName "SecretsServer REST" -Direction Inbound -Protocol TCP -LocalPort 9000 -Action Allow
   New-NetFirewallRule -DisplayName "SecretsServer gRPC" -Direction Inbound -Protocol TCP -LocalPort 50051 -Action Allow
   ```
3. Desde la PC del cliente, prueba: `curl http://<IP_DE_ESTA_PC>:9000/api/health`

Ver la guía completa de deploy multi-PC en el README del backend cliente.

---

## Equipo

| Nombre | Rol |
|---|---|
| Harold Camargo | Líder |
| Samuel Ortiz | API e Integración (este repo del lado del cliente) |
| Michael Ramírez | Seguridad y Criptografía |
| Juan Stiven Castro | Desarrollo |
| Jose | Datos y Persistencia |
