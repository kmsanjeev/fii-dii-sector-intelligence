"""Conservatively enrich OGDB records with externally retrieved Wikidata claims.

This adapter deliberately does not perform name-only joins or create empirical
cases. Candidate claims must already be retrieved through an approved source
route and must agree on birth date, place, and occupation. Both the original
OGDB record and the Wikidata candidate references are retained for review.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _normalise(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _exact_candidate(record: dict[str, Any], candidate: dict[str, Any]) -> bool:
    return all(
        (
            _normalise(record.get("birth_date")) == _normalise(candidate.get("birth_date")),
            _normalise(record.get("birth_place")) == _normalise(candidate.get("birth_place")),
            _normalise(record.get("occupation")) == _normalise(candidate.get("occupation")),
        )
    ) and bool(str(candidate.get("wdid") or "").strip())


def enrich_records(
    ogdb_payload: dict[str, Any],
    candidates_by_ogid: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Return a source-preserving identity-enrichment snapshot.

    A matched identity remains ``RESEARCH_ONLY_NO_EVENT``. This function never
    constructs or submits a ``CaseRecord`` and therefore cannot increase the
    empirical-case count.
    """

    enriched: list[dict[str, Any]] = []
    matched = 0
    for record in ogdb_payload.get("records", []):
        candidates = candidates_by_ogid.get(str(record.get("ogid") or ""), [])
        exact = [candidate for candidate in candidates if _exact_candidate(record, candidate)]
        item = {
            "ogid": record.get("ogid"),
            "original_ogdb_record": record,
            "candidate_count": len(candidates),
            "identity_status": "UNMATCHED_AMBIGUOUS_OR_MISMATCHED",
            "case_eligibility": "RESEARCH_ONLY_NO_EVENT",
            "usable_empirical_case": False,
            "wikidata_candidates": candidates,
        }
        if len(exact) == 1:
            candidate = exact[0]
            matched += 1
            item["identity_status"] = "IDENTITY_MATCHED_RESEARCH_ONLY_NO_EVENT"
            item["wikidata_identity"] = {
                "wdid": candidate["wdid"],
                "claims": {
                    "birth_date": candidate.get("birth_date"),
                    "birth_place": candidate.get("birth_place"),
                    "occupation": candidate.get("occupation"),
                },
                "references": candidate.get("references", []),
            }
        enriched.append(item)

    return {
        "feed_id": "VEDA-EMP-WD-001",
        "source_route": "WIKIDATA_CLAIMS_EXACT_MATCH",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "input_feed_id": ogdb_payload.get("feed_id"),
        "records_considered": len(enriched),
        "identity_matches": matched,
        "usable_empirical_cases": 0,
        "reason_not_eligible": "Identity enrichment supplies no dated outcome/event or leakage review.",
        "records": enriched,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ogdb_snapshot", type=Path)
    parser.add_argument("candidate_claims", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.ogdb_snapshot.read_text(encoding="utf-8"))
    candidates = json.loads(args.candidate_claims.read_text(encoding="utf-8"))
    result = enrich_records(payload, candidates)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("records_considered", "identity_matches", "usable_empirical_cases")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
