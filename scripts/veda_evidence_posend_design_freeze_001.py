"""Feature-blind POSEND study-design freeze and matched-power planning."""
from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import date
from pathlib import Path
from statistics import NormalDist
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
R1_PATH = ROOT / "docs/current-state/evidence-posend-acq-r1/FINAL_MANIFEST.json"
FEATURE_PATH = ROOT / "docs/current-state/emp-feature-003/02_FEATURE_FAMILY_REGISTRY.json"
LEGACY_PATH = ROOT / "docs/current-state/emp-posend-acq-001/04_FINAL_MANIFEST.json"
OUT = ROOT / "docs/current-state/evidence-posend-design-freeze-001"
FEATURE_HASH = "da810777ea18ff74ebcdb9b3003dd8a0b4a5b88f68cd79b0c27b569c18340297"
PROGRAMME = "VEDA-EVIDENCE-POSEND-DESIGN-FREEZE-001"
PROTOCOL_ID = "POSEND_FORMAL_ROLE_END_PROTOCOL"
PROTOCOL_VERSION = "v1"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


def write_json(name: str, value: Any) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def write_md(name: str, value: str) -> None:
    (OUT / name).write_text(value.rstrip() + "\n", encoding="utf-8")


def dt(value: str) -> date:
    return date.fromisoformat(value)


