from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.astrology_governance import validate_registry_directory

REGISTRY_ROOT = ROOT / "data" / "veda" / "research" / "astrology"


def main() -> None:
    report = validate_registry_directory(REGISTRY_ROOT)
    print(json.dumps(report.to_dict(), indent=2))
    report.assert_valid()


if __name__ == "__main__":
    main()
