"""Emit the canonical governed Theme summary for deterministic validation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.services.governed_theme_intelligence import build_runtime_cache, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-cache",
        action="store_true",
        help="Build validated membership and bounded price projection artifacts.",
    )
    args = parser.parse_args()
    if args.write_cache:
        print(json.dumps(build_runtime_cache(), ensure_ascii=False, sort_keys=True))
    else:
        print(
            json.dumps(
                summary(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
        )


if __name__ == "__main__":
    main()
