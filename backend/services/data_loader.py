"""
Data Loader — Phase 10
Loads all intelligence CSVs into memory at startup.
Auto-reloads every 60 minutes via background thread.
Thread-safe reads via a shared state dict + lock.
"""

import json
import threading
import time
from pathlib import Path

import pandas as pd

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

RELOAD_INTERVAL_S = 3600  # 60 minutes

# ── Source files ──────────────────────────────────────────────────────────────

SOURCES = {
    "participant_intel":    cfg.INTELLIGENCE_DIR / "participant_intelligence.csv",
    "participant_flows":    cfg.INTELLIGENCE_DIR / "participant_flow_scores.csv",
    "sector_rotation":      cfg.INTELLIGENCE_DIR / "sector_rotation_intelligence.csv",
    "sector_flows":         cfg.INTELLIGENCE_DIR / "sector_flow_scores.csv",
    "bull_run":             cfg.INTELLIGENCE_DIR / "bull_run_probability.csv",
    "bull_run_watchlist":   cfg.INTELLIGENCE_DIR / "bull_run_watchlist.csv",
    "deal_signals":         cfg.INTELLIGENCE_DIR / "institutional_deal_signals.csv",
    "event_calendar":       cfg.INTELLIGENCE_DIR / "event_calendar.csv",
    "upcoming_catalysts":   cfg.INTELLIGENCE_DIR / "upcoming_catalysts.csv",
    "corporate_confidence": cfg.INTELLIGENCE_DIR / "corporate_confidence_scores.csv",
    "price_momentum":       cfg.INTELLIGENCE_DIR / "price_momentum.csv",
    # Phase 15 — Fundamentals
    "valuation_scores":       cfg.NSE_DIR / "results" / "valuation_scores.csv",
    "shareholding":           cfg.NSE_DIR / "shareholding" / "quarterly_shp.csv",
    # Phase 15B — Extended Financials (OPM, ROCE, Book Value, Sales Growth 3Y)
    "extended_financials":    cfg.NSE_DIR / "results" / "extended_financials.csv",
    # Phase 16 — Management Intelligence
    "holding_trends":       cfg.NSE_DIR / "shareholding" / "holding_trends.csv",
    "management_sentiment": cfg.NSE_DIR / "shareholding" / "management_sentiment.csv",
    # Phase 7C / Corporate Actions
    "corp_actions":         cfg.INTELLIGENCE_DIR / "corporate_action_signals.csv",
    # Phase 7A raw deal tape (individual block/bulk deals with client names)
    "block_deals":          cfg.INTELLIGENCE_DIR / "block_bulk_deals.csv",
    # Phase UI-C: sequence-paired client transactions (precomputed by the
    # engine -- pairing is too slow to run per-request)
    "deal_records":         cfg.INTELLIGENCE_DIR / "deal_records.csv",
    # Phase 18 — Corporate Announcements Intelligence
    "announcements":        cfg.INTELLIGENCE_DIR / "company_announcements.csv",
    "announcement_signals": cfg.INTELLIGENCE_DIR / "announcement_signals.csv",
    # Phase A/C — Technical + F&O + Trade Conviction Intelligence
    "ml_scores":              cfg.INTELLIGENCE_DIR / "ml_scores_combined.csv",
    # Phase 12C — Forward return model (trained on realized returns)
    "fwd_return_scores":      cfg.INTELLIGENCE_DIR / "ml_forward_return_scores.csv",
    "technical":              cfg.INTELLIGENCE_DIR / "technical_indicators.csv",
    "fno_intel":              cfg.INTELLIGENCE_DIR / "fno_intelligence.csv",
    "watchlist_metrics":      cfg.INTELLIGENCE_DIR / "watchlist_metrics.csv",   # Phase WL-1
    "trade_conviction":       cfg.INTELLIGENCE_DIR / "trade_conviction_scores.csv",
    "index_momentum":         cfg.INTELLIGENCE_DIR / "index_momentum.csv",
    "quarterly_results":      cfg.NSE_DIR / "results" / "quarterly_results.csv",
    "theme_intelligence":     cfg.INTELLIGENCE_DIR / "theme_intelligence.csv",
    "theme_tagging":          cfg.REFERENCE_DIR / "theme_tagging.csv",
    # Phase FPI — NSDL/CDSL/SEBI sector FPI ownership signals
    "fpi_signals":            cfg.FPI_DIR / "fpi_sector_signals.csv",
    # Phase AF — AstroFinance Intelligence
    "astro_signals":          cfg.INTELLIGENCE_DIR / "astro_signals.csv",
    # Phase F — Alt-data intelligence
    "news_signals":           cfg.INTELLIGENCE_DIR / "news_signals.csv",
    "news_sentiment":         cfg.INTELLIGENCE_DIR / "news_sentiment.csv",
    "insider_signals":        cfg.INTELLIGENCE_DIR / "insider_signals.csv",
    "concall_summary":        cfg.INTELLIGENCE_DIR / "concall_summary.csv",
    # Phase G — Consensus + purity
    "consensus_scores":       cfg.INTELLIGENCE_DIR / "consensus_scores.csv",
    "purity_change_log":      cfg.INTELLIGENCE_DIR / "purity_change_log.csv",
    # Phase H — Trend + AGM + Theme momentum
    "trend_scores":           cfg.INTELLIGENCE_DIR / "trend_scores.csv",
    "agm_signals":            cfg.INTELLIGENCE_DIR / "agm_signals.csv",
    "theme_momentum":         cfg.INTELLIGENCE_DIR / "theme_momentum.csv",
    # Phase D — Key S/R levels (confluence engine)
    "key_levels":             cfg.INTELLIGENCE_DIR / "key_levels.csv",
}

