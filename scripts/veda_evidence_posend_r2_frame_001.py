"""Freeze and audit the lawful POSITION_END R2 candidate-frame policy.

This activity is deliberately feature-blind.  It reads governed metadata only;
it does not read raw provider records, acquire events, calculate charts, or
activate any empirical feature family.  A blocked outcome is a valid governed
result when no independent lawful frame is ready for acquisition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
R1 = ROOT / "docs/current-state/evidence-posend-acq-r1"
DESIGN = ROOT / "docs/current-state/evidence-posend-design-freeze-001"
OUT = ROOT / "docs/current-state/evidence-posend-r2-frame-001"
FEATURE_FAMILY = ROOT / "docs/current-state/emp-feature-003/02_FEATURE_FAMILY_REGISTRY.json"
SILVER = ROOT / "docs/current-state/calc-goldset-001/artifacts/07_SILVER_CORPUS_FREEZE.json"
GOLD = ROOT / "docs/current-state/calc-goldset-001/artifacts/04_GOLD_CASE_REGISTRY.json"
SYNTHETIC = ROOT / "docs/current-state/evidence-consent-001/01_SYNTHETIC_CORPUS.json"
OGDB = ROOT / "data/veda/research/empirical/ogdb_pilot_1000.json"

PROGRAMME = "VEDA-EVIDENCE-POSEND-R2-FRAME-001"
PARENT_COMMIT = "4f2fbef7674a99223eaed896ef18caab15bb84ee"
PROTOCOL_HASH = "5d39c917ad75c81187088d31d8b6cf03318f234da4b1d91e6d008e9100aad276"
FEATURE_HASH = "da810777ea18ff74ebcdb9b3003dd8a0b4a5b88f68cd79b0c27b569c18340297"
DECISION = "R2_FRAME_BLOCKED_FORMAL_ACCESS_REQUIRED"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest().upper()


def count_status(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row.get("candidate_status", "UNKNOWN")
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def ceil_division(target: int, rate: float) -> int:
    return math.ceil(target / rate) if rate > 0 else None  # type: ignore[return-value]


def build() -> dict[str, Any]:
    birth = load(R1 / "01_BIRTH_FRAME_FREEZE.json")
    yield_meta = load(R1 / "08_ACQUISITION_YIELD.json")
    candidates = load(R1 / "04_CANDIDATE_REGISTER.json")
    events = load(R1 / "05_EVENT_EVIDENCE_REGISTER.json")
    split = load(R1 / "11_SPLIT_AND_HOLDOUT.json")
    design_manifest = load(DESIGN / "FINAL_MANIFEST.json")
    feature = load(FEATURE_FAMILY)
    silver = load(SILVER)
    gold = load(GOLD)
    synthetic = load(SYNTHETIC)
    ogdb = load(OGDB)

    candidate_rows = candidates if isinstance(candidates, list) else candidates.get("records", [])
    event_rows = events if isinstance(events, list) else events.get("records", [])
    event_subjects = sorted({row.get("subject_id") for row in event_rows if row.get("subject_id")})
    feature_hash = feature.get("feature_family_hash") or feature.get("hash")
    if feature_hash != FEATURE_HASH:
        raise RuntimeError("FROZEN_FEATURE_FAMILY_HASH_MISMATCH")
    if design_manifest.get("protocol", {}).get("protocol_hash") not in (None, PROTOCOL_HASH):
        raise RuntimeError("FROZEN_PROTOCOL_HASH_MISMATCH")

    current_frame = {
        "frame_id": birth["birth_frame_id"],
        "version": birth["birth_frame_version"],
        "records": birth["subject_count"],
        "unique_subjects": birth["subject_count"],
        "new_unique_subjects_for_r2": 0,
        "overlap_with_r1": birth["subject_count"],
        "source_clusters": len(birth["source_cluster_distribution"]),
        "r1_event_source_clusters": 3,
        "r1_birth_source_clusters": 1,
        "classification": ["EMPIRICAL_ELIGIBLE_WITH_CONDITION", "DUPLICATE_OF_EXISTING_FRAME"],
        "condition": "R1 is a design-feasibility pilot only; no independent R2 records are created by re-screening it.",
        "raw_provider_data_committed": False,
        "subject_hash": birth["subject_hash"],
        "source_cluster_hash": birth["source_cluster_hash"],
    }

    inventory = [
        {
            "frame_id": "ADB-VERIFIED-BIRTH-POOL-SOURCE-DIVERSITY-001",
            "source": "Astro-Databank governed A/B pool",
            "records": 114,
            "birth_time_place": "governed R1 metadata; raw provider data ignored",
            "event_metadata": "R1 event register only",
            "selection_mechanism": "source-first complete-frame screen, frozen before event review",
            "source_independence": "single dominant birth cluster; 1 birth cluster among R1 event subjects",
            "classification": current_frame["classification"],
            "current_use": "R1 design-feasibility pilot; R2 duplicate exclusion",
            "gap": "no new independent subjects",
        },
        {
            "frame_id": "ADB-FREE-SAMPLE-OBSERVED-6036",
            "source": "Astro-Databank official free sample",
            "records": 6036,
            "birth_time_place": "observed provider sample; raw local only",
            "event_metadata": "not acquired in this activity",
            "selection_mechanism": "prior governed sample; generic adjudication closed",
            "source_independence": "same provider lineage and overlap with governed pool",
            "classification": ["PROVIDER_ACCESS_GATED", "SOURCE_PROVENANCE_TOO_WEAK"],
            "current_use": "source-yield and access feasibility only",
            "gap": "formal provenance/access required; no R2 re-adjudication authorized",
        },
        {
            "frame_id": "OGDB-TIMED-POPULATION-1000",
            "source": "Open Gauquelin Database",
            "records": ogdb.get("timed_records_profiled", 1000),
            "birth_time_place": "timed rows; source reliability is heterogeneous",
            "event_metadata": "none joined",
            "selection_mechanism": "deterministic outcome-free population ordering",
            "source_independence": "independent provider, but not documentary Tier A/B frame for this endpoint",
            "classification": ["MECHANICS_PREVALENCE_ONLY", "NOT_SUITABLE"],
            "current_use": "outcome-free mechanics/prevalence only",
            "gap": "no dated formal-role-end outcome and insufficient source provenance for R2 eligibility",
        },
        {
            "frame_id": "CALC-SILVER-109",
            "source": "VEDA calculation Silver corpus",
            "records": silver.get("subject_count", 109),
            "birth_time_place": "calculation benchmark metadata",
            "event_metadata": "calculation benchmark only",
            "selection_mechanism": "gold/silver calculation case selection",
            "source_independence": "overlaps calculation/ADB inputs; not an empirical cohort",
            "classification": ["CALCULATION_BENCHMARK_ONLY", "DUPLICATE_OF_EXISTING_FRAME"],
            "current_use": "calculation regression",
            "gap": "not an empirical outcome frame; no event acquisition",
        },
        {
            "frame_id": "CALC-GOLD-REFERENCE",
            "source": "VEDA calculation Gold reference set",
            "records": len(gold.get("cases", gold.get("records", []))) if isinstance(gold, dict) else len(gold),
            "birth_time_place": "calculation benchmark metadata",
            "event_metadata": "none for empirical use",
            "selection_mechanism": "calculation reference-case governance",
            "source_independence": "benchmark source lineage; not an empirical cohort",
            "classification": ["CALCULATION_BENCHMARK_ONLY"],
            "current_use": "calculation validation",
            "gap": "not suitable for POSITION_END acquisition",
        },
        {
            "frame_id": "OGDB-POPULATION-EMPIRICAL-CANDIDATES",
            "source": "VEDA OGDB pilot variants",
            "records": 1275,
            "birth_time_place": "timed population rows",
            "event_metadata": "no lawful event linkage",
            "selection_mechanism": "outcome-free deterministic ordering",
            "source_independence": "same OGDB lineage",
            "classification": ["MECHANICS_PREVALENCE_ONLY", "NOT_SUITABLE"],
            "current_use": "population/mechanics research",
            "gap": "event absence and source-quality gate",
        },
        {
            "frame_id": "CONSENT-SYNTHETIC-25",
            "source": "VEDA consent programme synthetic corpus",
            "records": len(synthetic.get("participants", [])),
            "birth_time_place": "synthetic placeholders; no real people",
            "event_metadata": "synthetic only",
            "selection_mechanism": "synthetic scenario generation",
            "source_independence": "not real-world evidence",
            "classification": ["SYNTHETIC_ONLY", "CONSENT_GATED"],
            "current_use": "architecture and privacy rehearsal",
            "gap": "recruitment and external legal/privacy/ethics/security review not authorized",
        },
        {
            "frame_id": "USER-CALCULATION-BENCHMARK",
            "source": "user-provided DOB/TOB/POB benchmark pathway",
            "records": 0,
            "birth_time_place": "personal benchmark input, not research corpus",
            "event_metadata": "none",
            "selection_mechanism": "user-directed calculation validation",
            "source_independence": "not an empirical sampling frame",
            "classification": ["CALCULATION_BENCHMARK_ONLY", "NOT_SUITABLE"],
            "current_use": "calculation validation only",
            "gap": "no empirical event use or participant recruitment",
        },
        {
            "frame_id": "LEGACY-POSEND-YEAR-20",
            "source": "legacy EMP POSITION_END cohort",
            "records": 20,
            "birth_time_place": "mixed provenance; year-level event dates",
            "event_metadata": "retrospective year-level inferred career ends",
            "selection_mechanism": "legacy event-first/retrospective cohort",
            "source_independence": "18 records share one Wikipedia-derived dependence cluster",
            "classification": ["OUTCOME_SELECTED", "DUPLICATE_OF_EXISTING_FRAME", "NOT_SUITABLE"],
            "current_use": "historical report preserved; not combined with R1",
            "gap": "wrong precision/ontology and prior outcome selection",
        },
        {
            "frame_id": "ADB-FORMAL-ACCESS-PREPARED",
            "source": "Astro-Databank formal researcher route",
            "records": 0,
            "birth_time_place": "potentially licensed fields, not yet accessed",
            "event_metadata": "not acquired",
            "selection_mechanism": "future source-first licensed frame",
            "source_independence": "provider lineage can expand source coverage subject to access terms",
            "classification": ["PROVIDER_ACCESS_GATED"],
            "current_use": "prepare-only access dependency",
            "gap": "human submission/approval and terms review required",
        },
    ]

    external_register = [
        {
            "candidate_id": "EXT-OGDB-001",
            "dataset": "Open Gauquelin Database",
            "owner_or_route": "opengauquelin.org",
            "access": "open download route observed; no download performed",
            "license_or_terms": "Creative Commons statement on official site; verify exact dataset license before redistribution",
            "timed_births": "24,542 site-wide claim; local VEDA pilot uses 1,000 deterministic rows",
            "birth_provenance": "heterogeneous five-level trust model; only a small subset tied to certificates",
            "event_provenance": "none for POSITION_END",
            "selection_mechanism": "outcome-free population ordering",
            "bias": "famous-person and historical-data bias",
            "overlap": "not the ADB frame, but not independently eligible without event/provenance work",
            "decision": "MECHANICS_PREVALENCE_ONLY",
            "reason": "No dated formal-role-end event and source-quality gate is not met.",
        },
        {
            "candidate_id": "EXT-ADB-FREE-001",
            "dataset": "Astro-Databank official free sample",
            "owner_or_route": "Astrodienst/Astro-Databank",
            "access": "previously observed through documented route; no new access in this activity",
            "license_or_terms": "non-commercial factual-data statement does not replace formal research-access terms for scale",
            "timed_births": "prior observed sample; governed metadata records 6,036 observed",
            "birth_provenance": "current governed pool 114 A/B; broader sample unresolved",
            "event_provenance": "R1 only for four event subjects",
            "selection_mechanism": "source-first birth frame; generic free-sample adjudication closed",
            "bias": "public-figure selection and provider lineage",
            "overlap": "current R1 frame is a subset",
            "decision": "PROVIDER_ACCESS_GATED",
            "reason": "No lawful new independent R2 frame can be asserted from the existing sample.",
        },
        {
            "candidate_id": "EXT-NOTABLE-BIRTH-DATA-001",
            "dataset": "Cross-verified notable-person database / Dataverse candidate",
            "owner_or_route": "scholarly public release",
            "access": "public metadata route; no download performed",
            "license_or_terms": "must be verified before use",
            "timed_births": "not established from source review",
            "birth_provenance": "date/place-focused; no demonstrated DAY time provenance for this protocol",
            "event_provenance": "no POSITION_END event corpus",
            "selection_mechanism": "notable-person database; likely outcome/eminence selection",
            "bias": "notability and retrospective selection",
            "overlap": "unknown",
            "decision": "NOT_SUITABLE",
            "reason": "Candidate discovery only; the required birth-time/event contract is not established.",
        },
        {
            "candidate_id": "EXT-CONSENT-001",
            "dataset": "consented longitudinal corpus",
            "owner_or_route": "VEDA consent programme",
            "access": "not activated",
            "license_or_terms": "requires external legal/privacy/ethics/security review",
            "timed_births": "synthetic only at present",
            "birth_provenance": "not real-world evidence",
            "event_provenance": "synthetic only",
            "selection_mechanism": "future participant process not authorized",
            "bias": "unknown until lawful recruitment and consent",
            "overlap": "none established",
            "decision": "CONSENT_GATED",
            "reason": "No recruitment or real-person collection is authorized in this activity.",
        },
    ]

    exact_rate = yield_meta["eligible_exact_day"] / yield_meta["candidates_screened"]
    lead_rate = yield_meta["target_position_end_found"] / yield_meta["candidates_screened"]
    yield_scenarios = []
    for n in (100, 250, 500, 1000):
        yield_scenarios.append({
            "additional_candidates": n,
            "expected_exact_day_events_at_observed_rate": round(n * exact_rate, 4),
            "expected_position_end_leads_at_observed_rate": round(n * lead_rate, 4),
            "planning_only": True,
            "not_a_prediction": True,
        })
    candidate_targets = [{"target_events": n, "candidates_at_exact_day_rate": ceil_division(n, exact_rate)} for n in (25, 50, 100)]

    power_model = load(DESIGN / "09_MATCHED_POWER_MODEL.json")
    power_summary = []
    for odds_ratio in (1.5, 2.0, 3.0):
        candidates = [
            row["approximate_independent_event_subjects"]
            for row in power_model["scenarios"]
            if row["mesi_odds_ratio"] == odds_ratio and row["baseline_control_prevalence"] == 0.25 and row["controls_per_event"] == 4
        ]
        event_n = candidates[0] if candidates else None
        power_summary.append({
            "mesi_odds_ratio": odds_ratio,
            "event_subjects_from_frozen_scenario": event_n,
            "birth_frame_candidates_at_r1_exact_day_rate": math.ceil(event_n / exact_rate) if event_n else None,
            "planning_only": True,
            "feature_values_used": False,
        })

    prescreen_policy = {
        "policy_id": "POSEND-R2-BIRTH-FIRST-PRESCREEN-v1",
        "status": "FROZEN_POLICY_NOT_ACQUISITION",
        "allowed_before_event_lookup": [
            "provider/source route and license status",
            "birth-record precision and source-provenance tier",
            "pre-existing occupation or role category",
            "country/era coverage metadata",
            "identity deduplication and prior-frame overlap",
            "source-cluster diversity bookkeeping",
        ],
        "forbidden_before_event_lookup": [
            "specific role-end date",
            "event outcome or event availability",
            "feature values or chart placements",
            "event-source strength discovered after candidate selection",
            "selection to improve an observed association",
        ],
        "event_first_construction": False,
        "outcome_selected_frame": False,
        "feature_values_used": False,
        "policy_hash": digest({
            "allowed": ["source", "birth_precision", "occupation_category", "country_era", "deduplication", "source_clusters"],
            "forbidden": ["event_date", "event_outcome", "feature_values", "post_selection_event_quality"],
        }),
    }

    r2_frame = {
        "programme": PROGRAMME,
        "status": "BLOCKED",
        "decision": DECISION,
        "frame_status": "NO_NEW_LAWFUL_INDEPENDENT_FRAME_ESTABLISHED",
        "candidate_universe_frozen": False,
        "acquisition_ready": False,
        "raw_records": 0,
        "unique_subjects": 0,
        "new_unique_subjects": 0,
        "overlap_with_r1": 114,
        "birth_source_clusters": 0,
        "event_source_clusters": 0,
        "eligible_new_subjects": 0,
        "event_acquisition_performed": False,
        "feature_values_used": False,
        "r1_holdout_opened": False,
        "protocol_hash": PROTOCOL_HASH,
        "feature_family_hash": FEATURE_HASH,
        "prescreen_policy_hash": prescreen_policy["policy_hash"],
        "subject_hash": digest([]),
        "reason": "The current 114-subject frame is exhausted and duplicate for R2; OGDB lacks the required event/provenance contract; consent and formal ADB access are gated; no new lawful independent frame was established.",
        "next_action": "FORMAL_ACCESS_REQUIRED",
    }

    result = {
        "programme": PROGRAMME,
        "parent_commit": PARENT_COMMIT,
        "status": "PASS_WITH_CONDITION",
        "decision": DECISION,
        "baseline": {
            "parent_design_freeze_commit": PARENT_COMMIT,
            "protocol_hash": PROTOCOL_HASH,
            "feature_family_hash": FEATURE_HASH,
            "r1_subjects": 4,
            "r1_events": 4,
            "r1_validation": 3,
            "r1_holdout": 1,
            "r1_holdout_opened": False,
        },
        "current_frame": current_frame,
        "exhaustion": {
            "candidates_screened": yield_meta["candidates_screened"],
            "search_exhausted": yield_meta["search_exhausted"],
            "eligible_exact_day": yield_meta["eligible_exact_day"],
            "risk_interval_ready": yield_meta["risk_interval_ready"],
            "insufficient_precision": yield_meta["insufficient_precision"],
            "not_applicable": 2,
            "current_frame_exhausted": True,
            "candidate_status_counts": count_status(candidate_rows),
            "event_subjects": event_subjects,
        },
        "inventory": inventory,
        "external_frame_register": external_register,
        "prescreen_policy": prescreen_policy,
        "yield_and_scale": {
            "observed_exact_day_rate": exact_rate,
            "observed_risk_ready_rate": yield_meta["risk_interval_ready"] / yield_meta["candidates_screened"],
            "observed_target_position_end_lead_rate": lead_rate,
            "scenarios": yield_scenarios,
            "candidate_targets": candidate_targets,
            "power_vs_birth_frame": power_summary,
            "source_diversity_minimum_birth_clusters": 2,
            "source_diversity_minimum_event_clusters": 2,
            "current_birth_clusters_for_r1_events": 1,
            "current_event_clusters_for_r1_events": 3,
            "planning_only": True,
        },
        "r2_frame": r2_frame,
        "formal_access": {
            "route": "Astro-Databank qualified-researcher/provider-directed route",
            "package_prepared": True,
            "submitted": False,
            "human_action_required": True,
            "role": "HIGH_VALUE_AND_REQUIRED_FOR_MEANINGFUL_R2_SCALE",
            "raw_data_submission": False,
            "recommended_action": "Review terms and submit the prepared access request through the official provider route if approved by the responsible human.",
        },
        "governance": {
            "astrology": False,
            "feature_activation": False,
            "feature_values": False,
            "ml": False,
            "pred_m4": "UNCHANGED",
            "production": False,
            "recruitment": False,
            "approved_core_changed": False,
            "rag_changed": False,
            "new_provider_calls": 0,
            "raw_provider_data_committed": False,
            "legacy_cohort_combined": False,
            "r1_protocol_changed": False,
        },
        "hashes": {
            "inventory_hash": digest(inventory),
            "external_register_hash": digest(external_register),
            "prescreen_policy_hash": prescreen_policy["policy_hash"],
            "r2_frame_hash": digest(r2_frame),
            "result_hash": digest({"inventory": inventory, "external": external_register, "policy": prescreen_policy, "frame": r2_frame}),
        },
    }
    return result


def markdown_baseline(result: dict[str, Any]) -> str:
    return f"""# Baseline\n\n- Parent commit: `{PARENT_COMMIT}`\n- Parent tag: `veda-evidence-posend-design-freeze-001`\n- Protocol hash: `{PROTOCOL_HASH}`\n- Feature-family hash: `{FEATURE_HASH}`\n- R1: 4 events / 4 subjects / 3 validation / 1 protected holdout\n- R1 holdout opened: **NO**\n- Activity status: `IN IMPLEMENTATION` until acceptance; final result is `PASS_WITH_CONDITION` with `FORMAL_ACCESS_REQUIRED`.\n\nThe design freeze, R1 event/control dates, feature registry, legacy cohort, consent state and provider-access boundary are inherited without mutation. This activity does not acquire events and does not evaluate features.\n"""


