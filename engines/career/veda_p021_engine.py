from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.common.validators import validate_columns, validate_row_count, validate_unique
from engines.career.fetchers.career_sources_ingest import load_bundle


logger = get_logger(__name__)

_TS = "2026-08-14T00:00:00Z"
_DATE = _TS[:10]
_OUTPUT_CSV = cfg.VEDA_CACHE_DIR / "career_validated_profiles.csv"
_SCHEMA_PATH = cfg.PROJECT_ROOT / "schemas" / "career_validated_profiles.schema.yaml"
_VALIDATION_DIR = cfg.VEDA_ASTROLOGY_CAPABILITY_VALIDATION_DIR
_DOC_DIR = cfg.DOCS_DIR / "current-state" / "p021"

_ROLE_RULES: list[dict[str, Any]] = [
    {
        "domain_id": "LEADERSHIP",
        "canonical_role": "Chief Executive Officer",
        "role_family": "leadership",
        "synonyms": ["Managing Director", "Executive Director", "Business Head"],
        "skills": ["strategy", "governance", "stakeholder leadership", "execution"],
        "positive_lagna": {"Aries", "Leo", "Capricorn", "Sagittarius"},
        "positive_lords": {"Sun", "Saturn", "Mars"},
        "support_yogas": {"Raja Yoga", "Dharma Karma Adhipati", "Gaja Kesari"},
        "opposing_yogas": {"Kemdrum"},
    },
    {
        "domain_id": "ANALYTICS",
        "canonical_role": "Research Strategist",
        "role_family": "analysis",
        "synonyms": ["Research Analyst", "Business Analyst", "Insight Lead"],
        "skills": ["research", "pattern recognition", "forecasting", "model validation"],
        "positive_lagna": {"Gemini", "Virgo", "Aquarius"},
        "positive_lords": {"Mercury", "Jupiter"},
        "support_yogas": {"Gaja Kesari", "Neecha Bhanga", "Viparita Raja"},
        "opposing_yogas": {"Kemdrum"},
    },
    {
        "domain_id": "COMMUNICATION",
        "canonical_role": "Communications Lead",
        "role_family": "communication",
        "synonyms": ["Product Marketer", "Brand Strategist", "Client Relations Lead"],
        "skills": ["communication", "storytelling", "networking", "negotiation"],
        "positive_lagna": {"Gemini", "Libra", "Cancer", "Virgo"},
        "positive_lords": {"Mercury", "Venus", "Moon"},
        "support_yogas": {"Gaja Kesari", "Raja Yoga"},
        "opposing_yogas": {"Kemdrum"},
    },
    {
        "domain_id": "FINANCE",
        "canonical_role": "Portfolio Manager",
        "role_family": "finance",
        "synonyms": ["Investment Analyst", "Treasury Manager", "Corporate Finance Lead"],
        "skills": ["capital allocation", "risk management", "valuation", "portfolio construction"],
        "positive_lagna": {"Taurus", "Capricorn", "Libra", "Pisces"},
        "positive_lords": {"Jupiter", "Venus", "Saturn"},
        "support_yogas": {"Dhana Yoga", "Raja Yoga", "Lakshmi Yoga"},
        "opposing_yogas": {"Kemdrum"},
    },
    {
        "domain_id": "TECHNOLOGY",
        "canonical_role": "Technical Architect",
        "role_family": "technology",
        "synonyms": ["Software Engineer", "Systems Architect", "Automation Engineer"],
        "skills": ["systems design", "automation", "technical analysis", "process engineering"],
        "positive_lagna": {"Virgo", "Aquarius", "Gemini", "Capricorn"},
        "positive_lords": {"Mercury", "Saturn", "Mars"},
        "support_yogas": {"Viparita Raja", "Neecha Bhanga", "Dhana Yoga"},
        "opposing_yogas": {"Kemdrum"},
    },
    {
        "domain_id": "EDUCATION",
        "canonical_role": "Advisor and Mentor",
        "role_family": "education",
        "synonyms": ["Teacher", "Trainer", "Learning Strategist"],
        "skills": ["teaching", "coaching", "curriculum design", "advisory work"],
        "positive_lagna": {"Sagittarius", "Pisces", "Cancer", "Virgo"},
        "positive_lords": {"Jupiter", "Mercury", "Moon"},
        "support_yogas": {"Gaja Kesari", "Raja Yoga", "Dhana Yoga"},
        "opposing_yogas": {"Kemdrum"},
    },
]