_MARKET_CONTEXT_PATH = cfg.INTELLIGENCE_DIR / "market_context.json"
_ASTRO_CONTEXT_PATH  = cfg.INTELLIGENCE_DIR / "market_astro_context.json"

_lock = threading.Lock()
_data: dict[str, pd.DataFrame | None] = {k: None for k in SOURCES}
_loaded_at: dict[str, str | None] = {k: None for k in SOURCES}
_dataset_metadata: dict[str, dict] = {}

_DATE_COLUMNS = (
    "as_of_date",
    "date",
    "filing_date",
    "date_end",
    "last_date",
    "latest_date",
    "trade_date",
    "event_date",
    "ex_date_dt",
)
_FRESHNESS_RANK = {
    "INTRADAY": 0,
    "EOD": 1,
    "DELAYED": 2,
    "STALE": 3,
    "QUALITY_WARNING": 4,
    "UNKNOWN": 5,
    "UNAVAILABLE": 6,
}
_EOD_MAX_BUSINESS_LAG = 1
_DELAYED_MAX_BUSINESS_LAG = 3
_SCHEDULED_DATE_DATASETS = {"event_calendar", "upcoming_catalysts", "corp_actions"}


def _utc_iso(path: Path) -> str | None:
    try:
        return pd.Timestamp.fromtimestamp(path.stat().st_mtime, tz="UTC").isoformat()
    except OSError:
        return None


def _date_summary_for_column(
    df: pd.DataFrame, date_column: str
) -> tuple[str, str | None, int, int]:
    parsed = pd.to_datetime(df[date_column], errors="coerce", format="mixed")
    # Reject truncated legacy years such as ``10-Nov-202`` instead of
    # allowing pandas to interpret them as year 0202.
    valid_year = parsed.dt.year.between(1900, 2100)
    parsed.loc[~valid_year] = pd.NaT
    valid = parsed.dropna()
    if valid.empty:
        return date_column, None, int(parsed.isna().sum()), 0
    return (
        date_column,
        valid.max().date().isoformat(),
        int(parsed.isna().sum()),
        int(valid.nunique()),
    )


def _date_summary(df: pd.DataFrame) -> tuple[str | None, str | None, int, int]:
    date_column = next((column for column in _DATE_COLUMNS if column in df.columns), None)
    if date_column is None:
        return None, None, 0, 0
    return _date_summary_for_column(df, date_column)


def _business_day_lag(as_of: str, today: pd.Timestamp) -> int | None:
    as_of_date = pd.Timestamp(as_of).normalize()
    today = today.normalize()
    if as_of_date > today:
        return None
    if as_of_date == today:
        return 0
    return max(0, len(pd.bdate_range(as_of_date, today)) - 1)


def _freshness_from_lag(lag: int | None) -> str:
    if lag is None:
        return "UNKNOWN"
    if lag <= _EOD_MAX_BUSINESS_LAG:
        return "EOD"
    if lag <= _DELAYED_MAX_BUSINESS_LAG:
        return "DELAYED"
    return "STALE"


