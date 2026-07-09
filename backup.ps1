# backup.ps1 -- Phase R1-D1: raw data backup to external drive
#
# Mirrors the irreplaceable data directories to the backup target using
# robocopy /MIR, then verifies file count + total bytes per directory.
#
# WHAT IS BACKED UP (acquired or user-created -- cannot be rebuilt):
#   data\NSE          raw NSE data incl. bhavcopy archive 1995+ (~20 GB)
#   data\historical   institutional positioning history (NSE only keeps recent)
#   data\reference    sector/theme/classification CSVs incl. manual overrides
#   data\portfolio    transactions.csv (append-only source of truth)
#   data\execution    orders.csv (trade audit trail)
#   data\research     user notes
#   data\auth         auth SQLite (sessions, API keys)
#
# WHAT IS NOT (rebuildable by engines, or secrets):
#   data\intelligence, data\cache, data\backtest, data\aggregated, logs, .env
#
# Usage:   .\backup.ps1                     (default target F:\Projects\fii-dii-backup)
#          .\backup.ps1 -Target "G:\bak"
# Schedule: registered as weekly Windows Scheduled Task (Sunday 08:00 IST,
#           outside market hours per G-A-04). See CHANGELOG v4.31.0.
#
# Exit codes: 0 = success + verified, 1 = robocopy failure or verify mismatch.

param(
    [string]$Target = "F:\Projects\fii-dii-backup"
)

$ErrorActionPreference = "Continue"
$SourceRoot = $PSScriptRoot
$DataRoot   = Join-Path $SourceRoot "data"
$LogDir     = Join-Path $SourceRoot "logs"
$LogFile    = Join-Path $LogDir "backup.log"

$Dirs = @("NSE", "historical", "reference", "portfolio", "execution", "research", "auth")

if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Force $LogDir | Out-Null }

function Write-Log([string]$msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    Add-Content -Path $LogFile -Value $line -Encoding utf8
    Write-Host $line
}

# ── Preconditions ─────────────────────────────────────────────────────────────

$targetDrive = Split-Path -Qualifier $Target
if (-not (Test-Path $targetDrive)) {
    Write-Log "FATAL: backup drive $targetDrive not available -- is the external drive plugged in?"
    exit 1
}
if (-not (Test-Path $Target)) { New-Item -ItemType Directory -Force $Target | Out-Null }

Write-Log "=== BACKUP START -> $Target ==="
$failed = $false

# ── Mirror each directory ─────────────────────────────────────────────────────

foreach ($d in $Dirs) {
    $src = Join-Path $DataRoot $d
    $dst = Join-Path (Join-Path $Target "data") $d
    if (-not (Test-Path $src)) {
        Write-Log "SKIP  data\$d (source missing)"
        continue
    }
    Write-Log "SYNC  data\$d ..."
    # /MIR mirror; /R:2 retries; /W:5 wait; quiet per-file output; append robocopy log
    robocopy $src $dst /MIR /R:2 /W:5 /NP /NFL /NDL /LOG+:$LogFile | Out-Null
    $rc = $LASTEXITCODE
    # Robocopy: 0-7 = success (bits: copies/extras/mismatches), >=8 = failure
    if ($rc -ge 8) {
        Write-Log "FAIL  data\$d -- robocopy exit code $rc"
        $failed = $true
    } else {
        Write-Log "OK    data\$d (robocopy code $rc)"
    }
}

# ── Verify: file count + total bytes per directory ────────────────────────────

Write-Log "--- VERIFY ---"
foreach ($d in $Dirs) {
    $src = Join-Path $DataRoot $d
    $dst = Join-Path (Join-Path $Target "data") $d
    if (-not (Test-Path $src)) { continue }

    $s = Get-ChildItem $src -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
    $t = Get-ChildItem $dst -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
    $sc = [int]$s.Count; $tc = [int]$t.Count
    $sb = [long]($s.Sum); $tb = [long]($t.Sum)

    if (($sc -eq $tc) -and ($sb -eq $tb)) {
        Write-Log ("VERIFIED  data\{0}: {1:N0} files, {2:N2} GB" -f $d, $sc, ($sb / 1GB))
    } else {
        Write-Log ("MISMATCH  data\{0}: source {1:N0} files/{2:N0} B  target {3:N0} files/{4:N0} B" -f $d, $sc, $sb, $tc, $tb)
        $failed = $true
    }
}

if ($failed) {
    Write-Log "=== BACKUP FINISHED WITH ERRORS ==="
    exit 1
}
Write-Log "=== BACKUP COMPLETE AND VERIFIED ==="
exit 0
