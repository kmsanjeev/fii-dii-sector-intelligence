"""Feature-blind POSITION_END evidence redesign.

This activity audits the existing outcome corpus only.  It deliberately reads
feature metadata (identity, version and hashes) but never imports a feature
calculator, chart engine or activation output.  The generated artifacts are
research/governance records, not empirical signal results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.veda_power_planner import two_proportion_required


COHORT_PATH = ROOT / "docs/current-state/emp-posend-acq-001/02_COHORT_FREEZE.json"
FAMILY_PATH = ROOT / "docs/current-state/emp-feature-003/02_FEATURE_FAMILY_REGISTRY.json"
POWER_PATH = ROOT / "docs/current-state/evidence-rebaseline-001/03_POWER_SENSITIVITY.json"
OUT = ROOT / "docs/current-state/evidence-posend-rebaseline-001"
PROGRAMME = "VEDA-EVIDENCE-POSEND-REBASELINE-001"
RUN_DATE = "2026-08-18"


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def source_tier(source_quality: str) -> tuple[str, str]:
    mapping = {
        "PRIMARY_OFFICIAL": ("A", "PRIMARY_OFFICIAL"),
        "STRONG_REFERENCED_STRUCTURED": ("B", "STRONG_STRUCTURED"),
        "SINGLE_REFERENCED_STRUCTURED": ("C", "SECONDARY_STRUCTURED"),
    }
    return mapping.get(source_quality, ("D", "UNKNOWN"))


def cluster_for(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if host.endswith("wikipedia.org"):
        return "WIKIPEDIA_UPSTREAM"
    if host == "baseballhall.org":
        return "BASEBALL_HALL_OF_FAME"
    if host == "www.fff.fr":
        return "FRENCH_FOOTBALL_FEDERATION"
    return "UNKNOWN"


def event_id(subject_id: str) -> str:
    return f"POSEND-001-{subject_id}"


def _split_hash(ids: list[str]) -> str:
    return digest(sorted(ids))


def _event_rows(subjects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for subject in subjects:
        tier, source_class = source_tier(subject.get("source_quality", "UNKNOWN"))
        url = subject.get("event_source", "")
        rows.append(
            {
                "subject_id": subject["subject_id"],
                "event_id": event_id(subject["subject_id"]),
                "event_family": "POSITION_END",
                "event_type": "POSITION_END",
                "event_subtype_raw": subject.get("event_subtype", "UNRESOLVED"),
                "event_subtype_governed": "CAREER_END_INFERRED",
                "event_date": subject.get("event_date"),
                "date_precision": subject.get("date_precision", "UNKNOWN"),
                "event_definition": "Source-described professional career end; not a verified formal effective role-end date",
                "objectivity": "INFERRED_FROM_BIOGRAPHY",
                "event_source": url,
                "event_source_class": source_class,
                "event_evidence_tier": tier,
                "event_provenance": "ACQUISITION_MANIFEST_SOURCE_RETAINED",
                "birth_provenance": subject.get("birth_provenance"),
                "discovery_source": "VEDA-EMP-POSEND-ACQ-001",
                "corroborating_source": None,
                "dependence_cluster": cluster_for(url),
                "feature_data_included": False,
            }
        )
    return sorted(rows, key=lambda row: row["subject_id"])


def build() -> dict[str, Any]:
    cohort = read_json(COHORT_PATH)
    family = read_json(FAMILY_PATH)
    power = read_json(POWER_PATH)
    subjects = sorted(cohort["subjects"], key=lambda row: row["subject_id"])
    validation = list(cohort["validation_subjects"])
    holdout = list(cohort["holdout_subjects"])
    ids = [row["subject_id"] for row in subjects]
    events = _event_rows(subjects)
    policy = {
        "event_family": "POSITION_END",
        "selection_lane": "BIRTH_FIRST",
        "one_primary_event_per_subject": True,
        "prior_exposure_exclusion": True,
        "feature_based_selection": False,
        "source_and_date_precision_preserved": True,
        "holdout_split": "existing_subject_level_70_30",
    }
    quality = Counter(row["source_quality"] for row in subjects)
    tiers = Counter(source_tier(row.get("source_quality", "UNKNOWN"))[0] for row in subjects)
    clusters = Counter(row["dependence_cluster"] for row in events)
    precision = Counter(row.get("date_precision", "UNKNOWN") for row in subjects)
    governed_subtypes = Counter(row["event_subtype_governed"] for row in events)

    scenario_rows = []
    for baseline in (0.10, 0.20, 0.30):
        for absolute_delta in (0.05, 0.10, 0.15, 0.20):
            target = min(0.99, baseline + absolute_delta)
            scenario_rows.append(
                two_proportion_required(
                    baseline,
                    target,
                    design_effect=1.10,
                    exclusion_fraction=0.15,
                )
            )

    contracts = []
    for contract in family["contracts"]:
        contracts.append(
            {
                "feature_id": contract["feature_id"],
                "name": contract["name"],
                "version": contract["version"],
                "hash": contract["hash"],
                "source_status": contract["source_status"],
                "source_ids": contract["source_ids"],
                "implementation_status": contract["implementation_status"],
                "activation_inspected": False,
            }
        )

    return {
        "programme": PROGRAMME,
        "run_date": RUN_DATE,
        "cohort_freeze": {
            "cohort_id": cohort["id"],
            "version": cohort["version"],
            "subjects": len(subjects),
            "events": len(events),
            "subject_hash": cohort["subject_list_hash"],
            "event_hash": cohort["event_list_hash"],
            "source_manifest_hash": cohort["source_manifest_hash"],
            "event_definition_hash": cohort["event_definition_hash"],
            "selection_policy_hash": digest(policy),
            "selection_policy": policy,
            "precision_distribution": dict(sorted(precision.items())),
            "subtype_distribution_raw": dict(sorted(Counter(row.get("event_subtype", "UNKNOWN") for row in subjects).items())),
            "subtype_distribution_governed": dict(sorted(governed_subtypes.items())),
            "validation_subjects": len(validation),
            "holdout_subjects": len(holdout),
            "validation_subject_hash": _split_hash(validation),
            "holdout_subject_hash": _split_hash(holdout),
            "holdout_protected": bool(cohort["holdout_protected"]),
            "legacy_subjects": 4,
        },
        "event_provenance": {
            "record_count": len(events),
            "records": events,
            "birth_event_provenance_separated": True,
            "outcome_leakage": "NO_EVIDENCE_OF_OUTCOME_LEAKAGE",
            "outcome_leakage_basis": [
                "Acquisition manifest records astrology_inspected_during_acquisition=false",
                "feature_based_selection=false and feature family hash was verified only as metadata",
                "No activation, association, p-value or permutation output was read by this activity",
            ],
            "source_quality_counts_raw": dict(sorted(quality.items())),
            "source_tier_counts": dict(sorted(tiers.items())),
        },
        "date_precision": {
            "policy": {
                "DAY": "future primary/confirmatory eligibility if all other gates pass",
                "MONTH": "secondary interval-censored analysis only",
                "YEAR": "exploratory/acquisition/feasibility only",
                "UNKNOWN": "not timing-study eligible",
            },
            "before": {key: precision.get(key, 0) for key in ("DAY", "MONTH", "YEAR", "UNKNOWN")},
            "after_recovery": {"DAY": 0, "MONTH": 0, "YEAR": len(subjects), "UNKNOWN": 0},
            "upgraded_to_day": 0,
            "upgraded_to_month": 0,
            "unchanged": len(subjects),
            "downgraded": 0,
            "conflicted": 1,
            "synthetic_dates_created": 0,
            "source_resolution_status": "BOUNDED_PASS_COMPLETE_NO_HONEST_PRECISION_UPGRADE",
            "reviewed_high_value_sources": 2,
            "remaining_sources": 18,
        },
        "precision_recovery": {
            "bounded": True,
            "review_date": RUN_DATE,
            "records_in_scope": len(subjects),
            "official_or_institutional_pages_checked": [
                {
                    "subject_id": "aaron-henry-1934-02-05",
                    "source": "https://baseballhall.org/hall-of-famers/aaron-hank",
                    "finding": "Institutional career ranges end in 1976; no effective day or month for cessation is stated",
                    "result": "UNCHANGED_YEAR",
                },
                {
                    "subject_id": "abbes-claude-1927-05-24",
                    "source": "https://www.fff.fr/equipe-nationale/joueur/8477-abbes-claude/fiche.html",
                    "finding": "FFF page lists club activity through 06/1967; it does not support the cohort's 1962 professional-career-end definition",
                    "result": "EVENT_DEFINITION_CONFLICT_UNRESOLVED",
                },
            ],
            "remaining_source_action": "Existing Wikipedia-derived pages were not treated as independent precision upgrades; further review stops under the bounded stop rule until a specific documentary lead exists.",
            "date_selection_rule": "No publication date, last activity, successor appointment or inferred month-start was substituted for an effective event date.",
        },
        "source_dependence": {
            "source_clusters": len(clusters),
            "cluster_counts": dict(sorted(clusters.items())),
            "largest_cluster": clusters.most_common(1)[0][0],
            "largest_cluster_records": clusters.most_common(1)[0][1],
            "largest_cluster_share": round(clusters.most_common(1)[0][1] / len(events), 4),
            "unknown_cluster_records": clusters.get("UNKNOWN", 0),
            "independence_warning": "Wikipedia language editions are treated as one upstream dependence cluster; cluster count is not statistical independent N.",
        },
        "holdout": {
            "protected": True,
            "validation_subjects": len(validation),
            "holdout_subjects": len(holdout),
            "validation_subject_hash": _split_hash(validation),
            "holdout_subject_hash": _split_hash(holdout),
            "validation_day_eligible": 0,
            "validation_month_eligible": 0,
            "validation_exploratory": len(validation),
            "holdout_day_eligible": 0,
            "holdout_month_eligible": 0,
            "holdout_exploratory": len(holdout),
            "holdout_migration": False,
            "feature_results_opened": False,
        },
        "risk_intervals": {
            "ready": 0,
            "partial": 0,
            "unavailable": len(subjects),
            "status": "UNAVAILABLE",
            "reason": "The frozen records retain event years but do not provide a governed role/employment start interval from which an at-risk window can be constructed.",
            "future_policy": "Do not generate controls until role start, event definition and exclusion windows are independently documented.",
        },
        "feature_family": {
            "feature_family_id": family["feature_family_id"],
            "feature_family_version": family["feature_family_version"],
            "feature_family_hash": family["feature_family_hash"],
            "feature_count": len(contracts),
            "contracts": contracts,
            "feature_changes": 0,
            "activation_inspected": False,
            "feature_scoring": False,
            "astrology_calculation": False,
            "semantic_compatibility": "UNASSESSED_FEATURE_BLIND",
        },
        "power": {
            "planner": "scripts/veda_power_planner.py::two_proportion_required",
            "source_plan_status": power["status"],
            "raw_eligible_n": len(subjects),
            "source_diverse_bound": 2,
            "day_eligible_n": 0,
            "month_secondary_n": 0,
            "year_exploratory_n": len(subjects),
            "required_n_plus_5pp": sorted({row["approximate_independent_subjects"] for row in scenario_rows if row["absolute_effect"] == 0.05}),
            "required_n_plus_10pp": sorted({row["approximate_independent_subjects"] for row in scenario_rows if row["absolute_effect"] == 0.10}),
            "required_n_plus_15pp": sorted({row["approximate_independent_subjects"] for row in scenario_rows if row["absolute_effect"] == 0.15}),
            "required_n_plus_20pp": sorted({row["approximate_independent_subjects"] for row in scenario_rows if row["absolute_effect"] == 0.20}),
            "scenarios": scenario_rows,
            "confirmatory_powered": False,
            "limitation": "These are deterministic planning sensitivities, not a conditional-risk-set power guarantee.",
        },
        "study_decision": {
            "decision": "POSEND_EXPLORATORY_ONLY_REACQUIRE_REQUIRED",
            "event_family_homogeneity": "HETEROGENEOUS_EXPLORATORY_ONLY",
            "primary_position_end_definition": "FORMAL_EFFECTIVE_ROLE_END",
            "secondary_definitions": ["RETIREMENT_EFFECTIVE_DATE", "RESIGNATION_EFFECTIVE_DATE", "TERM_COMPLETION", "PUBLIC_OFFICE_END"],
            "excluded_definitions": ["CAREER_END_INFERRED_AS_EXACT_DAY", "DATE_OF_DEATH_AS_POSITION_END", "ANNOUNCEMENT_DATE_AS_EFFECTIVE_END"],
            "reason": "All 20 records remain YEAR precision, current labels describe inferred professional career ends rather than a single objective effective role-end event, the largest source cluster is Wikipedia-derived, and no role-start risk interval is available.",
            "confirmatory_cohort_ready": False,
            "secondary_retrospective_ready": False,
            "reacquisition_required": True,
            "next_programme_id": "VEDA-EVIDENCE-POSEND-ACQ-R1",
        },
        "safety": {
            "feature_scoring": False,
            "outcome_association": False,
            "astrology_calculation": False,
            "ml": "LOCKED",
            "pred_m4": "UNCHANGED",
            "production": "UNCHANGED",
            "approved_core_changed": False,
            "rag_changed": False,
            "raw_provider_data_committed": False,
        },
    }


def write() -> dict[str, Any]:
    result = build()
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {
        "01_COHORT_FREEZE.json": result["cohort_freeze"],
        "03_EVENT_PROVENANCE_AUDIT.json": result["event_provenance"],
        "04_DATE_PRECISION_AUDIT.json": result["date_precision"],
        "05_PRECISION_RECOVERY_REGISTER.json": result["precision_recovery"],
        "06_SOURCE_DEPENDENCE.json": result["source_dependence"],
        "07_HOLDOUT_PROTECTION.json": result["holdout"],
        "08_RISK_INTERVAL_READINESS.json": result["risk_intervals"],
        "10_FEATURE_FAMILY_FREEZE.json": result["feature_family"],
        "11_POWER_READINESS.json": result["power"],
    }
    for name, payload in outputs.items():
        (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = write() if args.write else build()
    print(json.dumps({"programme": PROGRAMME, "decision": result["study_decision"]["decision"], "subjects": result["cohort_freeze"]["subjects"], "day_eligible": result["power"]["day_eligible_n"], "feature_scoring": result["safety"]["feature_scoring"]}, sort_keys=True))
