# Capital Flow Intelligence Platform — Dev Server Stopper
# Usage: .\stop.ps1

function Kill-Port($port, $label) {
    $pids = netstat -ano 2>$null |
        Select-String ":$port\s" |
        ForEach-Object { ($_ -split '\s+')[-1] } |
        Where-Object { $_ -match '^\d+$' } |
        Sort-Object -Unique
    foreach ($p in $pids) {
        try {
            Stop-Process -Id $p -Force -ErrorAction Stop
            Write-Host "  [$label] stopped (PID $p)" -ForegroundColor Green
        } catch {}
    }
}

Write-Host "Stopping Capital Flow Intelligence Platform..." -ForegroundColor Cyan
Kill-Port 8001 "backend"
Kill-Port 5173 "frontend"
Write-Host "Done."
