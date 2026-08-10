from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.astrology_ontology import write_default_documents

TARGET_DIR = ROOT / "data" / "veda"


def main() -> None:
    written = write_default_documents(TARGET_DIR)
    for path in written:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
