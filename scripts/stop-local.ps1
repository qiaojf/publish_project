$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$runtimeRoot = Join-Path $projectRoot "local-data\run"

foreach ($service in @("frontend", "backend")) {
    $pidFile = Join-Path $runtimeRoot "$service.pid"
    if (-not (Test-Path $pidFile)) { continue }
    $servicePid = [int](Get-Content -LiteralPath $pidFile -Raw)
    $process = Get-Process -Id $servicePid -ErrorAction SilentlyContinue
    if ($process) {
        & taskkill.exe /PID $servicePid /T /F | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Could not stop $service (PID $servicePid). Run this script in the same user context that started the services."
            continue
        }
        Write-Host "Stopped $service (PID $servicePid)."
    }
    Remove-Item -LiteralPath $pidFile -ErrorAction SilentlyContinue
}

Write-Host "PostgreSQL was left running to protect other local sessions."
