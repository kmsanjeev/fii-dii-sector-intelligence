"""Profile a bounded Open Gauquelin Database timed-data snapshot.

The adapter creates source-preserving birth-record candidates only. OGDB rows
do not become empirical cases until an objectively dated outcome/event and
leakage review are present in the shared CaseRegistry.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

SOURCE_URL = "https://opengauquelin.org/download/ogdb-time.csv.zip"
LICENSE_URL = "https://opengauquelin.org/about"


def profile_csv(csv_path: str | Path, output_path: str | Path, *, limit: int = 25) -> dict:
    rows = []
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for raw in reader:
            date_value = (raw.get("DATE") or "").strip()
            if not date_value or len(rows) >= limit:
                continue
            try:
                parsed = datetime.strptime(date_value, "%Y-%m-%d %H:%M")
            except ValueError:
                continue
            rows.append(
                {
                    "ogid": (raw.get("OGID") or "").strip(),
                    "wdid": (raw.get("WDID") or "").strip() or None,
                    "subject_label": " ".join(filter(None, [(raw.get("GNAME") or "").strip(), (raw.get("FNAME") or "").strip()])),
                    "occupation": (raw.get("OCCU") or "").strip(),
                    "birth_date": parsed.date().isoformat(),
                    "birth_time": parsed.strftime("%H:%M"),
                    "birth_time_precision": "MINUTE",
                    "birth_place": (raw.get("PLACE") or "").strip(),
                    "country_code": (raw.get("CY") or "").strip(),
                    "timezone_offset": (raw.get("TZO") or "").strip() or None,
                    "source_quality": "SOURCE_RECORD_UNREVIEWED",
                    "case_eligibility": "RESEARCH_ONLY_NO_EVENT",
                }
            )
    payload = {
        "feed_id": "VEDA-EMP-OGDB-001",
        "snapshot_source": SOURCE_URL,
        "license_reference": LICENSE_URL,
        "access_type": "OPEN_DOWNLOAD",
        "retrieved_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "delimiter": ";",
        "source_file": Path(csv_path).name,
        "pilot_limit": limit,
        "timed_records_profiled": len(rows),
        "usable_empirical_cases": 0,
        "reason_not_eligible": "OGDB birth records do not by themselves provide a dated outcome/event and leakage review.",
        "records": rows,
    }
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("output_path")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()
    payload = profile_csv(args.csv_path, args.output_path, limit=args.limit)
    print(json.dumps({key: payload[key] for key in ("feed_id", "timed_records_profiled", "usable_empirical_cases")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
