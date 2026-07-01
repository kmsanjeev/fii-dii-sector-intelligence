# Capital Flow Intelligence Platform — Dev Server Launcher
# Usage: .\start.ps1
# Starts backend (port 8001) and frontend (port 5173) as detached processes.

$ROOT = $PSScriptRoot

function Is-PortListening($port) {
    $conns = netstat -ano 2>$null | Select-String ":$port\s"
    return $conns.Count -gt 0
}

Write-Host "Starting Capital Flow Intelligence Platform..." -ForegroundColor Cyan

# --- Backend ---
if (Is-PortListening 8001) {
    Write-Host "  [backend]  already running on :8001" -ForegroundColor Yellow
} else {
    Start-Process `
        -FilePath "py" `
        -ArgumentList "-3.11 -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload" `
        -WorkingDirectory $ROOT `
        -WindowStyle Hidden
    Start-Sleep -Seconds 6
    if (Is-PortListening 8001) {
        Write-Host "  [backend]  started  ->  http://localhost:8001" -ForegroundColor Green
    } else {
        Write-Host "  [backend]  FAILED to start" -ForegroundColor Red
    }
}

# --- Frontend ---
if (Is-PortListening 5173) {
    Write-Host "  [frontend] already running on :5173" -ForegroundColor Yellow
} else {
    Start-Process `
        -FilePath "cmd.exe" `
        -ArgumentList "/c npm run dev" `
        -WorkingDirectory "$ROOT\frontend" `
        -WindowStyle Hidden
    Start-Sleep -Seconds 10
    if (Is-PortListening 5173) {
        Write-Host "  [frontend] started  ->  http://localhost:5173" -ForegroundColor Green
    } else {
        Write-Host "  [frontend] FAILED to start" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Platform ready. Open http://localhost:5173 in your browser." -ForegroundColor Cyan
Write-Host "Run .\stop.ps1 to shut down both servers."