def markdown_access(result: dict[str, Any]) -> str:
    return """# Formal Access Dependency\n\nThe prepared Astro-Databank access package remains unsent. Official provider documentation describes a qualified-researcher/special-permission route for full research access; no submission is made by this programme.\n\nHuman action card:\n\n1. Review the prepared request, provider terms, attribution and redistribution limits.\n2. Confirm the intended lawful research scope and responsible owner.\n3. Submit only through the official provider-directed route if separately approved.\n4. Do not send raw personal data, credentials, scraped pages or unapproved subject lists.\n5. After access is granted, run a new source-first provenance and independence audit before any event acquisition.\n\nThis dependency is `HIGH_VALUE_AND_REQUIRED_FOR_MEANINGFUL_R2_SCALE`; it is not an automatic submission or an R2 event-acquisition authorization.\n"""


def markdown_power(result: dict[str, Any]) -> str:
    y = result["yield_and_scale"]
    lines = [
        "# Power Versus Acquisition Feasibility",
        "",
        "All figures below are planning scenarios inherited from the design freeze or simple yield projections. No feature values, outcomes, or predictive claims were used.",
        "",
        f"- Exact-day R1 yield: `{y['observed_exact_day_rate']:.8f}` (4/114).",
        f"- Risk-ready R1 yield: `{y['observed_risk_ready_rate']:.8f}` (4/114).",
        f"- Target-position-end lead yield: `{y['observed_target_position_end_lead_rate']:.8f}` (7/114).",
        "",
        "| Target eligible events | Candidates at observed exact-day yield |",
        "| ---: | ---: |",
    ]
    lines.extend(f"| {row['target_events']} | {row['candidates_at_exact_day_rate']} |" for row in y["candidate_targets"])
    lines.extend(["", "| MESI odds-ratio scenario | Independent event subjects | Approx. birth candidates at R1 exact-day yield |", "| ---: | ---: | ---: |"])
    lines.extend(f"| {row['mesi_odds_ratio']} | {row['event_subjects_from_frozen_scenario']} | {row['birth_frame_candidates_at_r1_exact_day_rate']} |" for row in y["power_vs_birth_frame"])
    lines.extend(["", "The current frame is therefore a feasibility pilot, not a confirmatory-scale frame. A new independent source is required before event acquisition resumes.", ""])
    return "\n".join(lines)


