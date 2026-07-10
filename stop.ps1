# Capital Flow Intelligence Platform — Dev Server Stopper
# Usage: .\stop.ps1
#
# Kills by COMMAND LINE, not just by port. uvicorn --reload runs as a
# reloader parent + worker child; killing only the port-holding worker
# leaves the parent alive to respawn a child, and on Windows multiple
# uvicorn instances can co-bind :8001 -- stale servers then keep serving
# old code (observed 2026-07-10: five simultaneous LISTEN entries).

Write-Host "Stopping Capital Flow Intelligence Platform..." -ForegroundColor Cyan

# --- Backend: every uvicorn process (reloader parents AND workers) ---
# NOTE: on Windows, uvicorn --reload launches its worker via
# multiprocessing.spawn -- that child's command line says "spawn_main",
# not "uvicorn", and it inherits the :8001 socket. Both patterns matter.
$uv = Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='py.exe'" |
    Where-Object { $_.CommandLine -match 'uvicorn|multiprocessing\.spawn' }
foreach ($p in $uv) {
    try {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop
        Write-Host "  [backend]  stopped uvicorn (PID $($p.ProcessId))" -ForegroundColor Green
    } catch {}
}

# --- Frontend: vite dev server (node) via port ---
$pids = netstat -ano 2>$null |
    Select-String ":5173\s.*LISTENING" |
    ForEach-Object { ($_ -split '\s+')[-1] } |
    Where-Object { $_ -match '^\d+$' } |
    Sort-Object -Unique
foreach ($p in $pids) {
    try {
        Stop-Process -Id $p -Force -ErrorAction Stop
        Write-Host "  [frontend] stopped (PID $p)" -ForegroundColor Green
    } catch {}
}

# --- Verify nothing is left holding :8001 ---
Start-Sleep -Seconds 2
$left = netstat -ano 2>$null | Select-String ":8001\s.*LISTENING"
if ($left) {
    Write-Host "  WARNING: something still listens on :8001 -- run stop.ps1 again" -ForegroundColor Yellow
    $left | ForEach-Object { Write-Host "    $_" -ForegroundColor Yellow }
} else {
    Write-Host "  port 8001 clear" -ForegroundColor Green
}
Write-Host "Done."
