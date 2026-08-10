from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.astrology_interpretation_validation import validate_exported_bundle


def main() -> None:
    report = validate_exported_bundle(ROOT)
    print(json.dumps(report, indent=2))
    if not report["is_valid"]:
        raise AssertionError(
            "P005 interpretation validation export is stale:\n"
            f"missing_files={report['missing_files']}\n"
            f"mismatched_files={report['mismatched_files']}"
        )


if __name__ == "__main__":
    main()
