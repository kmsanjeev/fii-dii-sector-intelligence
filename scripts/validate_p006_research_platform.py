from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.research.platform.validation import validate_snapshot_directory


SNAPSHOT_ROOT = ROOT / "data" / "research" / "synthetic_pilot"


def main() -> None:
    report = validate_snapshot_directory(SNAPSHOT_ROOT)
    print(json.dumps(report.to_dict(), indent=2))
    report.assert_valid()


if __name__ == "__main__":
    main()
