# Setup automatico del Backend Servidor (Python/FastAPI + gRPC)
# Uso: .\setup.ps1
# Requiere: Python 3.11+

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptRoot

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " SecretsServer - Setup automatico" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Python
Write-Host "[1/5] Verificando Python..." -ForegroundColor Yellow
try {
    $pyVersion = python --version 2>&1
    Write-Host "      $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python no esta instalado. Descarga Python 3.11+ de python.org" -ForegroundColor Red
    exit 1
}

# 2. Crear venv si no existe
Write-Host ""
Write-Host "[2/5] Creando entorno virtual..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "      venv creado" -ForegroundColor Green
} else {
    Write-Host "      venv ya existe (se reutiliza)" -ForegroundColor Green
}

# 3. Instalar dependencias
Write-Host ""
Write-Host "[3/5] Instalando dependencias (puede tardar 2-3 min)..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
Write-Host "      Dependencias instaladas" -ForegroundColor Green

# 4. Crear .env si no existe
Write-Host ""
Write-Host "[4/5] Configurando .env..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "      .env creado desde .env.example" -ForegroundColor Green
} else {
    Write-Host "      .env ya existe (se conserva)" -ForegroundColor Green
}

# 5. Generar stubs gRPC desde el .proto
Write-Host ""
Write-Host "[5/5] Generando stubs gRPC..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" "scripts\generate_grpc.py"
Write-Host "      Stubs generados" -ForegroundColor Green

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Setup completo." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para levantar el servidor:" -ForegroundColor White
Write-Host "    .\.venv\Scripts\activate" -ForegroundColor Cyan
Write-Host "    python -m src.main" -ForegroundColor Cyan
Write-Host ""
Write-Host "REST     : http://localhost:9000/docs" -ForegroundColor White
Write-Host "gRPC     : localhost:50051" -ForegroundColor White
Write-Host "Audit    : http://localhost:9000/api/audit (requiere JWT)" -ForegroundColor White
Write-Host ""