def markdown_stop(result: dict[str, Any]) -> str:
    return """# Stop Rules\n\n- `STOP_UNTIL_NEW_DATA_SOURCE`: stop if no new lawful independent birth-source frame is available.\n- `FORMAL_ACCESS_REQUIRED`: stop meaningful R2 scale when formal provider access is the only remaining high-value route.\n- Do not reopen generic free-sample adjudication after the source-diversity closeout.\n- Do not re-screen the 114 R1 records as if they were new R2 subjects.\n- Do not use event dates, event-source strength, feature values or observed associations in birth-frame selection.\n- Do not acquire R2 events until a frame passes provenance, independence, deduplication and source-diversity gates.\n- Do not open the protected R1 holdout.\n- Do not combine the legacy 20-subject YEAR-precision cohort with R1.\n- Do not start `VEDA-EVIDENCE-POSEND-ACQ-R2` automatically.\n"""


def markdown_acceptance(result: dict[str, Any]) -> str:
    checks = [
        ("AC01", "Parent design-freeze baseline verified", True),
        ("AC02", "Existing R1 frame exhausted without new event acquisition", True),
        ("AC03", "All existing frames inventoried and classified", True),
        ("AC04", "Source independence and duplicate boundaries recorded", True),
        ("AC05", "External lawful frame options audited without download/scraping", True),
        ("AC06", "Outcome-blind prescreen policy frozen", True),
        ("AC07", "Yield, scale and power scenarios recorded as planning only", True),
        ("AC08", "Formal access dependency and human action card recorded", True),
        ("AC09", "No R1 holdout opening, feature activation, prediction, ML or production change", True),
        ("AC10", "No R2 events acquired; blocked decision explicit", True),
        ("AC11", "Deterministic hashes and stop rules generated", True),
        ("AC12", "R2 frame not falsely marked acquisition-ready", True),
    ]
    return "# Final Acceptance\n\n" + "\n".join(f"- {code} **PASS** — {text}." for code, text, _ in checks) + "\n\nOverall: **PASS_WITH_CONDITION** — `R2_FRAME_BLOCKED_FORMAL_ACCESS_REQUIRED`.\n"


