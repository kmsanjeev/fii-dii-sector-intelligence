from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.astrology_ontology import validate_ontology_directory

TARGET_ROOT = ROOT / "data" / "veda"


def main() -> None:
    report = validate_ontology_directory(TARGET_ROOT)
    print(json.dumps(report.to_dict(), indent=2))
    report.assert_valid()


if __name__ == "__main__":
    main()
