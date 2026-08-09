# Capital Flow Intelligence Platform — Dev Server Launcher
# Usage: .\start.ps1
# Starts backend (port 8001) and frontend (port 5173) as detached processes.

$ROOT = $PSScriptRoot

# Ensure logs directory exists
if (-not (Test-Path "$ROOT\logs")) {
    New-Item -ItemType Directory -Path "$ROOT\logs" -Force | Out-Null
}

function Is-PortListening($port) {
    $conns = netstat -ano 2>$null | Select-String ":$port\s+.*LISTENING"
    return $conns.Count -gt 0
}

function Resolve-BackendRuntime {
    $candidates = @(
        @{
            Name = "py -3.11"
            FilePath = "py"
            ProbeArgs = @("-3.11", "-c", "import uvicorn, fastapi, openai, ddgs")
            RunArgs = @("-3.11", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload")
            HasResearchRuntime = $true
        },
        @{
            Name = "py -3.11"
            FilePath = "py"
            ProbeArgs = @("-3.11", "-c", "import uvicorn, fastapi, openai")
            RunArgs = @("-3.11", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload")
            HasResearchRuntime = $false
        },
        @{
            Name = "py"
            FilePath = "py"
            ProbeArgs = @("-c", "import uvicorn, fastapi, openai, ddgs")
            RunArgs = @("-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload")
            HasResearchRuntime = $true
        },
        @{
            Name = "py"
            FilePath = "py"
            ProbeArgs = @("-c", "import uvicorn, fastapi, openai")
            RunArgs = @("-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload")
            HasResearchRuntime = $false
        }
    )

    foreach ($candidate in $candidates) {
        try {
            $probeCmd = "$($candidate.FilePath) $($candidate.ProbeArgs -join ' ')"
            Write-Host "  [debug] probing: $probeCmd" -ForegroundColor DarkGray
            $output = & $candidate.FilePath @($candidate.ProbeArgs) 2>&1
            $exitCode = $LASTEXITCODE
            Write-Host "  [debug]   exit code: $exitCode" -ForegroundColor DarkGray
            if ($exitCode -eq 0) {
                Write-Host "  [debug]   PROBE PASSED" -ForegroundColor DarkGray
                return $candidate
            } else {
                Write-Host "  [debug]   output: $($output | Out-String)" -ForegroundColor DarkGray
            }
        } catch {
            Write-Host "  [debug]   exception: $_" -ForegroundColor DarkGray
            continue
        }
    }
    return $null
}

Write-Host "Starting Capital Flow Intelligence Platform..." -ForegroundColor Cyan

# Quick check: what does `py` default to?
try {
    $pyVersion = & py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>&1
    Write-Host "  [info] py default version: $pyVersion" -ForegroundColor DarkGray
} catch {
    Write-Host "  [info] py command not available" -ForegroundColor DarkGray
}

# --- Backend ---
if (Is-PortListening 8001) {
    Write-Host "  [backend]  already running on :8001" -ForegroundColor Yellow
} else {
    $backendRuntime = Resolve-BackendRuntime
    if (-not $backendRuntime) {
        Write-Host "  [backend]  FAILED to find a Python runtime with uvicorn/fastapi/openai installed" -ForegroundColor Red
    } else {
        Write-Host "  [backend]  using $($backendRuntime.Name)" -ForegroundColor DarkGray
        if (-not $backendRuntime.HasResearchRuntime) {
            Write-Host "  [backend]  warning: selected runtime does not include ddgs, so Veda research mode will stay unavailable" -ForegroundColor Yellow
        }
        $logFile = Join-Path $ROOT "logs\backend_startup.log"
        Start-Process `
            -FilePath $backendRuntime.FilePath `
            -ArgumentList $backendRuntime.RunArgs `
            -WorkingDirectory $ROOT `
            -WindowStyle Hidden `
            -RedirectStandardOutput $logFile `
            -RedirectStandardError (Join-Path $ROOT "logs\backend_startup_err.log")
        for ($i = 0; $i -lt 15 -and -not (Is-PortListening 8001); $i++) {
            Start-Sleep -Seconds 1
        }
        if (Is-PortListening 8001) {
            Write-Host "  [backend]  started  ->  http://localhost:8001" -ForegroundColor Green
        } else {
            Write-Host "  [backend]  FAILED to start" -ForegroundColor Red
            $errLog = Join-Path $ROOT "logs\backend_startup_err.log"
            if (Test-Path $errLog) {
                $errContent = Get-Content $errLog -Raw
                if ($errContent) {
                    Write-Host "  [backend]  Error log ($errLog):" -ForegroundColor Red
                    Write-Host $errContent -ForegroundColor DarkRed
                }
            }
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
