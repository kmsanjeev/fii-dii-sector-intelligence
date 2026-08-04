# Capital Flow Intelligence Platform — Dev Server Launcher
# Usage: .\start.ps1
# Starts backend (port 8001) and frontend (port 5173) as detached processes.

$ROOT = $PSScriptRoot

function Is-PortListening($port) {
    $conns = netstat -ano 2>$null | Select-String ":$port\s"
    return $conns.Count -gt 0
}

function Resolve-BackendRuntime {
    $candidates = @(
        @{
            Name = "py -3.11"
            FilePath = "py"
            ProbeArgs = @("-3.11", "-c", "import uvicorn, fastapi, openai")
            RunArgs = @("-3.11", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload")
        },
        @{
            Name = "python"
            FilePath = "python"
            ProbeArgs = @("-c", "import uvicorn, fastapi, openai")
            RunArgs = @("-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload")
        },
        @{
            Name = "py"
            FilePath = "py"
            ProbeArgs = @("-c", "import uvicorn, fastapi, openai")
            RunArgs = @("-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload")
        }
    )

    foreach ($candidate in $candidates) {
        try {
            & $candidate.FilePath @($candidate.ProbeArgs) *> $null
            if ($LASTEXITCODE -eq 0) {
                return $candidate
            }
        } catch {
            continue
        }
    }
    return $null
}

Write-Host "Starting Capital Flow Intelligence Platform..." -ForegroundColor Cyan

# --- Backend ---
if (Is-PortListening 8001) {
    Write-Host "  [backend]  already running on :8001" -ForegroundColor Yellow
} else {
    $backendRuntime = Resolve-BackendRuntime
    if (-not $backendRuntime) {
        Write-Host "  [backend]  FAILED to find a Python runtime with uvicorn/fastapi/openai installed" -ForegroundColor Red
    } else {
        Write-Host "  [backend]  using $($backendRuntime.Name)" -ForegroundColor DarkGray
        Start-Process `
            -FilePath $backendRuntime.FilePath `
            -ArgumentList $backendRuntime.RunArgs `
            -WorkingDirectory $ROOT `
            -WindowStyle Hidden
        for ($i = 0; $i -lt 15 -and -not (Is-PortListening 8001); $i++) {
            Start-Sleep -Seconds 1
        }
        if (Is-PortListening 8001) {
            Write-Host "  [backend]  started  ->  http://localhost:8001" -ForegroundColor Green
        } else {
            Write-Host "  [backend]  FAILED to start" -ForegroundColor Red
        }
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
