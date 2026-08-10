from __future__ import annotations

from typing import Any, Mapping


_KUNDLI_INTERPRETATION_LABELS = {
    "STRONG_BUY": "Strong positive astrology heuristic",
    "BUY": "Positive astrology heuristic",
    "HOLD": "Mixed astrology heuristic",
    "CAUTION": "Cautionary astrology heuristic",
    "EXIT": "Negative astrology heuristic",
    "AVOID": "High-risk astrology heuristic",
}

_KUNDLI_CHART_LABELS = {
    "BUY": "Positive natal astrology signal",
    "HOLD": "Mixed natal astrology signal",
    "CAUTION": "Cautionary natal astrology signal",
    "EXIT": "Negative natal astrology signal",
    "AVOID": "High-risk natal astrology signal",
    "MODERATE": "Moderately positive natal astrology signal",
    "NEUTRAL": "Neutral natal astrology signal",
}

_ASTROFINANCE_LABELS = {
    "BUY": "Positive AstroFinance heuristic",
    "HOLD": "Mixed AstroFinance heuristic",
    "CAUTION": "Cautionary AstroFinance heuristic",
    "EXIT": "Negative AstroFinance heuristic",
    "AVOID": "High-risk AstroFinance heuristic",
}

_KUNDLI_BOUNDARY = (
    "Astrology-derived market heuristic only; not validated financial advice."
)
_ASTROFINANCE_BOUNDARY = (
    "AstroFinance heuristic only; cross-check with market, technical, and fundamental evidence."
)
_LONGEVITY_BOUNDARY = (
    "Traditional Jyotisha interpretation only; not a factual lifespan or death prediction."
)


def longevity_boundary_note() -> str:
    return _LONGEVITY_BOUNDARY


def _with_common_metadata(
    payload: dict[str, Any],
    *,
    evidence_class: str,
    source_status: str,
    interpretation_type: str,
    output_classification: str,
    boundary_note: str,
) -> dict[str, Any]:
    payload["evidence_class"] = evidence_class
    payload["source_status"] = source_status
    payload["interpretation_type"] = interpretation_type
    payload["high_stakes"] = True
    payload["actionability"] = "NON_ACTIONABLE_HEURISTIC"
    payload["output_classification"] = output_classification
    payload["boundary_note"] = boundary_note
    return payload


def present_kundli_interpretation(payload: Mapping[str, Any]) -> dict[str, Any]:
    raw_code = str(payload.get("signal", "HOLD") or "HOLD")
    label = _KUNDLI_INTERPRETATION_LABELS.get(raw_code, "Astrology heuristic")
    safe_payload = dict(payload)
    safe_payload["signal_code"] = raw_code
    safe_payload["signal"] = label
    safe_payload["signal_label"] = label
    return _with_common_metadata(
        safe_payload,
        evidence_class="ASTROLOGY_HEURISTIC",
        source_status="LEGACY_UNSOURCED",
        interpretation_type="STOCK_ASTROLOGY_HEURISTIC",
        output_classification="ASTROLOGY_HEURISTIC",
        boundary_note=_KUNDLI_BOUNDARY,
    )


def present_kundli_chart(chart: Mapping[str, Any]) -> dict[str, Any]:
    safe_chart = dict(chart)
    raw_code = str(chart.get("astro_action", "") or "")
    if raw_code:
        label = _KUNDLI_CHART_LABELS.get(raw_code, "Astrology-derived natal signal")
        safe_chart["astro_action_code"] = raw_code
        safe_chart["astro_action"] = label
        safe_chart["astro_action_label"] = label
        _with_common_metadata(
            safe_chart,
            evidence_class="ASTROLOGY_HEURISTIC",
            source_status="LEGACY_UNSOURCED",
            interpretation_type="STOCK_ASTROLOGY_HEURISTIC",
            output_classification="ASTROLOGY_HEURISTIC",
            boundary_note=_KUNDLI_BOUNDARY,
        )
    return safe_chart


def _astrofinance_reason(payload: Mapping[str, Any]) -> str:
    sector = str(payload.get("sector", "this sector") or "this sector")
    primary_planet = str(payload.get("primary_planet", "The ruling planet") or "The ruling planet")
    planet_sign = str(payload.get("planet_sign", "its current sign") or "its current sign")
    planet_state = str(payload.get("planet_state", "") or "")
    retrograde = bool(payload.get("planet_retrograde", False))
    eclipse_active = bool(payload.get("eclipse_active", False))
    astro_score = float(payload.get("astro_score", 0) or 0)

    if eclipse_active:
        return (
            f"AstroFinance marks {sector} as a higher-volatility heuristic regime during the current eclipse window. "
            "Treat this as an internal astrology-based caution signal rather than a trading instruction."
        )
    if retrograde and primary_planet not in {"Rahu", "Ketu"}:
        return (
            f"{primary_planet}, the AstroFinance model's ruling planet for {sector}, is retrograde in {planet_sign}. "
            "The model treats that as a weakening factor for short-term sector momentum, not as validated investment advice."
        )
    if planet_state == "DEBILITATED":
        return (
            f"{primary_planet} is in a weak sign state for the AstroFinance model, which currently lowers the heuristic outlook for {sector}. "
            "This is a non-classical experimental signal that should be cross-checked against market evidence."
        )
    if astro_score >= 25:
        return (
            f"The AstroFinance model reads {primary_planet} in {planet_sign} as a supportive backdrop for {sector}. "
            "Use this as a bounded heuristic signal alongside price, flow, and fundamental analysis."
        )
    if astro_score >= -15:
        return (
            f"The AstroFinance model finds mixed planetary conditions around {sector}, with no strong directional conclusion. "
            "Interpret the signal as a heuristic context layer rather than a direct market action."
        )
    if astro_score >= -35:
        return (
            f"The AstroFinance model reads challenging planetary conditions for {sector} today. "
            "This is a cautionary heuristic signal, not a validated instruction to trade or exit."
        )
    return (
        f"The AstroFinance model flags pronounced planetary stress around {sector} in its current heuristic framework. "
        "Treat the signal as experimental and non-actionable without independent market confirmation."
    )


def present_astrofinance_signal(payload: Mapping[str, Any]) -> dict[str, Any]:
    raw_code = str(payload.get("astro_action", "HOLD") or "HOLD")
    label = _ASTROFINANCE_LABELS.get(raw_code, "AstroFinance heuristic")
    safe_payload = dict(payload)
    safe_payload["astro_action_code"] = raw_code
    safe_payload["astro_action"] = label
    safe_payload["astro_action_label"] = label
    safe_payload["astro_reason"] = _astrofinance_reason(payload)
    return _with_common_metadata(
        safe_payload,
        evidence_class="INTERNAL_HEURISTIC",
        source_status="UNVERIFIED",
        interpretation_type="ASTROFINANCE_HEURISTIC",
        output_classification="ASTROLOGY_HEURISTIC",
        boundary_note=_ASTROFINANCE_BOUNDARY,
    )