def _build_metadata(
    key: str,
    path: Path,
    df: pd.DataFrame | None,
    now: pd.Timestamp | None = None,
) -> dict:
    source = f"FII-DII provider-local dataset: {path.name}"
    updated = _utc_iso(path)
    if df is None or df.empty:
        return {
            "dataset": key,
            "source": source,
            "as_of": None,
            "freshness": "UNAVAILABLE",
            "last_successful_update": updated,
            "dataset_build_at": updated,
            "row_count": 0 if df is None else len(df),
            "date_column": None,
            "retrieval_column": None,
            "retrieved_rows": 0,
            "retrieval_coverage": "UNAVAILABLE",
            "null_date_rows": 0,
            "limitations": [
                "Dataset is unavailable or empty; no current evidence is claimed."
            ],
        }

    date_column, as_of, null_date_rows, distinct_dates = _date_summary(df)
    limitations: list[str] = []
    if (
        key == "quarterly_results"
        and date_column == "filing_date"
        and null_date_rows > len(df) // 2
        and "date_end" in df.columns
    ):
        date_column, as_of, null_date_rows, distinct_dates = _date_summary_for_column(
            df, "date_end"
        )
        limitations.append(
            "quarterly_results: filing_date coverage is insufficient; freshness is "
            "based on valid period-end date_end values."
        )
    if key in _SCHEDULED_DATE_DATASETS:
        freshness = _freshness_from_lag(
            _business_day_lag(
                updated[:10] if updated else "",
                (now or pd.Timestamp.now()).normalize(),
            )
            if updated
            else None
        )
        limitations.append(
            "Scheduled event dates are not used as the dataset freshness timestamp."
        )
        as_of = None
    elif date_column is None or as_of is None:
        freshness = "UNKNOWN"
        limitations.append(
            "No usable date column is available; freshness cannot be established."
        )
    else:
        lag = _business_day_lag(as_of, (now or pd.Timestamp.now()).normalize())
        if lag is None:
            freshness = "QUALITY_WARNING"
            limitations.append(
                "Latest dataset date is in the future relative to provider runtime date."
            )
        elif lag <= _EOD_MAX_BUSINESS_LAG:
            freshness = "EOD"
        elif lag <= _DELAYED_MAX_BUSINESS_LAG:
            freshness = "DELAYED"
        else:
            freshness = "STALE"
            limitations.append(
                f"{key}: latest dated evidence is {lag} business days behind provider runtime date."
            )
    if null_date_rows:
        limitations.append(
            f"{key}: {null_date_rows} row(s) have an invalid or missing "
            f"{date_column or 'date'} value."
        )

    retrieval_column = "retrieved_at" if "retrieved_at" in df.columns else None
    retrieved_rows = 0
    retrieval_coverage = "LEGACY_RETRIEVAL_TIMESTAMP_UNAVAILABLE"
    if retrieval_column:
        retrieved_rows = int(df[retrieval_column].notna().sum())
        retrieval_coverage = (
            "COMPLETE" if retrieved_rows == len(df)
            else "PARTIAL" if retrieved_rows
            else "NO_RETRIEVAL_TIMESTAMPS"
        )

    return {
        "dataset": key,
        "source": source,
        "as_of": as_of,
        "freshness": freshness,
        "last_successful_update": updated,
        "dataset_build_at": updated,
        "row_count": len(df),
        "date_column": date_column,
        "retrieval_column": retrieval_column,
        "retrieved_rows": retrieved_rows,
        "retrieval_coverage": retrieval_coverage,
        "distinct_dates": distinct_dates,
        "null_date_rows": null_date_rows,
        "limitations": limitations,
    }


def _unavailable_metadata(key: str, path: Path) -> dict:
    return _build_metadata(key, path, None)