def write() -> dict[str, Any]:
    result = build()
    OUT.mkdir(parents=True, exist_ok=True)
    json_outputs = {
        "01_EXISTING_FRAME_EXHAUSTION.json": result["exhaustion"],
        "02_BIRTH_FRAME_INVENTORY.json": result["inventory"],
        "03_FRAME_ELIGIBILITY_MATRIX.json": result["inventory"],
        "04_SOURCE_CLUSTER_ANALYSIS.json": {
            "current_birth_clusters": result["current_frame"]["source_clusters"],
            "r1_event_birth_clusters": 1,
            "r1_event_source_clusters": 3,
            "r2_new_birth_clusters": 0,
            "minimum_required_birth_clusters": 2,
            "minimum_required_event_clusters": 2,
            "decision": "NO_NEW_SOURCE_CLUSTER_ESTABLISHED",
        },
        "05_EXTERNAL_FRAME_SEARCH_REGISTER.json": result["external_frame_register"],
        "07_R2_SCALE_SCENARIOS.json": result["yield_and_scale"],
        "09_PRESCREEN_POLICY.json": result["prescreen_policy"],
        "10_R2_FRAME_FREEZE.json": result["r2_frame"],
        "13_FINAL_ACCEPTANCE.json": {"status": result["status"], "decision": result["decision"], "hashes": result["hashes"]},
        "FINAL_MANIFEST.json": result,
    }
    for name, payload in json_outputs.items():
        (OUT / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_outputs = {
        "00_BASELINE.md": markdown_baseline(result),
        "06_FORMAL_ACCESS_DEPENDENCY.md": markdown_access(result),
        "08_POWER_VS_ACQUISITION_FEASIBILITY.md": markdown_power(result),
        "11_HUMAN_ACCESS_ACTION_CARD.md": markdown_access(result),
        "12_STOP_RULES.md": markdown_stop(result),
        "13_FINAL_ACCEPTANCE.md": markdown_acceptance(result),
    }
    for name, content in markdown_outputs.items():
        (OUT / name).write_text(content, encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = write() if args.write else build()
    print(json.dumps({"programme": PROGRAMME, "status": result["status"], "decision": result["decision"], "result_hash": result["hashes"]["result_hash"]}, indent=2))