def feature_metadata(registry: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for c in registry["contracts"]:
        result.append({
            "feature_id": c["feature_id"],
            "name": c["name"],
            "version": c["version"],
            "hash": c["hash"],
            "tier": c["tier"],
            "timing_level": c["timing_level"],
            "required_inputs": c["required_inputs"],
            "source_ids": c["source_ids"],
            "source_status": c["source_status"],
            "source_lineage": c["source_lineage"],
            "temporal_semantics": "date-indexed period interval metadata only; activation is not read",
        })
    assert len(result) == 5
    return result


def validate_r1(r1: dict[str, Any], registry: dict[str, Any]) -> dict[str, str]:
    assert r1["birth_frame"]["subject_count"] == 114
    assert r1["birth_frame"]["tier_distribution"] == {"A": 37, "B": 77}
    assert len(r1["events"]) == 4
    assert len(r1["control_design"]["controls"]) == 8
    assert r1["split"]["validation_subjects"] == ["ADB-51916", "ADB-53387", "ADB-53441"]
    assert r1["split"]["holdout_subjects"] == ["ADB-53866"]
    assert r1["split"]["feature_results_inspected"] is False
    assert r1["astrology_blind"] is True and r1["feature_blind"] is True
    assert registry["feature_family_hash"] == FEATURE_HASH
    return {
        "subject_hash": r1["new_cohort"]["subject_hash"],
        "event_hash": r1["new_cohort"]["event_hash"],
        "control_date_hash": r1["control_design"]["control_date_hash"],
        "birth_frame_hash": r1["birth_frame"]["subject_hash"],
        "feature_family_hash": FEATURE_HASH,
        "validation_hash": r1["split"]["validation_subject_hash"],
        "holdout_hash": r1["split"]["holdout_subject_hash"],
        "acquisition_policy_hash": r1["birth_frame"]["selection_policy_hash"],
    }


def validate_controls(r1: dict[str, Any], exclusion: int = 14, separation: int = 14) -> dict[str, Any]:
    roles = {r["event_id"]: r for r in r1["role_intervals"]}
    by_event: dict[str, list[date]] = {}
    invalid = []
    for c in r1["control_design"]["controls"]:
        role = roles[c["event_id"]]
        value = dt(c["control_date"])
        if not (dt(role["role_start"]) < value < dt(role["role_end"])):
            invalid.append(c["control_id"] + ":outside_role")
        if (dt(role["role_end"]) - value).days < exclusion:
            invalid.append(c["control_id"] + ":pre_event_exclusion")
        if c["post_event"]:
            invalid.append(c["control_id"] + ":post_event")
        by_event.setdefault(c["event_id"], []).append(value)
    for event_id, values in by_event.items():
        for left, right in zip(sorted(values), sorted(values)[1:]):
            if (right - left).days < separation:
                invalid.append(event_id + ":control_separation")
    return {
        "r1_controls": 8,
        "r1_controls_per_event": 2,
        "pre_event_exclusion_days": exclusion,
        "minimum_separation_days": separation,
        "all_valid_under_protocol": not invalid,
        "invalid_controls": invalid,
    }


def case_prevalence(control_prevalence: float, odds_ratio: float) -> float:
    odds = odds_ratio * control_prevalence / (1 - control_prevalence)
    return odds / (1 + odds)


def matched_scenario(k: int, baseline: float, odds_ratio: float, rho: float) -> dict[str, Any]:
    target = case_prevalence(baseline, odds_ratio)
    allocation = 1.0 / k
    pbar = (baseline + allocation * target) / (1 + allocation)
    alpha = 0.01
    z_alpha = NormalDist().inv_cdf(1 - alpha / 2)
    z_beta = NormalDist().inv_cdf(0.80)
    delta = abs(target - baseline)
    design_effect = 1 + (k - 1) * rho
    control_n = math.ceil((((z_alpha * math.sqrt((1 + 1 / allocation) * pbar * (1 - pbar))) +
                            (z_beta * math.sqrt(baseline * (1 - baseline) +
                                                target * (1 - target) / allocation))) / delta) ** 2 * design_effect)
    event_n = math.ceil(control_n * allocation)
    return {
        "controls_per_event": k,
        "baseline_control_prevalence": baseline,
        "mesi_odds_ratio": odds_ratio,
        "target_case_prevalence": round(target, 8),
        "within_subject_correlation": rho,
        "design_effect": round(design_effect, 8),
        "alpha": alpha,
        "target_power": 0.80,
        "approximate_control_observations": control_n,
        "approximate_independent_event_subjects": event_n,
        "recruitment_target_after_exclusions": math.ceil(event_n / 0.85),
        "method": "MATCHED_RISK_SET_NORMAL_APPROXIMATION_SCENARIO_ONLY",
        "limitation": "No R1 feature values were used; exact conditional-risk-set power requires frozen nuisance parameters.",
    }


def synthetic_smoke(scenarios: list[dict[str, Any]]) -> dict[str, Any]:
    rng = random.Random(20260819)
    results = []
    for scenario in scenarios[:3]:
        n = min(max(scenario["approximate_independent_event_subjects"], 100), 400)
        diffs = []
        for _ in range(120):
            total = 0.0
            for _ in range(n):
                case = int(rng.random() < scenario["target_case_prevalence"])
                controls = sum(int(rng.random() < scenario["baseline_control_prevalence"])
                               for _ in range(scenario["controls_per_event"]))
                total += case - controls / scenario["controls_per_event"]
            diffs.append(total / n)
        results.append({
            "controls_per_event": scenario["controls_per_event"],
            "mesi_odds_ratio": scenario["mesi_odds_ratio"],
            "synthetic_event_subjects": n,
            "replicates": 120,
            "mean_case_minus_control_contrast": round(sum(diffs) / len(diffs), 8),
        })
    return {
        "status": "PASS",
        "seed": 20260819,
        "purpose": "synthetic binary-state plumbing smoke test only; not feature validation or a power claim",
        "real_r1_subject_ids_used": False,
        "real_r1_feature_values_used": False,
        "astrology_used": False,
        "results": results,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    r1 = read_json(R1_PATH)
    registry = read_json(FEATURE_PATH)
    legacy = read_json(LEGACY_PATH)
    hashes = validate_r1(r1, registry)
    control_validation = validate_controls(r1)
    assert control_validation["all_valid_under_protocol"]

    event_definition = {
        "event_id": "FORMAL_PUBLIC_ROLE_END_EFFECTIVE_DATE",
        "family": "FORMAL_PUBLIC_ROLE_END",
        "definition": "Exact calendar date on which an identifiable substantive public or institutional role effectively ends while active immediately before the date.",
        "required": ["formal role", "DAY start", "DAY effective end", "official or strong institutional source", "effective-end semantics"],
        "included_subtypes": ["TERM_COMPLETION", "EFFECTIVE_RESIGNATION", "EFFECTIVE_REMOVAL", "EFFECTIVE_RETIREMENT"],
        "excluded_primary_subtypes": ["GENERIC_CAREER_END", "ANNOUNCEMENT_ONLY", "DEATH_ENDPOINT", "UNRESOLVED_ROLE_CONFLICT"],
        "mortality_policy": "ROLE_END_BY_DEATH_EXCLUDED",
    }
    eligibility = {
        "birth_frame": "PRE_EXISTING_GOVERNED_BIRTH_FRAME_ONLY",
        "event_search_direction": "BIRTH_FRAME_TO_OBJECTIVE_EVENT",
        "birth_evidence": ["Tier A", "Tier B"],
        "event_evidence": ["primary official", "strong institutional"],
        "date_precision": "DAY for role start and role end",
        "role_active_before_event": True,
        "mortality_policy": "ROLE_END_BY_DEATH_EXCLUDED",
        "one_primary_event_per_subject": True,
        "selection": "chronologically first eligible event after frame freeze; event_id tie-break only",
        "pre_screen": "pre-existing public-role metadata may prioritize search only if frozen before event lookup",
        "feature_values_used": False,
        "astrology_used": False,
    }
    controls = {
        "primary_design": "WITHIN_SUBJECT_PRE_EVENT_RISK_SET_MATCHED_CASE_CROSSOVER",
        "unit_of_analysis": "EVENT_CONTROL_SET; independent N is event-subject",
        "future_controls_per_event": 4,
        "r1_historical_controls_per_event": 2,
        "risk_interval": "[role_start, role_end - 14 days]",
        "pre_event_exclusion_days": 14,
        "minimum_control_separation_days": 14,
        "placement": "deterministic interior quantiles; no feature-result tuning",
        "weekday_matching": "NO in primary design",
        "calendar_month_season_matching": "NO in primary design",
        "tenure_matching": "same formal-role interval; relative tenure descriptive only",
        "age_matching": "within-subject identity controls age; no separate age match",
        "competing_event_policy": "exclude controls near another eligible role end or unresolved role conflict",
        "date_quality": "DAY precision",
        "r1_validation": control_validation,
    }
    multiplicity = {
        "family": "five frozen POSITION_END features",
        "primary_method": "HOLM_FAMILYWISE_ERROR_CONTROL",
        "alpha": 0.05,
        "secondary_method": "MAXIMUM_STATISTIC_PERMUTATION_ONLY_IF_EXCHANGEABILITY_JUSTIFIED",
        "exploratory_fdr": "not confirmatory",
        "correction_executed": False,
    }
    effect_mesi = {
        "primary_effect_measure": "feature-specific conditional matched odds ratio; family-level inference over the five-test vector",
        "raw_independent_proportion_difference": "PROHIBITED",
        "mesi": {"low": {"odds_ratio": 1.5}, "medium": {"odds_ratio": 2.0}, "high": {"odds_ratio": 3.0}},
        "mesi_basis": "scientific/practical scenarios, never estimated from the pilot",
        "directional_test": False,
        "target_power": 0.80,
    }
    split = {
        "design_set": "software and control mechanics only; no feature selection",
        "validation": "pre-specified descriptive/development checks after acquisition freeze",
        "holdout": "subject-level, protected, unopened for association, thresholds or control tuning",
        "small_n": "HOLDOUT_UNDERPOWERED if meaningful protection cannot be supported",
    }
    acquisition = {
        "frame": "pre-existing governed birth frame then objective event search",
        "source_diversity": "single birth-source cluster cannot support confirmatory inference",
        "next_programme": "VEDA-EVIDENCE-POSEND-ACQ-R2",
    }
    protocol = {
        "protocol_id": PROTOCOL_ID,
        "protocol_version": PROTOCOL_VERSION,
        "event_definition": event_definition,
        "eligibility": eligibility,
        "controls": controls,
        "estimand": {
            "notation": "Delta_j = E[Z_ij(T_i) - (1/K) sum_k Z_ij(C_ik)]",
            "null": "no pre-specified family enrichment at effective role-end dates versus matched risk-set dates",
            "alternative": "at least one frozen family member is enriched under the matched design",
            "case_date": "exact effective role-end date",
            "control_dates": "K dates from the same subject's active-role risk interval",
            "independence": "event-subjects are independent; controls are nested",
        },
        "feature_family": {"id": registry["feature_family_id"], "version": registry["feature_family_version"], "hash": FEATURE_HASH, "count": 5},
        "multiplicity": multiplicity,
        "effect_mesi": effect_mesi,
        "split": split,
        "acquisition": acquisition,
    }
    protocol_hash = sha(protocol)

    scenarios = []
    for baseline in (0.10, 0.25, 0.50):
        for odds_ratio in (1.5, 2.0, 3.0):
            for k in (2, 4, 8):
                scenarios.append(matched_scenario(k, baseline, odds_ratio, 0.25))
    power = {
        "model": "matched within-subject risk-set planning approximation",
        "primary_controls_per_event": 4,
        "primary_baseline_prevalence": 0.25,
        "primary_correlation": 0.25,
        "alpha": 0.01,
        "alpha_reason": "conservative per-feature sensitivity for five-family Holm planning",
        "target_power": 0.80,
        "scenarios": scenarios,
        "correlation_sensitivity": [matched_scenario(4, 0.25, 2.0, rho) for rho in (0.0, 0.25, 0.50)],
        "r1_event_subjects": 4,
        "r1_powered": False,
        "r1_suitable_for_effect_estimation": False,
        "r1_feature_values_used": False,
    }
    synthetic = synthetic_smoke(scenarios)
    pilot = {
        "pilot_role": "DESIGN_FEASIBILITY_PILOT",
        "subjects": 4,
        "events": 4,
        "validation": 3,
        "holdout": 1,
        "birth_source_clusters": 1,
        "event_source_clusters": 3,
        "hashes": hashes,
        "feature_values_inspected": False,
        "holdout_opened": False,
        "legacy_20_subject_year_cohort_combined": False,
    }
    diversity = {
        "r1_birth_clusters": 1,
        "r1_event_clusters": 3,
        "confirmatory_single_birth_cluster_allowed": False,
        "future_confirmatory_gate": {
            "minimum_independent_birth_source_clusters": 2,
            "minimum_event_source_clusters": 2,
            "report_country_era_role_type_birth_tier_event_tier_and_upstream_cluster": True,
        },
        "conservative_bound": 1,
        "formal_adb_access": "HIGH_VALUE_FOR_SCALE",
        "formal_adb_request_submitted": False,
    }
    r2 = {
        "programme_id": "VEDA-EVIDENCE-POSEND-ACQ-R2",
        "status": "NOT_STARTED",
        "eligible_birth_frame": "latest governed verified A/B frame; expansion requires separate source-governance authorization",
        "candidate_order": "deterministic frame order with full denominator retained",
        "pre_screen": "only pre-existing occupation/public-role metadata; no outcome or astrology filtering",
        "event_ontology": "FORMAL_PUBLIC_ROLE_END with non-mortality primary lane and separate subtypes",
        "source_hierarchy": ["primary official", "strong institutional documentary", "discovery-only excluded"],
        "day_requirement": "DAY start and effective DAY end",
        "role_interval": "complete active-role interval with 14-day exclusion and 14-day separation",
        "source_dependence": "birth/event upstream cluster, country, role family and era",
        "stop_rule": "STOP_UNTIL_NEW_DATA_SOURCE when confirmatory diversity or exact-day matched N cannot be achieved",
        "formal_access": "HIGH_VALUE_FOR_SCALE; not submitted",
        "scoring_authorized": False,
    }
    stop_rules = {
        "stop_until_new_data_source": ["single birth-source cluster", "unattainable matched N", "incoherent effective-end ontology", "invalid role intervals", "unavailable scale access without an independent frame"],
        "never_authorized": ["feature scoring", "astrology calculation", "prediction", "ML", "production"],
    }
    manifest = {
        "programme": PROGRAMME,
        "status": "PASS_WITH_CONDITION",
        "decision": "POSEND_DESIGN_FROZEN_FORMAL_ACCESS_HIGH_VALUE",
        "next_programme_id": "VEDA-EVIDENCE-POSEND-ACQ-R2",
        "next_programme_started": False,
        "pilot": pilot,
        "protocol_hash": protocol_hash,
        "event_definition": event_definition,
        "control_policy": controls,
        "feature_family": {"count": 5, "version": "1.0.0", "hash": FEATURE_HASH, "activation_accessed": False},
        "multiplicity": multiplicity,
        "effect_mesi": effect_mesi,
        "power": power,
        "synthetic_power_simulation": synthetic,
        "source_diversity": diversity,
        "r2_protocol": r2,
        "stop_rules": stop_rules,
        "legacy": {"path": str(LEGACY_PATH.relative_to(ROOT)), "preserved": True, "combined_with_r1": False},
        "safety": {"astrology": "NO", "feature_scoring": "NO", "outcome_association": "NO", "ml": "LOCKED", "pred_m4": "UNCHANGED / INSUFFICIENT_SAMPLE", "production": "UNCHANGED", "rag": "UNCHANGED", "subject_data_added_to_rag": False, "raw_provider_data_committed": False},
    }

    write_json("01_R1_PILOT_FREEZE.json", pilot)
    write_md("02_PRIMARY_EVENT_DEFINITION.md", "The primary event is FORMAL_PUBLIC_ROLE_END_EFFECTIVE_DATE: an exact DAY on which an identifiable substantive public or institutional role effectively ends while active immediately before the date. Both boundaries require official or strong institutional evidence. Announcement-only, generic career-end, death and unresolved-conflict records are excluded from the primary lane.")
    write_json("03_ELIGIBILITY_CONTRACT.json", eligibility)
    write_md("04_RISK_SET_AND_CONTROL_POLICY.md", "The primary design is a within-subject pre-event risk-set matched case-crossover. The independent unit is the event-subject; controls are nested dates. Future R2 uses four deterministic interior-quantile controls per event, a 14-day pre-event exclusion, and 14-day minimum separation. Weekday, month and season matching are not applied. Same-role tenure and subject identity provide the within-person frame. The eight R1 controls remain historical and pass the frozen policy.")
    write_md("05_PRIMARY_ESTIMAND.md", "For subject/event i and feature j, Delta_j = E[Z_ij(T_i) - (1/K) sum_k Z_ij(C_ik)]. T is the exact effective role-end date and C are matched active-role risk-set dates. The primary null is no enrichment for the five-feature family. Feature-specific conditional matched odds ratios are the effect measures; subjects/events, not case plus controls, define independent N. No Z values are calculated here.")
    write_json("06_FEATURE_FAMILY_FREEZE.json", {"feature_family_id": registry["feature_family_id"], "feature_family_version": registry["feature_family_version"], "feature_family_hash": FEATURE_HASH, "feature_count": 5, "contracts": feature_metadata(registry), "changed": 0, "activation_accessed": False})
    write_md("07_MULTIPLICITY_POLICY.md", "The five features are one family. Confirmatory family-wise error is controlled at alpha 0.05 with Holm adjustment. All five hypotheses are fixed before scoring. Maximum-statistic permutation is secondary and conditional on justified exchangeability; FDR is exploratory only. No correction is executed here.")
    write_md("08_EFFECT_AND_MESI_POLICY.md", "Primary effect: feature-specific conditional matched odds ratio. Raw independent-proportion differences are prohibited. MESI scenarios are fixed before scoring: LOW OR 1.5, MEDIUM OR 2.0, HIGH OR 3.0. These are practical planning scenarios, not pilot estimates; testing is non-directional.")
    write_json("09_MATCHED_POWER_MODEL.json", power)
    write_md("10_SOURCE_DIVERSITY_GATE.md", "All four R1 event subjects share one upstream birth-source cluster, so R1 is design-feasibility only. Confirmatory inference may not rely on one birth cluster. Future reports must include birth/event clusters, country, era, role type, birth tier and event tier. The future gate requires at least two independent birth clusters and two event clusters. Formal ADB access is HIGH_VALUE_FOR_SCALE and remains unsubmitted.")
    write_md("11_PROSPECTIVE_SPLIT_POLICY.md", "The R1 3/1 split protects process only and is not meaningful replication. R2 must freeze the full denominator before partitions. A design set may test software/control mechanics only. Holdout is subject-level, protected and unopened for association, thresholds, control tuning or feature selection. If future N cannot support meaningful protection, return HOLDOUT_UNDERPOWERED.")
    write_md("12_ACQUISITION_R2_PROTOCOL.md", "VEDA-EVIDENCE-POSEND-ACQ-R2 remains NOT_STARTED. Use the governed A/B birth frame, retain the denominator, search from frame to objective events, require DAY start/end and official/institutional evidence, prefer non-mortality, and track upstream source clusters. A pre-existing public-role metadata filter may prioritize search only if frozen before event lookup. Formal ADB access is HIGH_VALUE_FOR_SCALE and was not submitted. No scoring is authorized.")
    write_md("13_PREREGISTRATION.md", "Protocol POSEND_FORMAL_ROLE_END_PROTOCOL v1 specifies a five-feature POSITION_END family, exact effective role-end cases, four within-subject pre-event controls, conditional matched odds ratios, Holm alpha 0.05, MESI OR 1.5/2.0/3.0, DAY role boundaries, non-mortality primary events, and protected subject-level holdout. It prohibits astrology, feature activation, outcome association, prediction, ML, production and holdout opening. The R1 pilot cannot estimate prevalence, correlation, effect size or variance. Any material change requires a new protocol version.")
    write_json("14_PROTOCOL_HASH.json", {"protocol_id": PROTOCOL_ID, "protocol_version": PROTOCOL_VERSION, "protocol_hash": protocol_hash, "hash_inputs": ["event_definition", "eligibility", "controls", "feature_family", "multiplicity", "effect_mesi", "split", "acquisition"]})
    write_md("15_STOP_RULES.md", "Return STOP_UNTIL_NEW_DATA_SOURCE when confirmatory diversity cannot be achieved, matched N is unattainable, effective-end ontology is incoherent, role intervals are invalid, or scale requires unavailable access without an independent frame. Feature-blind adjudication and protocol checks may continue. Feature scoring, astrology, prediction, ML and production are never authorized by this activity.")
    write_md("16_FINAL_ACCEPTANCE.md", "PASS: R1 hashes, legacy, holdout, event/eligibility, controls, feature family, multiplicity, MESI, split, source gate, R2 status, safety and deterministic artifacts. PASS_WITH_CONDITION: R1 is not powered or suitable for effect estimation; one birth cluster blocks confirmatory inference; formal ADB access is high-value. BLOCKED: none. FAIL: none.")
    write_json("17_SYNTHETIC_POWER_SIMULATION.json", synthetic)
    write_json("FINAL_MANIFEST.json", manifest)
    print(json.dumps({"programme": PROGRAMME, "status": manifest["status"], "decision": manifest["decision"], "protocol_hash": protocol_hash, "r1_controls_valid": control_validation["all_valid_under_protocol"], "scoring": "NO", "astrology": "NO"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
