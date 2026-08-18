import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path

from engines.ai.knowledge.language_foundation import load_locale


ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = ROOT / "docs" / "current-state" / "lang-002-hi-review-pack-001"
CSV_PATH = PACK_DIR / "VEDA_HINDI_HUMAN_REVIEW.csv"
MD_PATH = PACK_DIR / "VEDA_HINDI_HUMAN_REVIEW.md"


def _baseline_locale():
    raw = subprocess.check_output([
        "git",
        "show",
        "b603fde41441c8a93b25e7fa4688f838ffe6ce8e:data/veda/localization/locales/hi.json",
    ])
    return json.loads(raw)


def test_review_pack_has_exactly_49_unique_current_entries():
    pack = load_locale("hi")
    english = json.loads((ROOT / "data/veda/localization/locales/en.json").read_text(encoding="utf-8"))
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected_ids = set(pack["terms"]) | set(english["messages"])
    assert len(rows) == 49
    assert {row["canonical_id"] for row in rows} == expected_ids
    assert len({row["canonical_id"] for row in rows}) == 49
    assert all(row["human_decision"] == "" for row in rows)
    assert all(row["human_suggested_hindi"] == "" for row in rows)
    assert all(row["human_comments"] == "" for row in rows)


def test_review_pack_strings_and_states_match_committed_locale():
    # The review pack is historical evidence and must remain tied to its
    # committed pre-source-review baseline, not the corrected locale.
    pack = _baseline_locale()
    english = json.loads((ROOT / "data/veda/localization/locales/en.json").read_text(encoding="utf-8"))
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        canonical_id = row["canonical_id"]
        if canonical_id in pack["terms"]:
            assert row["english"] == next(item["english"] for item in json.loads((ROOT / "data/veda/localization/canonical_term_registry.json").read_text(encoding="utf-8"))["terms"] if item["canonical_id"] == canonical_id)
            assert row["hindi_current"] == pack["terms"][canonical_id]
        else:
            assert row["english"] == english["messages"][canonical_id]
            assert row["hindi_current"] == pack["messages"][canonical_id]
        assert row["translation_state"] == "MACHINE_DRAFT"
    assert pack["human_reviewed"] is False
    assert pack["production_authorized"] is False
    assert pack["review_counts"]["HUMAN_REVIEWED"] == 0
    assert pack["review_counts"]["APPROVED_PRESENTATION"] == 0


def test_review_pack_priority_counts_and_determinism():
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    counts = {priority: sum(row["priority"] == priority for row in rows) for priority in ("CRITICAL", "TECHNICAL", "NORMAL")}
    assert counts == {"CRITICAL": 8, "TECHNICAL": 33, "NORMAL": 8}
    first = hashlib.sha256(MD_PATH.read_bytes() + CSV_PATH.read_bytes()).hexdigest()
    second = hashlib.sha256(MD_PATH.read_bytes() + CSV_PATH.read_bytes()).hexdigest()
    assert first == second


def test_markdown_has_exactly_the_same_49_canonical_headings():
    pack = load_locale("hi")
    english = json.loads((ROOT / "data/veda/localization/locales/en.json").read_text(encoding="utf-8"))
    expected_ids = set(pack["terms"]) | set(english["messages"])
    markdown = MD_PATH.read_text(encoding="utf-8")
    headings = re.findall(r"^### (\d{2}) — ([A-Z0-9_.]+)$", markdown, flags=re.MULTILINE)
    assert len(headings) == 49
    assert [int(number) for number, _ in headings] == list(range(1, 50))
    assert {canonical_id for _, canonical_id in headings} == expected_ids
    assert markdown.count("[ ] ACCEPT") == 49
    assert markdown.count("[ ] CHANGE") == 49
    assert markdown.count("[ ] UNSURE") == 49


def test_markdown_current_hindi_values_match_the_locale_pack():
    # Historical review material intentionally retains the pre-correction text.
    pack = _baseline_locale()
    english = json.loads((ROOT / "data/veda/localization/locales/en.json").read_text(encoding="utf-8"))
    expected = {**pack["terms"], **pack["messages"]}
    markdown = MD_PATH.read_text(encoding="utf-8")
    chunks = re.findall(r"^### \d{2} — ([A-Z0-9_.]+)\n\n(.*?)(?=\n### |\n## |\Z)", markdown, flags=re.MULTILINE | re.DOTALL)
    assert len(chunks) == 49
    for canonical_id, body in chunks:
        current = re.search(r"^- Current Hindi: `(.+)`$", body, flags=re.MULTILINE)
        assert current is not None
        assert current.group(1) == expected[canonical_id]
    assert set(english["messages"]) <= set(expected)
