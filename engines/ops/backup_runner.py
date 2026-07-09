"""
Backup Runner -- Phase R1-D1 (Data Control integration)
Python wrapper around backup.ps1 so the Data Control page's SSE engine
runner (which spawns Python scripts) can trigger and live-stream a backup.

Streams every backup.ps1 log line to stdout unbuffered and exits with the
script's exit code (0 = mirrored + verified, 1 = failure/mismatch).

Run:  py -3.11 engines/ops/backup_runner.py [target_path]
"""

import subprocess
import sys
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[2]
BACKUP_PS1 = ROOT / "backup.ps1"


def main() -> int:
    if not BACKUP_PS1.exists():
        print("ERROR: backup.ps1 not found at repo root")
        return 1

    cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(BACKUP_PS1),
    ]
    if len(sys.argv) > 1:
        cmd += ["-Target", sys.argv[1]]

    print("Backup starting (backup.ps1) -- mirrors raw data dirs, then verifies...")
    sys.stdout.flush()

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line.rstrip())
        sys.stdout.flush()
    proc.wait()

    if proc.returncode == 0:
        print("Backup finished: COMPLETE AND VERIFIED")
    else:
        print(f"ERROR: backup exited with code {proc.returncode} -- check logs/backup.log")
    return proc.returncode or 0


if __name__ == "__main__":
    sys.exit(main())
