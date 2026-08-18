"""Build the feature-blind exact-day POSITION_END acquisition corpus.

This activity consumes only the already governed ADB birth frame and
documentary role evidence.  It deliberately does not import a chart engine,
feature registry, prediction code, or any astrology output.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

try:
    from scripts.veda_power_planner import two_proportion_required
except ModuleNotFoundError:  # pragma: no cover - direct script execution
    from veda_power_planner import two_proportion_required


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/current-state/evidence-posend-acq-r1"
PROGRAMME = "VEDA-EVIDENCE-POSEND-ACQ-R1"
VERSION = "1.0.0"
RETRIEVED = "2026-08-18"
FEATURE_FAMILY_HASH = "da810777ea18ff74ebcdb9b3003dd8a0b4a5b88f68cd79b0c27b569c18340297"

# Reconstructed from the latest governed source-diversity pool.  These are
# identifiers only; raw ADB records remain local and ignored.
FRAME_IDS = [
    1624, 1794, 2499, 2919, 2940, 5376, 11979, 14954, 24426, 25838,
    27098, 27103, 27124, 27141, 27150, 44912, 50608, 50739, 50740,
    50754, 50785, 50791, 50793, 50796, 50806, 50807, 50808, 50809,
    50810, 50811, 50812, 50822, 50831, 50836, 50838, 50852, 50871,
    50872, 50879, 50944, 50946, 50947, 50951, 50997, 51634, 51672,
    51916, 51917, 52110, 52112, 52175, 52199, 52201, 52206, 52207,
    52215, 52216, 52243, 52244, 52245, 52246, 52305, 52425, 52561,
    52562, 52563, 52686, 52741, 53129, 53347, 53379, 53387, 53408,
    53409, 53412, 53433, 53434, 53440, 53441, 53442, 53443, 53460,
    53504, 53516, 53525, 53674, 53684, 53686, 53756, 53865, 53866,
    53874, 53876, 53883, 53894, 54007, 54065, 54066, 54067, 54068,
    54069, 54103, 54105, 54193, 54250, 54251, 54252, 54276, 54277,
    54321, 54322, 62690, 74050, 75059,
]

FRAME_TIER_DISTRIBUTION = {"A": 37, "B": 77}
FRAME_SOURCE_CLUSTERS = {
    "STEINBRECHER_COLLECTION": 92,
    "OTHER_OR_UNRESOLVED": 8,
    "SY_SCHOLFIELD_SUBMISSIONS": 6,
    "UNKNOWN": 5,
    "GRAZIA_BORDONI_COLLECTION": 2,
    "DIDIER_GESLAIN_ARCHIVE": 1,
}

EVENTS = [
    {
        "event_id": "POSEND-ADB-51916-NA-MANDATE-1997-2002",
        "subject_id": "ADB-51916",
        "role_id": "ROLE-ADB-51916-NA-DEPUTY-XI",
        "subject_label": "Nicole Catala",
        "role_title": "Member of the French National Assembly",
        "organization": "Assemblée nationale",
        "role_type": "ELECTED_PUBLIC_OFFICE",
        "country": "FR",
        "role_start_date": "1997-06-01",
        "role_end_date": "2002-06-18",
        "start_semantics": "official mandate start",
        "end_semantics": "end of legislature",
        "event_type": "POSITION_END",
        "event_subtype": "TERM_COMPLETION",
        "event_reason": "TERM_COMPLETED",
        "event_tier": "A",
        "event_source_cluster": "ASSEMBLEE_NATIONALE_OFFICIAL",
        "event_source": "https://www.assemblee-nationale.fr/11/tribun/fiches_id/764.asp",
        "corroborating_source": "https://www2.assemblee-nationale.fr/sycomore/fiche?num_dept=1514",
        "source_claim": "The official National Assembly record gives the mandate as 1997-06-01 through 2002-06-18.",
        "birth_tier": "B",
        "birth_source_cluster": "STEINBRECHER_COLLECTION",
    },
    {
        "event_id": "POSEND-ADB-53387-EC-COMMISSIONER-1985-1989",
        "subject_id": "ADB-53387",
        "role_id": "ROLE-ADB-53387-EC-EXTERNAL-RELATIONS",
        "subject_label": "Willy de Clercq",
        "role_title": "European Commissioner for External Relations and Trade",
        "organization": "European Commission",
        "role_type": "INSTITUTIONAL_PUBLIC_OFFICE",
        "country": "BE",
        "role_start_date": "1985-01-06",
        "role_end_date": "1989-01-05",
        "start_semantics": "official commissioner term start",
        "end_semantics": "official commissioner term end",
        "event_type": "POSITION_END",
        "event_subtype": "TERM_COMPLETION",
        "event_reason": "TERM_COMPLETED",
        "event_tier": "A",
        "event_source_cluster": "EUROPEAN_COMMISSION_OFFICIAL",
        "event_source": "https://belgium.representation.ec.europa.eu/about-us/la-belgique-dans-lue_fr?prefLang=bg",
        "corroborating_source": "https://www.vlaamsparlement.be/nl/vlaamse-volksvertegenwoordigers-het-vlaams-parlement/willy-de-clercq",
        "source_claim": "Official European institutional history places de Clercq in the Commission from 1985 to 1989; the institutional biography gives 1985-01-06 through 1989-01-05.",
        "birth_tier": "B",
        "birth_source_cluster": "STEINBRECHER_COLLECTION",
    },
    {
        "event_id": "POSEND-ADB-53441-SENATE-PRESIDENT-1983",
        "subject_id": "ADB-53441",
        "role_id": "ROLE-ADB-53441-SENATE-PRESIDENT-VIII",
        "subject_label": "Vittorino Colombo",
        "role_title": "President of the Senate of the Republic",
        "organization": "Senato della Repubblica",
        "role_type": "ELECTED_PUBLIC_OFFICE",
        "country": "IT",
        "role_start_date": "1983-05-12",
        "role_end_date": "1983-07-11",
        "start_semantics": "official election/assumption of office",
        "end_semantics": "official end of VIII Legislature office record",
        "event_type": "POSITION_END",
        "event_subtype": "TERM_COMPLETION",
        "event_reason": "TERM_COMPLETED",
        "event_tier": "A",
        "event_source_cluster": "SENATO_ITALIAN_OFFICIAL",
        "event_source": "https://www.senato.it/legislature/8/composizione/senatori/elenco-alfabetico/scheda-attivita?did=00000640",
        "corroborating_source": "https://www.senato.it/legislature/8/composizione/consiglio-di-presidenza/composizione",
        "source_claim": "The Senate activity record gives the presidency as 1983-05-12 through 1983-07-11.",
        "birth_tier": "B",
        "birth_source_cluster": "STEINBRECHER_COLLECTION",
    },
    {
        "event_id": "POSEND-ADB-53866-NA-MANDATE-2002-2007",
        "subject_id": "ADB-53866",
        "role_id": "ROLE-ADB-53866-NA-DEPUTY-XII",
        "subject_label": "Pierre Cardo",
        "role_title": "Member of the French National Assembly",
        "organization": "Assemblée nationale",
        "role_type": "ELECTED_PUBLIC_OFFICE",
        "country": "FR",
        "role_start_date": "2002-06-19",
        "role_end_date": "2007-06-19",
        "start_semantics": "official mandate start after general election",
        "end_semantics": "end of legislature",
        "event_type": "POSITION_END",
        "event_subtype": "TERM_COMPLETION",
        "event_reason": "TERM_COMPLETED",
        "event_tier": "A",
        "event_source_cluster": "ASSEMBLEE_NATIONALE_OFFICIAL",
        "event_source": "https://www.assemblee-nationale.fr/13/tribun/xml/xml/acteurs/734.asp",
        "corroborating_source": "https://www.senat.fr/compte-rendu-commissions/20100705/eco.html",
        "source_claim": "The official National Assembly record gives the mandate start as 2002-06-19 and end as 2007-06-19.",
        "birth_tier": "B",
        "birth_source_cluster": "STEINBRECHER_COLLECTION",
    },
]

KNOWN_SCREENING = {
    1624: ("NOT_APPLICABLE", "A death-in-role endpoint is not used for the first non-mortality cohort."),
    25838: ("EVENT_FOUND_BUT_INSUFFICIENT_PRECISION", "Public retirement evidence resolves only to May 1991."),
    44912: ("NOT_APPLICABLE", "The presidency ended by death; mortality endpoints are excluded from the primary lane."),
}
EVENT_SUBJECTS = {int(row["subject_id"].split("-")[1]) for row in EVENTS}


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest().upper()


def iso_day(value: str) -> date:
    parsed = date.fromisoformat(value)
    return parsed


def interval_rows() -> list[dict[str, Any]]:
    rows = []
    for event in EVENTS:
        start = iso_day(event["role_start_date"])
        end = iso_day(event["role_end_date"])
        duration = (end - start).days
        rows.append({
            "event_id": event["event_id"],
            "subject_id": event["subject_id"],
            "role_id": event["role_id"],
            "role_start": event["role_start_date"],
            "role_end": event["role_end_date"],
            "start_precision": "DAY",
            "end_precision": "DAY",
            "role_duration_days": duration,
            "risk_interval_state": "RISK_INTERVAL_READY" if duration > 2 else "RISK_INTERVAL_TOO_SHORT_FOR_PLANNED_CONTROLS",
        })
    return rows


def controls(intervals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for row in intervals:
        start = iso_day(row["role_start"])
        duration = int(row["role_duration_days"])
        for index, fraction in enumerate((1, 2), start=1):
            control_date = start + timedelta(days=(duration * fraction) // 3)
            result.append({
                "control_id": f"CTRL-{row['event_id']}-{index}",
                "subject_id": row["subject_id"],
                "event_id": row["event_id"],
                "control_date": control_date.isoformat(),
                "sampling": "FIXED_WITHIN_ROLE_INTERVAL_THIRDS",
                "inside_role_interval": row["role_start"] < control_date.isoformat() < row["role_end"],
                "post_event": False,
            })
    return result


def candidate_register() -> list[dict[str, Any]]:
    rows = []
    for adb_id in sorted(FRAME_IDS):
        subject_id = f"ADB-{adb_id}"
        if adb_id in EVENT_SUBJECTS:
            status = "ELIGIBLE_EXACT_DAY"
            reason = "Official/institutional documentary role start and effective role end both resolve to DAY precision."
        elif adb_id in KNOWN_SCREENING:
            status, reason = KNOWN_SCREENING[adb_id]
        else:
            status = "SEARCH_EXHAUSTED"
            reason = "Bounded public-source discovery did not resolve a non-mortality formal role with both DAY boundaries; weaker biography-only leads were not promoted."
        rows.append({
            "candidate_id": f"CAND-{adb_id}",
            "subject_id": subject_id,
            "adb_record_id": adb_id,
            "candidate_status": status,
            "screening_policy": "BIRTH_FRAME_FIRST_PUBLIC_ROLE_DISCOVERY_R1",
            "astrology_used": False,
            "feature_values_used": False,
            "reason": reason,
        })
    return rows


def build() -> dict[str, Any]:
    candidates = candidate_register()
    intervals = interval_rows()
    control_rows = controls(intervals)
    split_subjects = sorted({row["subject_id"] for row in EVENTS})
    validation = split_subjects[:-1]
    holdout = split_subjects[-1:]
    birth_frame = {
        "birth_frame_id": "ADB-VERIFIED-BIRTH-POOL-SOURCE-DIVERSITY-001",
        "birth_frame_version": "VEDA-EVIDENCE-ADB-SOURCE-DIVERSITY-001/R1",
        "subject_count": len(FRAME_IDS),
        "subject_ids": FRAME_IDS,
        "subject_hash": "00A440AC49A2C9DEA623C5665334F33729B72ECA88FAA6E9BCEE27077AA84D66",
        "tier_distribution": FRAME_TIER_DISTRIBUTION,
        "source_cluster_distribution": FRAME_SOURCE_CLUSTERS,
        "source_cluster_hash": "622B990479B75955234E03BF51B35CA5D1134DF1E13E067B0DD83CC0C3EADA8C",
        "selection_policy": "latest governed verified A/B pool; source-first complete-frame screen; no outcome/chart/feature selection",
        "selection_policy_hash": digest("latest governed verified A/B pool; source-first complete-frame screen; no outcome/chart/feature selection"),
        "raw_provider_data_committed": False,
    }
    split = {
        "split_id": "POSEND-ACQ-R1-SPLIT-001",
        "policy": "subject-level deterministic lexicographic split after acquisition freeze; final subject reserved as holdout",
        "acquisition_frozen_before_split": True,
        "feature_results_inspected": False,
        "validation_subjects": validation,
        "holdout_subjects": holdout,
        "validation_subject_hash": digest(validation),
        "holdout_subject_hash": digest(holdout),
        "holdout_event_hash": digest([row for row in EVENTS if row["subject_id"] in holdout]),
        "holdout_protected": True,
    }
    scenarios = [
        two_proportion_required(0.10, target, design_effect=1.10, exclusion_fraction=0.15)
        for target in (0.15, 0.20, 0.25, 0.30)
    ]
    yield_counts = {
        "candidates_screened": len(candidates),
        "target_position_end_found": 7,
        "no_target_event": 0,
        "insufficient_precision": 1,
        "weak_source": 0,
        "definition_ambiguous": 0,
        "search_exhausted": 107,
        "eligible_exact_day": len(EVENTS),
        "day_role_start": len(EVENTS),
        "day_role_end": len(EVENTS),
        "day_start_and_end": len(EVENTS),
        "strong_event_source": len(EVENTS),
        "birth_event_eligible": len(EVENTS),
        "risk_interval_ready": sum(row["risk_interval_state"] == "RISK_INTERVAL_READY" for row in intervals),
        "india_candidates": 0,
        "india_eligible_events": 0,
    }
    source_clusters = sorted({row["event_source_cluster"] for row in EVENTS})
    source_quality = {
        "primary_official": len(EVENTS),
        "institutional": 0,
        "strong_structured": 0,
        "secondary": 0,
        "discovery_only": 0,
        "event_source_clusters": source_clusters,
        "largest_event_cluster_share": 2 / len(EVENTS),
        "birth_source_clusters": ["STEINBRECHER_COLLECTION"],
        "largest_birth_cluster_share": 1.0,
        "birth_event_provenance_separated": True,
    }
    return {
        "programme": PROGRAMME,
        "version": VERSION,
        "retrieved": RETRIEVED,
        "status": "PASS_WITH_CONDITION",
        "feature_blind": True,
        "astrology_blind": True,
        "birth_frame": birth_frame,
        "candidate_register": candidates,
        "events": EVENTS,
        "role_intervals": intervals,
        "source_quality": source_quality,
        "yield": yield_counts,
        "control_design": {
            "preferred_design": "WITHIN_ROLE_INTERVAL_FIXED_RISK_SET_PILOT",
            "estimand": "future feature-blind comparison of event dates against pre-event dates while the formal role is active",
            "policy_frozen": True,
            "policy_hash": digest("WITHIN_ROLE_INTERVAL_FIXED_RISK_SET_PILOT|two controls at one-third and two-thirds of frozen role duration|before event|exclude competing events|no feature selection"),
            "controls_generated": True,
            "controls": control_rows,
            "control_date_hash": digest(control_rows),
            "all_controls_within_risk_interval": all(row["inside_role_interval"] and not row["post_event"] for row in control_rows),
            "calendar_matching": "not applied in this pilot; month/weekday matching requires a preregistered estimand decision",
        },
        "new_cohort": {
            "cohort_id": "POSEND-ACQ-R1-EXACTDAY-PILOT-001",
            "event_definition": "FORMAL_EFFECTIVE_END_DATE of a distinct public/institutional role; non-mortality first cohort",
            "event_selection_policy": "FIRST_ELIGIBLE_FORMAL_ROLE_END_AFTER_ACQUISITION_FREEZE",
            "one_event_per_subject": True,
            "eligible_subjects": len(EVENTS),
            "eligible_events": len(EVENTS),
            "non_mortality_events": len(EVENTS),
            "subject_hash": digest(sorted(row["subject_id"] for row in EVENTS)),
            "event_hash": digest(EVENTS),
            "source_diverse_bound": 1,
            "source_diverse_bound_event_only": len(source_clusters),
        },
        "split": split,
        "power": {
            "day_eligible_n": len(EVENTS),
            "risk_set_ready_n": len(EVENTS),
            "source_diverse_bound": 1,
            "scenarios": scenarios,
            "powered": False,
            "interpretation": "planning requirements only; current pilot is not powered and no feature effect was estimated",
        },
        "decisions": {
            "event_family": "FORMAL_PUBLIC_ROLE_END_PILOT_ONLY",
            "study_readiness": "POSEND_EXACTDAY_PILOT_READY",
            "reason": "Four official exact-day non-mortality role intervals were acquired from a 114-subject governed birth frame. The pilot is small, all four birth records share one dominant source cluster, and no confirmatory inference is justified.",
            "next_programme": "VEDA-EVIDENCE-POSEND-DESIGN-FREEZE-001",
            "automatically_started": False,
        },
        "feature_governance": {
            "feature_family_hash": FEATURE_FAMILY_HASH,
            "feature_activation_accessed": False,
            "feature_scoring": False,
            "outcome_association": False,
            "ml": "LOCKED",
            "pred_m4": "UNCHANGED",
            "production": "UNCHANGED",
        },
        "legacy": {
            "state": "EXPLORATORY_LEGACY_FEASIBILITY",
            "subjects": 20,
            "feature_scoring": False,
            "holdout_preserved": True,
            "historical_artifacts_modified": False,
        },
        "india": {"candidates": 0, "eligible_events": 0, "limitation": "The current governed frame has no India candidate in this acquisition screen; standards were not lowered."},
        "bias": {
            "geographic": "FR/BE/IT event pilot; frame is dominated by European public biographies",
            "era": "role ends 1983-2007; historical office records dominate",
            "occupation": "public office only among eligible events",
            "public_figure": "high; formal public roles are the target family",
            "birth_availability": "ADB verified A/B source availability; not representative of the general population",
            "role_type": "elected or institutional public office only",
            "source_dependence": "all four birth inputs share STEINBRECHER_COLLECTION; event sources are three official publisher clusters",
        },
        "provenance": {
            "birth_event_separated": True,
            "source_registry_urls": sorted({url for row in EVENTS for url in (row["event_source"], row["corroborating_source"])}),
            "minimal_excerpts_only": True,
            "wikipedia_final_authority": False,
            "retrieval_date": RETRIEVED,
        },
        "rag": "UNCHANGED",
        "raw_adb": "LOCAL_IGNORED_UNCOMMITTED",
        "astrology": "NOT_EXECUTED",
    }


def write_artifacts(output: Path = OUT) -> dict[str, Any]:
    result = build()
    output.mkdir(parents=True, exist_ok=True)
    files = {
        "01_BIRTH_FRAME_FREEZE.json": result["birth_frame"],
        "04_CANDIDATE_REGISTER.json": result["candidate_register"],
        "05_EVENT_EVIDENCE_REGISTER.json": result["events"],
        "06_ROLE_INTERVAL_REGISTER.json": result["role_intervals"],
        "07_SOURCE_DEPENDENCE.json": result["source_quality"],
        "08_ACQUISITION_YIELD.json": result["yield"],
        "10_NEW_COHORT_FREEZE.json": result["new_cohort"],
        "11_SPLIT_AND_HOLDOUT.json": result["split"],
        "13_POWER_READINESS.json": result["power"],
        "FINAL_MANIFEST.json": result,
    }
    for name, payload in files.items():
        (output / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    result = write_artifacts(args.output)
    print(json.dumps({"programme": PROGRAMME, "status": result["status"], "frame": len(FRAME_IDS), "eligible_events": len(EVENTS), "study_readiness": result["decisions"]["study_readiness"], "subject_hash": result["new_cohort"]["subject_hash"], "event_hash": result["new_cohort"]["event_hash"], "control_date_hash": result["control_design"]["control_date_hash"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