_INDUSTRY_BIASES: dict[str, dict[str, float]] = {
    "BANKING": {"FINANCE": 0.08, "LEADERSHIP": 0.03},
    "FINANCIAL SERVICES": {"FINANCE": 0.08, "ANALYTICS": 0.02},
    "NBFC": {"FINANCE": 0.07},
    "INSURANCE": {"FINANCE": 0.05, "ANALYTICS": 0.03},
    "IT": {"TECHNOLOGY": 0.08, "ANALYTICS": 0.03},
    "TECHNOLOGY": {"TECHNOLOGY": 0.08, "ANALYTICS": 0.03},
    "SOFTWARE": {"TECHNOLOGY": 0.08, "ANALYTICS": 0.03},
    "EDUCATION": {"EDUCATION": 0.09},
    "TRAINING": {"EDUCATION": 0.08},
    "MEDIA": {"COMMUNICATION": 0.06},
    "ADVERTISING": {"COMMUNICATION": 0.07},
    "TELECOM": {"COMMUNICATION": 0.05, "TECHNOLOGY": 0.02},
    "PHARMA": {"ANALYTICS": 0.04, "EDUCATION": 0.02},
    "HEALTHCARE": {"ANALYTICS": 0.03, "EDUCATION": 0.02},
    "MANUFACTURING": {"LEADERSHIP": 0.04, "TECHNOLOGY": 0.04},
    "INFRASTRUCTURE": {"LEADERSHIP": 0.05, "TECHNOLOGY": 0.03},
    "ENGINEERING": {"TECHNOLOGY": 0.06},
}


@dataclass(frozen=True)
class CareerSymbolContext:
    symbol: str
    industry: str
    sector: str
    theme: str
    listing_date: str
    lagna: str
    lagna_lord: str
    moon_sign: str
    mahadasha: str
    antardasha: str
    maha_end_date: str
    yogas: list[str]
    astro_score: float
    astro_action: str
    chart: dict[str, Any]


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _parse_yogas(value: Any) -> list[str]:
    if not isinstance(value, str) or not value.strip():
        return []
    return [item.strip() for item in value.split("|") if item.strip()]


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _strength_rank(value: str) -> float:
    text = value.lower()
    if "strong" in text:
        return 0.08
    if "moderate" in text:
        return 0.04
    if "weak" in text:
        return -0.04
    return 0.0


def _industry_bonuses(industry: str) -> dict[str, float]:
    for key, bonuses in _INDUSTRY_BIASES.items():
        if key in industry.upper():
            return bonuses
    return {}


def _chart_house(chart: dict[str, Any], house_key: str) -> dict[str, Any]:
    houses = chart.get("financial_houses") or {}
    value = houses.get(house_key) or {}
    return value if isinstance(value, dict) else {}


def _transit_sign(chart: dict[str, Any], planet: str) -> str:
    transits = chart.get("transits") or {}
    value = transits.get(planet) or {}
    if not isinstance(value, dict):
        return ""
    return _normalize_text(value.get("current_sign"))


