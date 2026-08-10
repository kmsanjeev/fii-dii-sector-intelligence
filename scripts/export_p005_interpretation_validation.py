from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engines.ai.knowledge.astrology_interpretation_validation import export_phase_bundle, render_phase_docs


def main() -> None:
    data_files = export_phase_bundle(ROOT)
    doc_files = render_phase_docs(ROOT)
    print(
        json.dumps(
            {
                "data_files": [str(path.relative_to(ROOT)) for path in data_files],
                "doc_files": [str(path.relative_to(ROOT)) for path in doc_files],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
