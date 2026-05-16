# Abre el firewall de Windows para que otros equipos en la LAN
# puedan conectarse al servidor en los puertos 9000 (REST) y 50051 (gRPC).
#
# Ejecutar como Administrador:
#   PowerShell como Admin -> .\scripts\open-firewall.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host " SecretsServer - Abrir firewall para LAN" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar admin
$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(`
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: ejecutar como Administrador." -ForegroundColor Red
    Write-Host "  Clic derecho en PowerShell -> 'Ejecutar como administrador'" -ForegroundColor Yellow
    exit 1
}

$rules = @(
    @{Name = "SecretsServer REST 9000"; Port = 9000},
    @{Name = "SecretsServer gRPC 50051"; Port = 50051}
)

foreach ($rule in $rules) {
    # Borrar regla si ya existe (idempotente)
    Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue | Remove-NetFirewallRule

    New-NetFirewallRule `
        -DisplayName $rule.Name `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $rule.Port `
        -Action Allow `
        -Profile Domain,Private | Out-Null

    Write-Host "  [OK] Puerto $($rule.Port) abierto - $($rule.Name)" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host " Firewall configurado." -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""

# Mostrar la IP en LAN para que el cliente la use
Write-Host "IP de esta PC en la LAN (para configurar el cliente):" -ForegroundColor White
$ips = Get-NetIPAddress -AddressFamily IPv4 `
    | Where-Object { $_.PrefixOrigin -in 'Dhcp','Manual' -and $_.InterfaceAlias -notmatch 'Loopback|vEthernet|VMware|VirtualBox' } `
    | Select-Object -ExpandProperty IPAddress
foreach ($ip in $ips) {
    Write-Host "  -> $ip" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "En la PC del cliente, durante setup.ps1, indica una de estas IPs." -ForegroundColor White
Write-Host ""
