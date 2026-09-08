param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$backendRoot = Join-Path $projectRoot "backend"
$runtimeRoot = Join-Path $projectRoot "local-data\run"
$logRoot = Join-Path $projectRoot "local-data\logs"
$portablePgRoot = Join-Path $projectRoot "local-data\postgres\pgsql"
$portablePgData = Join-Path $projectRoot "local-data\postgres-data"

New-Item -ItemType Directory -Force -Path $runtimeRoot, $logRoot | Out-Null

if (-not (Test-Path (Join-Path $backendRoot ".env"))) {
    Copy-Item -LiteralPath (Join-Path $backendRoot ".env.example") -Destination (Join-Path $backendRoot ".env")
    throw "backend/.env has been created. Set PostgreSQL credentials, create content_publish and content_publish_test, then run this script again."
}
if (-not (Test-Path (Join-Path $projectRoot ".env.local"))) {
    Copy-Item -LiteralPath (Join-Path $projectRoot ".env.example") -Destination (Join-Path $projectRoot ".env.local")
}

$frontendEnv = Get-Content -LiteralPath (Join-Path $projectRoot ".env.local") -Raw
if ($frontendEnv -match "(?m)^\s*VITE_USE_MOCK\s*=\s*true\s*$") {
    throw "Local integration requires VITE_USE_MOCK=false in .env.local."
}

$pgCtl = Join-Path $portablePgRoot "bin\pg_ctl.exe"
$pgIsReady = Join-Path $portablePgRoot "bin\pg_isready.exe"
if ((Test-Path $pgCtl) -and (Test-Path $portablePgData)) {
    if (-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 5432 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
        & $pgCtl -D $portablePgData -l (Join-Path $logRoot "postgres.log") start | Out-Host
    }
} elseif (-not (Get-Command pg_isready -ErrorAction SilentlyContinue)) {
    throw "PostgreSQL is not available. Install PostgreSQL 16+ or place portable binaries under local-data/postgres/pgsql."
} else {
    $pgIsReady = (Get-Command pg_isready).Source
}

& $pgIsReady -h 127.0.0.1 -p 5432 -t 5 | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "PostgreSQL is not accepting connections on 127.0.0.1:5432."
}

$venvPython = Join-Path $backendRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    if ($SkipInstall) { throw "backend/.venv is missing." }
    $pythonCommand = Get-Command python -ErrorAction Stop
    & $pythonCommand.Source -m venv (Join-Path $backendRoot ".venv")
    & $venvPython -m pip install -r (Join-Path $backendRoot "requirements.txt")
}
if (-not (Test-Path (Join-Path $projectRoot "node_modules"))) {
    if ($SkipInstall) { throw "node_modules is missing." }
    Push-Location $projectRoot
    try { & npm.cmd install } finally { Pop-Location }
}

Push-Location $backendRoot
try {
    & $venvPython -m alembic upgrade head
    & $venvPython scripts\seed.py
} finally {
    Pop-Location
}

if (-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 8000 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
    $backendProcess = Start-Process -FilePath $venvPython `
        -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
        -WorkingDirectory $backendRoot -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logRoot "backend.out.log") `
        -RedirectStandardError (Join-Path $logRoot "backend.err.log")
    Set-Content -LiteralPath (Join-Path $runtimeRoot "backend.pid") -Value $backendProcess.Id
}

if (-not (Test-NetConnection -ComputerName 127.0.0.1 -Port 5173 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
    $frontendProcess = Start-Process -FilePath (Get-Command npm.cmd).Source `
        -ArgumentList "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173" `
        -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $logRoot "frontend.out.log") `
        -RedirectStandardError (Join-Path $logRoot "frontend.err.log")
    Set-Content -LiteralPath (Join-Path $runtimeRoot "frontend.pid") -Value $frontendProcess.Id
}

$healthy = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 2
        if ($health.success -and $health.data.status -eq "ok") { $healthy = $true; break }
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $healthy) { throw "FastAPI did not become healthy. Check local-data/logs/backend.err.log." }

$frontendHealthy = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $frontendResponse = Invoke-WebRequest -Uri "http://127.0.0.1:5173" -TimeoutSec 2 -UseBasicParsing
        if ($frontendResponse.StatusCode -eq 200) { $frontendHealthy = $true; break }
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $frontendHealthy) { throw "Vue did not become healthy. Check local-data/logs/frontend.err.log." }

Write-Host "Local deployment is ready." -ForegroundColor Green
Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Swagger:  http://127.0.0.1:8000/docs"
Write-Host "Health:   http://127.0.0.1:8000/api/health"
$lanAddresses = [System.Net.Dns]::GetHostAddresses([System.Net.Dns]::GetHostName()) |
    Where-Object { $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork -and -not [System.Net.IPAddress]::IsLoopback($_) } |
    Select-Object -ExpandProperty IPAddressToString -Unique
foreach ($lanAddress in $lanAddresses) {
    Write-Host "LAN:      http://${lanAddress}:5173"
}
if ($lanAddresses) {
    Write-Host "If another computer cannot connect, allow inbound TCP 5173 in Windows Defender Firewall." -ForegroundColor Yellow
}
Write-Host "Stop app servers with: powershell -ExecutionPolicy Bypass -File scripts\stop-local.ps1"