def _load_all():
    loaded = 0
    for key, path in SOURCES.items():
        if not path.exists():
            logger.warning(f"[DataLoader] Missing: {path.name}")
            with _lock:
                _data[key] = None
                _loaded_at[key] = None
                _dataset_metadata[key] = _unavailable_metadata(key, path)
            continue
        try:
            df = pd.read_csv(path, low_memory=False)
            with _lock:
                _data[key] = df
                _loaded_at[key] = pd.Timestamp.now().isoformat()
                _dataset_metadata[key] = _build_metadata(key, path, df)
            loaded += 1
            logger.debug(f"[DataLoader] Loaded {path.name}: {len(df)} rows")
        except Exception as e:
            logger.error(f"[DataLoader] Failed to load {path.name}: {e}")
            with _lock:
                _data[key] = None
                _loaded_at[key] = None
                _dataset_metadata[key] = _unavailable_metadata(key, path)

    logger.info(f"[DataLoader] Loaded {loaded}/{len(SOURCES)} intelligence files")


def _reload_loop():
    while True:
        time.sleep(RELOAD_INTERVAL_S)
        logger.info("[DataLoader] Auto-reload triggered")
        _load_all()


def startup():
    """Load all data at app startup and launch background reload thread."""
    _load_all()
    t = threading.Thread(target=_reload_loop, daemon=True)
    t.start()
    logger.info("[DataLoader] Background reload thread started (60 min interval)")


def get(key: str) -> pd.DataFrame | None:
    """Thread-safe getter for a loaded DataFrame. Returns None if not available."""
    with _lock:
        return _data.get(key)


def get_market_context() -> dict:
    """Load market_context.json (PCR, date). Returns empty dict if missing."""
    try:
        if _MARKET_CONTEXT_PATH.exists():
            with open(_MARKET_CONTEXT_PATH, encoding="utf-8") as fh:
                return json.load(fh)
    except Exception:
        pass
    return {}


def get_astro_context() -> dict:
    """Load market_astro_context.json (planetary pulse). Returns empty dict if missing."""
    try:
        if _ASTRO_CONTEXT_PATH.exists():
            with open(_ASTRO_CONTEXT_PATH, encoding="utf-8") as fh:
                return json.load(fh)
    except Exception:
        pass
    return {}


def freshness() -> dict:
    """Return legacy load timestamps for all datasets."""
    with _lock:
        return {k: v for k, v in _loaded_at.items()}


def freshness_for(
    required_keys: tuple[str, ...], optional_keys: tuple[str, ...] = ()
) -> dict:
    """Return a bounded freshness/provenance contract for provider responses.

    Required datasets determine the aggregate state. Optional datasets are
    reported for transparency but cannot make an otherwise usable response
    unavailable. Missing values remain explicit in the endpoint payloads.
    """
    keys = tuple(dict.fromkeys((*required_keys, *optional_keys)))
    with _lock:
        datasets = {key: dict(_dataset_metadata.get(key, {})) for key in keys}

    required = [datasets[key] for key in required_keys]
    optional = [datasets[key] for key in optional_keys]
    if not required:
        required = optional

    def rank(item: dict) -> int:
        return _FRESHNESS_RANK.get(str(item.get("freshness", "UNKNOWN")), 5)

    worst = max(required, key=rank) if required else {"freshness": "UNAVAILABLE"}
    required_dates = [str(item["as_of"]) for item in required if item.get("as_of")]
    sources = [str(item["source"]) for item in datasets.values() if item.get("source")]
    limitations: list[str] = []
    for item in (*required, *optional):
        for limitation in item.get("limitations", []):
            if limitation not in limitations:
                limitations.append(limitation)
    if any(rank(item) >= _FRESHNESS_RANK["UNAVAILABLE"] for item in required):
        limitations.append("One or more required datasets are unavailable.")
    if any(rank(item) >= _FRESHNESS_RANK["UNAVAILABLE"] for item in optional):
        limitations.append(
            "One or more optional datasets are unavailable; affected fields are omitted."
        )

    updates = [
        item["last_successful_update"]
        for item in datasets.values()
        if item.get("last_successful_update")
    ]
    return {
        "state": str(worst.get("freshness", "UNAVAILABLE")),
        "as_of": min(required_dates) if required_dates else None,
        "source": sources,
        "last_successful_update": min(updates) if updates else None,
        "limitations": limitations,
        "datasets": datasets,
    }


def freshness_metadata() -> dict:
    """Return all dataset freshness metadata without hiding legacy timestamps."""
    with _lock:
        metadata = {key: dict(value) for key, value in _dataset_metadata.items()}
        loaded_at = dict(_loaded_at)
    return {"datasets": metadata, "legacy_loaded_at": loaded_at}