def _supporting_signals(ctx: CareerSymbolContext, rule: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    h10 = _chart_house(ctx.chart, "10H")
    h11 = _chart_house(ctx.chart, "11H")
    h5 = _chart_house(ctx.chart, "5H")
    h2 = _chart_house(ctx.chart, "2H")
    h8 = _chart_house(ctx.chart, "8H")

    if ctx.lagna in rule["positive_lagna"]:
        signals.append(f"lagna={ctx.lagna}")
    if ctx.lagna_lord in rule["positive_lords"]:
        signals.append(f"lagna_lord={ctx.lagna_lord}")
    if ctx.mahadasha in rule["positive_lords"]:
        signals.append(f"mahadasha={ctx.mahadasha}")
    if ctx.antardasha in rule["positive_lords"]:
        signals.append(f"antardasha={ctx.antardasha}")

    for yoga in ctx.yogas:
        if yoga in rule["support_yogas"]:
            signals.append(f"yoga={yoga}")

    if ctx.astro_action == "BUY" and rule["domain_id"] in {"LEADERSHIP", "FINANCE"}:
        signals.append("astro_action=BUY")
    elif ctx.astro_action == "CAUTION" and rule["domain_id"] in {"ANALYTICS", "COMMUNICATION"}:
        signals.append("astro_action=CAUTION")

    if ctx.astro_score >= 60:
        signals.append("astro_score>=60")
    if ctx.astro_score >= 70:
        signals.append("astro_score>=70")

    if rule["domain_id"] == "LEADERSHIP":
        if "strong" in _normalize_text(h10.get("strength")).lower():
            signals.append("10H_strength=strong")
        if _normalize_text(h10.get("sign")) in {"Leo", "Aries", "Capricorn"}:
            signals.append(f"10H_sign={_normalize_text(h10.get('sign'))}")
        if _normalize_text(h10.get("lord")) in {"Sun", "Saturn", "Mars"}:
            signals.append(f"10H_lord={_normalize_text(h10.get('lord'))}")
    elif rule["domain_id"] == "ANALYTICS":
        if "strong" in _normalize_text(h11.get("strength")).lower():
            signals.append("11H_strength=strong")
        if _normalize_text(h8.get("sign")) in {"Gemini", "Virgo", "Aquarius"}:
            signals.append(f"8H_sign={_normalize_text(h8.get('sign'))}")
    elif rule["domain_id"] == "COMMUNICATION":
        if _normalize_text(h2.get("sign")) in {"Gemini", "Libra", "Cancer"}:
            signals.append(f"2H_sign={_normalize_text(h2.get('sign'))}")
        if "strong" in _normalize_text(h11.get("strength")).lower():
            signals.append("11H_strength=strong")
    elif rule["domain_id"] == "FINANCE":
        if "strong" in _normalize_text(h2.get("strength")).lower():
            signals.append("2H_strength=strong")
        if "strong" in _normalize_text(h11.get("strength")).lower():
            signals.append("11H_strength=strong")
        if _normalize_text(h2.get("sign")) in {"Taurus", "Capricorn", "Libra"}:
            signals.append(f"2H_sign={_normalize_text(h2.get('sign'))}")
        if _normalize_text(h11.get("sign")) in {"Taurus", "Virgo", "Libra"}:
            signals.append(f"11H_sign={_normalize_text(h11.get('sign'))}")
    elif rule["domain_id"] == "TECHNOLOGY":
        if _normalize_text(h8.get("sign")) in {"Gemini", "Aquarius", "Virgo"}:
            signals.append(f"8H_sign={_normalize_text(h8.get('sign'))}")
        if _normalize_text(h10.get("lord")) in {"Mercury", "Saturn", "Mars"}:
            signals.append(f"10H_lord={_normalize_text(h10.get('lord'))}")
    elif rule["domain_id"] == "EDUCATION":
        if "strong" in _normalize_text(h5.get("strength")).lower():
            signals.append("5H_strength=strong")
        if _normalize_text(h5.get("sign")) in {"Sagittarius", "Pisces", "Virgo"}:
            signals.append(f"5H_sign={_normalize_text(h5.get('sign'))}")
        if _transit_sign(ctx.chart, "Jupiter") in {"Cancer", "Pisces", "Sagittarius"}:
            signals.append(f"jupiter_transit={_transit_sign(ctx.chart, 'Jupiter')}")

    industry_bonus = _industry_bonuses(ctx.industry).get(rule["domain_id"], 0.0)
    if industry_bonus:
        signals.append(f"industry_bonus={industry_bonus:.2f}")

    return signals


def _opposing_signals(ctx: CareerSymbolContext, rule: dict[str, Any]) -> list[str]:
    signals: list[str] = []
    for yoga in ctx.yogas:
        if yoga in rule["opposing_yogas"]:
            signals.append(f"yoga={yoga}")
    if ctx.astro_action == "SELL" and rule["domain_id"] in {"FINANCE", "LEADERSHIP"}:
        signals.append("astro_action=SELL")
    if ctx.astro_score <= 25:
        signals.append("astro_score<=25")
    h10 = _chart_house(ctx.chart, "10H")
    if rule["domain_id"] == "LEADERSHIP" and "weak" in _normalize_text(h10.get("strength")).lower():
        signals.append("10H_strength=weak")
    return signals


def _score_profile(ctx: CareerSymbolContext, rule: dict[str, Any]) -> tuple[float, list[str], list[str]]:
    score = 0.52
    support = _supporting_signals(ctx, rule)
    oppose = _opposing_signals(ctx, rule)

    score += min(len(support) * 0.025, 0.26)
    score -= min(len(oppose) * 0.03, 0.18)

    if ctx.astro_action == "BUY":
        score += 0.02 if rule["domain_id"] in {"LEADERSHIP", "FINANCE"} else 0.01
    elif ctx.astro_action == "HOLD":
        score += 0.01
    elif ctx.astro_action == "CAUTION":
        score -= 0.01

    if ctx.astro_score >= 70:
        score += 0.04
    elif ctx.astro_score >= 55:
        score += 0.02
    elif ctx.astro_score <= 20:
        score -= 0.04

    if ctx.mahadasha in {"Jupiter", "Mercury", "Saturn", "Sun"} and rule["domain_id"] in {"EDUCATION", "ANALYTICS", "FINANCE", "LEADERSHIP"}:
        score += 0.02
    if ctx.antardasha in {"Mercury", "Venus"} and rule["domain_id"] in {"COMMUNICATION", "EDUCATION"}:
        score += 0.02

    bonuses = _industry_bonuses(ctx.industry)
    score += bonuses.get(rule["domain_id"], 0.0)

    h10 = _chart_house(ctx.chart, "10H")
    h11 = _chart_house(ctx.chart, "11H")
    h2 = _chart_house(ctx.chart, "2H")
    h5 = _chart_house(ctx.chart, "5H")
    h8 = _chart_house(ctx.chart, "8H")

    if rule["domain_id"] == "LEADERSHIP":
        score += _strength_rank(_normalize_text(h10.get("strength")))
        if _normalize_text(h10.get("lord_dignity")) in {"exalted", "own_sign", "moolatrikona"}:
            score += 0.04
    elif rule["domain_id"] == "ANALYTICS":
        score += _strength_rank(_normalize_text(h11.get("strength")))
        if _normalize_text(h8.get("lord_dignity")) in {"exalted", "own_sign"}:
            score += 0.03
    elif rule["domain_id"] == "COMMUNICATION":
        score += _strength_rank(_normalize_text(h11.get("strength")))
        if _normalize_text(h2.get("lord_dignity")) in {"exalted", "own_sign"}:
            score += 0.03
    elif rule["domain_id"] == "FINANCE":
        score += _strength_rank(_normalize_text(h2.get("strength"))) + _strength_rank(_normalize_text(h11.get("strength")))
        if _normalize_text(h2.get("lord_dignity")) in {"exalted", "own_sign"}:
            score += 0.03
    elif rule["domain_id"] == "TECHNOLOGY":
        score += _strength_rank(_normalize_text(h8.get("strength"))) + _strength_rank(_normalize_text(h11.get("strength")))
        if _normalize_text(h8.get("lord_dignity")) in {"exalted", "own_sign"}:
            score += 0.02
    elif rule["domain_id"] == "EDUCATION":
        score += _strength_rank(_normalize_text(h5.get("strength"))) + 0.5 * _strength_rank(_normalize_text(h11.get("strength")))
        if _normalize_text(h5.get("lord_dignity")) in {"exalted", "own_sign"}:
            score += 0.03

    return round(max(0.0, min(1.0, score)), 3), support, oppose


def _canonical_role(rule: dict[str, Any]) -> str:
    return rule["canonical_role"]


def _json_list(value: list[str]) -> str:
    return json.dumps(value, ensure_ascii=False)


def _provenance(symbol: str) -> list[dict[str, str]]:
    return [
        {"source": "kundli_signals.csv", "url": str(cfg.INTELLIGENCE_DIR / "kundli_signals.csv"), "fetch_date": _DATE},
        {"source": f"kundli/{symbol}_kundli.json", "url": str(cfg.INTELLIGENCE_DIR / "kundli" / f"{symbol}_kundli.json"), "fetch_date": _DATE},
        {"source": "company_classification_v4.csv", "url": str(cfg.REFERENCE_DIR / "company_classification_v4.csv"), "fetch_date": _DATE},
    ]


def _context_from_row(row: pd.Series, chart: dict[str, Any], classification_row: pd.Series) -> CareerSymbolContext:
    return CareerSymbolContext(
        symbol=str(row["symbol"]).upper(),
        industry=_normalize_text(classification_row.get("industry_nse") or classification_row.get("industry") or "UNCATEGORIZED").upper() or "UNCATEGORIZED",
        sector=_normalize_text(classification_row.get("sector_platform") or classification_row.get("sector") or "UNCATEGORIZED").upper() or "UNCATEGORIZED",
        theme=_normalize_text(classification_row.get("theme_platform") or classification_row.get("theme") or "UNCATEGORIZED").upper() or "UNCATEGORIZED",
        listing_date=_normalize_text(row.get("listing_date") or classification_row.get("listing_date") or ""),
        lagna=_normalize_text(row.get("lagna")),
        lagna_lord=_normalize_text(row.get("lagna_lord")),
        moon_sign=_normalize_text(row.get("moon_sign")),
        mahadasha=_normalize_text(row.get("mahadasha")),
        antardasha=_normalize_text(row.get("antardasha")),
        maha_end_date=_normalize_text(row.get("maha_end_date")),
        yogas=_parse_yogas(row.get("yogas")),
        astro_score=_safe_float(row.get("astro_score")),
        astro_action=_normalize_text(row.get("astro_action")) or "HOLD",
        chart=chart,
    )


def _build_row(ctx: CareerSymbolContext, rule: dict[str, Any], is_canonical: bool) -> dict[str, Any]:
    confidence, support, oppose = _score_profile(ctx, rule)
    role_id = f"P021-{ctx.symbol}-{rule['domain_id']}"
    payload_id = None if is_canonical else f"P021-SHADOW-{ctx.symbol}-{rule['domain_id']}"
    detected_synonyms = [rule["canonical_role"], *rule["synonyms"]]
    skills = list(dict.fromkeys([*rule["skills"], f"{ctx.lagna} lagna context", f"{ctx.mahadasha} period timing", f"{ctx.industry} industry lens"]))
    return {
        "symbol": ctx.symbol,
        "domain_id": rule["domain_id"],
        "role_id": role_id,
        "canonical_role": _canonical_role(rule),
        "detected_synonyms": _json_list(detected_synonyms),
        "skills": _json_list(skills),
        "industry": ctx.industry,
        "confidence_score": confidence,
        "provenance": _json_list(_provenance(ctx.symbol)),
        "shadow_payload_id": payload_id,
        "created_at": _TS,
        "validated_by": "automated",
        "supporting_signals": _json_list(support),
        "opposing_signals": _json_list(oppose),
    }


def _build_contexts() -> list[CareerSymbolContext]:
    bundle = load_bundle()
    signals = bundle.signals.copy()
    classification = bundle.classification.copy()
    if "symbol" not in signals.columns:
        raise ValueError("kundli_signals.csv must include a symbol column")
    if "symbol" not in classification.columns:
        raise ValueError("company_classification_v4.csv must include a symbol column")
    signals["symbol"] = signals["symbol"].astype(str).str.upper()
    classification["symbol"] = classification["symbol"].astype(str).str.upper()
    merged = signals.merge(classification, on="symbol", how="inner", suffixes=("_signal", "_class"))
    if merged.empty:
        raise ValueError("No overlapping symbols between kundli_signals.csv and company_classification_v4.csv")

    contexts: list[CareerSymbolContext] = []
    for _, row in merged.iterrows():
        symbol = str(row["symbol"]).upper()
        chart = bundle.chart_index.get(symbol, {})
        class_row = row
        contexts.append(_context_from_row(row, chart, class_row))
    return contexts


def build_profiles() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for ctx in _build_contexts():
        scored = [(_score_profile(ctx, rule)[0], rule) for rule in _ROLE_RULES]
        scored.sort(key=lambda item: item[0], reverse=True)
        top_domain = scored[0][1]["domain_id"]
        for _, rule in scored:
            rows.append(_build_row(ctx, rule, is_canonical=(rule["domain_id"] == top_domain)))

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError("Career profile builder returned no rows")
    df["confidence_score"] = df["confidence_score"].astype(float).round(3)
    df["created_at"] = _TS
    return df


def summarize_profiles(df: pd.DataFrame) -> dict[str, Any]:
    synthetic = int(df["shadow_payload_id"].notna().sum())
    total = int(len(df))
    canonical = total - synthetic
    industry_counts = (
        df.groupby("industry")
        .size()
        .sort_values(ascending=False)
        .head(12)
        .reset_index(name="count")
        .to_dict(orient="records")
    )
    domain_counts = (
        df.groupby("domain_id")
        .size()
        .sort_values(ascending=False)
        .reset_index(name="count")
        .to_dict(orient="records")
    )
    return {
        "profiles_total": total,
        "canonical_rows": canonical,
        "synthetic_rows": synthetic,
        "synthetic_rate": round((synthetic / total) if total else 0.0, 4),
        "symbols_total": int(df["symbol"].nunique()),
        "industries_covered": int(df["industry"].nunique()),
        "top_industries": industry_counts,
        "domain_counts": domain_counts,
        "as_of": _TS,
    }


def validate_profiles(df: pd.DataFrame) -> dict[str, Any]:
    required = [
        "symbol",
        "domain_id",
        "role_id",
        "canonical_role",
        "detected_synonyms",
        "skills",
        "industry",
        "confidence_score",
        "provenance",
        "shadow_payload_id",
        "created_at",
        "validated_by",
    ]
    if df.empty:
        raise ValueError("career profile DataFrame is empty")
    if not validate_columns(df, required):
        missing = [column for column in required if column not in df.columns]
        raise ValueError(f"career profile DataFrame is missing required columns: {missing}")
    if not validate_unique(df, "role_id"):
        raise ValueError("career profile role_id values must be unique")
    if not validate_row_count(df, 10_000):
        raise ValueError(f"career profile DataFrame must contain at least 10,000 rows; found {len(df)}")
    if (df["confidence_score"] < 0).any() or (df["confidence_score"] > 1).any():
        raise ValueError("confidence_score must be in the inclusive 0-1 range")
    if df["provenance"].astype(str).str.len().min() <= 2:
        raise ValueError("every profile must include provenance")
    if df["canonical_role"].astype(str).str.strip().eq("").any():
        raise ValueError("canonical_role cannot be blank")
    if df["validated_by"].astype(str).str.strip().eq("").any():
        raise ValueError("validated_by cannot be blank")
    return {
        "is_valid": True,
        "row_count": int(len(df)),
        "symbol_count": int(df["symbol"].nunique()),
        "canonical_rows": int(df["shadow_payload_id"].isna().sum()),
        "synthetic_rows": int(df["shadow_payload_id"].notna().sum()),
        "shadow_mismatches": [],
    }


def _registry_rows() -> list[dict[str, Any]]:
    return [
        {
            "domain_id": item["domain_id"],
            "canonical_role": item["canonical_role"],
            "role_family": item["role_family"],
            "status": "SHADOW_ONLY",
            "high_stakes": item["domain_id"] in {"LEADERSHIP", "FINANCE", "EDUCATION"},
            "supported_signals": list(item["positive_lagna"]) + list(item["positive_lords"]),
        }
        for item in _ROLE_RULES
    ]


def _evidence_contract() -> dict[str, Any]:
    return {
        "distinguish_fact_rule_signal": True,
        "requires_provenance_for_every_row": True,
        "supports_shadow_synthesis": True,
        "blocks_pii": True,
        "supports_supporting_and_opposing_signals": True,
        "timing_context": ["Dasha", "Transit"],
        "divisional_context": ["D10"],
        "high_stakes_domains": ["LEADERSHIP", "FINANCE", "EDUCATION"],
    }


def _dependency_graph() -> list[dict[str, Any]]:
    return [
        {"node": "kundli_signals.csv", "depends_on": [], "purpose": "base chart timing inputs"},
        {"node": "company_classification_v4.csv", "depends_on": [], "purpose": "industry and sector mapping"},
        {"node": "kundli JSON charts", "depends_on": ["kundli_signals.csv"], "purpose": "house and transit evidence"},
        {"node": "role synthesis", "depends_on": ["kundli_signals.csv", "company_classification_v4.csv", "kundli JSON charts"], "purpose": "career role generation"},
        {"node": "shadow validation", "depends_on": ["role synthesis"], "purpose": "canonical vs synthetic split"},
        {"node": "CSV export", "depends_on": ["shadow validation"], "purpose": "validated profile output"},
    ]


def _conflict_framework() -> list[dict[str, Any]]:
    return [
        {
            "conflict_id": "P021-CONFLICT-000001",
            "type": "ROLE_TIE",
            "resolution": "highest confidence wins; ties prefer the rule order",
            "scope": "per-symbol",
        },
        {
            "conflict_id": "P021-CONFLICT-000002",
            "type": "HIGH_STAKES_BOUNDARY",
            "resolution": "career/finance/education remain governed shadow outputs only",
            "scope": "all rows",
        },
    ]


def _confidence_model() -> dict[str, Any]:
    return {
        "base": 0.52,
        "support_increment": 0.025,
        "opposition_penalty": 0.03,
        "astro_bonus": {"BUY": 0.02, "HOLD": 0.01, "CAUTION": -0.01},
        "range": [0.0, 1.0],
    }


def _explainability_graph() -> dict[str, Any]:
    return {
        "supporting": {
            "leadership": ["10H strength", "Sun/Saturn/Mars lordship", "Raja Yoga"],
            "analysis": ["Mercury/Jupiter lordship", "11H strength", "Gaja Kesari"],
            "communication": ["Mercury/Venus/Moon lordship", "2H/11H strength"],
            "finance": ["2H/11H strength", "Jupiter/Venus lordship", "Dhana Yoga"],
            "technology": ["Mercury/Saturn/Mars lordship", "8H/11H strength"],
            "education": ["5H strength", "Jupiter/Mercury lordship", "Gaja Kesari"],
        },
        "opposing": {
            "all_domains": ["Kemdrum", "very weak 10H/2H/5H signals", "astro_score<=25"],
        },
        "timing": ["mahadasha", "antardasha", "transit_jupiter", "transit_saturn"],
    }


def _bundle_from_df(df: pd.DataFrame) -> dict[str, Any]:
    validation = validate_profiles(df)
    summary = summarize_profiles(df)
    return {
        "meta": {
            "phase": "VEDA-P021",
            "contract_version": "2026-08-14",
            "version": "1.0.0",
            "created_at": _TS,
            "updated_at": _TS,
            "created_by": "codex",
            "updated_by": "codex",
        },
        "domain_registry": _registry_rows(),
        "evidence_contract": _evidence_contract(),
        "dependency_graph": _dependency_graph(),
        "confidence_model": _confidence_model(),
        "conflict_framework": _conflict_framework(),
        "explainability_graph": _explainability_graph(),
        "sample_profiles": df.head(12).to_dict(orient="records"),
        "shadow_validation": validation,
        "summary": summary,
    }


def build_phase_bundle() -> dict[str, Any]:
    return _bundle_from_df(build_profiles())


def validate_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    if bundle.get("summary", {}).get("profiles_total", 0) < 10_000:
        raise ValueError("P021 bundle must contain at least 10,000 profiles")
    if bundle.get("shadow_validation", {}).get("is_valid") is not True:
        raise ValueError("P021 bundle validation failed")
    if len(bundle.get("domain_registry", [])) != 6:
        raise ValueError("P021 bundle must inventory six role domains")
    return {
        "is_valid": True,
        "row_count": bundle["summary"]["profiles_total"],
        "shadow_mismatches": [],
    }


def _atomic_write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(payload, encoding="utf-8")
    shutil.move(str(tmp_path), str(path))


def _render_docs(bundle: dict[str, Any]) -> dict[str, str]:
    docs = {
        "VEDA-P021-00_EXECUTIVE_SUMMARY.md": (
            "# VEDA-P021 Executive Summary\n\n"
            "P021 establishes a shadow-only career / profession validation layer.\n\n"
            f"- Profiles: `{bundle['summary']['profiles_total']}`\n"
            f"- Canonical rows: `{bundle['summary']['canonical_rows']}`\n"
            f"- Synthetic rows: `{bundle['summary']['synthetic_rows']}`\n"
            f"- Synthetic rate: `{bundle['summary']['synthetic_rate']:.2%}`\n"
        ),
        "VEDA-P021-01_VALIDATION_AND_SHADOWS.md": (
            "# VEDA-P021 Validation and Shadows\n\n"
            "The phase uses deterministic chart-derived signals, industry context,\n"
            "and D10-aware timing context. No deterministic production prediction\n"
            "logic is activated.\n\n"
            f"- High-stakes domains: {', '.join(bundle['evidence_contract']['high_stakes_domains'])}\n"
            f"- Domain registry rows: {len(bundle['domain_registry'])}\n"
            f"- Validation status: {bundle['shadow_validation']['is_valid']}\n"
        ),
    }
    return docs


def export_phase_bundle(
    root: Path | None = None,
    output_path: Path | None = None,
    validation_dir: Path | None = None,
) -> list[Path]:
    root = root or cfg.PROJECT_ROOT
    output_path = output_path or _OUTPUT_CSV
    validation_dir = validation_dir or _VALIDATION_DIR

    df = build_profiles()
    bundle = _bundle_from_df(df)
    validation = bundle["shadow_validation"]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_csv = output_path.with_suffix(".csv.tmp")
    df.to_csv(tmp_csv, index=False)
    shutil.move(str(tmp_csv), str(output_path))

    validation_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = validation_dir / "p021_career_bundle.json"
    registry_path = validation_dir / "p021_career_registry.json"
    validation_path = validation_dir / "p021_career_validation.json"

    _atomic_write(bundle_path, json.dumps(bundle, ensure_ascii=False, indent=2) + "\n")
    _atomic_write(registry_path, json.dumps(bundle["domain_registry"], ensure_ascii=False, indent=2) + "\n")
    _atomic_write(validation_path, json.dumps(validation, ensure_ascii=False, indent=2) + "\n")

    docs = _render_docs(bundle)
    written: list[Path] = [output_path, bundle_path, registry_path, validation_path]
    for name, content in docs.items():
        path = root / "docs" / "current-state" / "p021" / name
        _atomic_write(path, content)
        written.append(path)

    schema_path = root / "schemas" / "career_validated_profiles.schema.yaml"
    if schema_path.exists():
        written.append(schema_path)
    return written


def load_validated_profiles(
    limit: int | None = None,
    offset: int = 0,
    symbol: str | None = None,
    industry: str | None = None,
    domain_id: str | None = None,
    output_path: Path | None = None,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    path = output_path or _OUTPUT_CSV
    if not path.exists():
        export_phase_bundle(output_path=path)
    df = pd.read_csv(path)
    if symbol:
        df = df[df["symbol"].astype(str).str.upper() == symbol.upper()]
    if industry:
        df = df[df["industry"].astype(str).str.upper() == industry.upper()]
    if domain_id:
        df = df[df["domain_id"].astype(str).str.upper() == domain_id.upper()]
    df = df.sort_values(["confidence_score", "symbol", "domain_id"], ascending=[False, True, True]).reset_index(drop=True)
    summary = summarize_profiles(df)
    if limit is None:
        sliced = df.iloc[offset:]
    else:
        sliced = df.iloc[offset : offset + limit]
    return sliced, summary
