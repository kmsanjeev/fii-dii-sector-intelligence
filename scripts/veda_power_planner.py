"""Research-only power and sample-size planning for VEDA empirical work.

This module plans independent evidence requirements; it does not score charts,
select cases, or alter production prediction behaviour.  The two-proportion
calculation is an approximation for planning sensitivity, not a replacement
for the preregistered case-crossover analysis.
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Any


Z_90 = 1.2815515655446004
Z_95 = 1.959963984540054
Z_975 = 2.241402727604947
Z_99 = 2.5758293035489004


def _z_for_alpha(alpha: float) -> float:
    if alpha <= 0 or alpha >= 1:
        raise ValueError("alpha must be between 0 and 1")
    # Fixed standard-normal quantiles keep this small planner dependency-free.
    table = {0.10: Z_90, 0.05: Z_95, 0.025: Z_975, 0.01: Z_99}
    return table.get(round(alpha, 6), Z_95)


def two_proportion_required(
    baseline_rate: float,
    target_rate: float,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
    allocation_ratio: float = 1.0,
    design_effect: float = 1.0,
    exclusion_fraction: float = 0.0,
) -> dict[str, Any]:
    """Return an auditable approximate independent-subject requirement."""
    if not 0 < baseline_rate < 1 or not 0 < target_rate < 1:
        raise ValueError("rates must be between 0 and 1")
    if not 0 < power < 1 or allocation_ratio <= 0 or design_effect < 1:
        raise ValueError("invalid power, allocation ratio, or design effect")
    if not 0 <= exclusion_fraction < 1:
        raise ValueError("exclusion_fraction must be in [0, 1)")
    delta = abs(target_rate - baseline_rate)
    if delta == 0:
        raise ValueError("target_rate must differ from baseline_rate")
    pbar = (baseline_rate + allocation_ratio * target_rate) / (1 + allocation_ratio)
    z_alpha = _z_for_alpha(alpha / 2)
    # Approximate inverse-normal quantiles for common planning powers.
    z_beta = {0.80: Z_95, 0.90: Z_975, 0.95: Z_99}.get(round(power, 2), Z_95)
    n_control = ((z_alpha * math.sqrt((1 + 1 / allocation_ratio) * pbar * (1 - pbar)) +
                  z_beta * math.sqrt(baseline_rate * (1 - baseline_rate) +
                                      target_rate * (1 - target_rate) / allocation_ratio)) / delta) ** 2
    n_control = math.ceil(n_control * design_effect)
    n_exposed = math.ceil(n_control * allocation_ratio)
    total_analytic = n_control + n_exposed
    total_recruit = math.ceil(total_analytic / (1 - exclusion_fraction))
    return {
        "baseline_rate": baseline_rate,
        "target_rate": target_rate,
        "absolute_effect": delta,
        "alpha": alpha,
        "power": power,
        "allocation_ratio": allocation_ratio,
        "design_effect": design_effect,
        "exclusion_fraction": exclusion_fraction,
        "approximate_control_subjects": n_control,
        "approximate_exposed_subjects": n_exposed,
        "approximate_independent_subjects": total_analytic,
        "recruitment_target_after_exclusions": total_recruit,
        "method": "TWO_PROPORTION_NORMAL_APPROXIMATION_RESEARCH_ONLY",
        "limitation": "Not a case-crossover power guarantee; exact conditional/permutation planning remains required.",
    }


def build_plan() -> dict[str, Any]:
    scenarios = []
    for baseline in (0.10, 0.20, 0.30):
        for absolute_delta in (0.05, 0.10, 0.15, 0.20):
            target = min(0.99, baseline + absolute_delta)
            scenarios.append(two_proportion_required(baseline, target, design_effect=1.10, exclusion_fraction=0.15))
    return {
        "activity_id": "VEDA-EVIDENCE-REBASELINE-001",
        "status": "RESEARCH_ONLY",
        "alpha_policy": {"confirmatory": 0.05, "holm": True, "maximum_statistic_permutation": True, "fdr": "EXPLORATORY_ONLY"},
        "scenarios": scenarios,
        "case_crossover_note": "Power must be re-estimated after event prevalence, control efficiency, clustering and date precision are frozen.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str)
    args = parser.parse_args()
    result = build_plan()
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        from pathlib import Path
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
