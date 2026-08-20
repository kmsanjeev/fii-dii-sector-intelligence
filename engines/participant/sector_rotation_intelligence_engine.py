"""
Sector Rotation Intelligence Engine
Phase 6C — deterministic sector leadership, breadth and rotation contract.

This remains the authoritative sector engine. It preserves the legacy flow /
price fields consumed by existing engines and adds an evidence-aware layer
based on current constituent prices. Participant values are deliberately
labelled as market-level context: the existing weighted allocation is not
direct sector-specific FII/DII attribution.
"""

import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("sector_rotation_intelligence")

INTELLIGENCE_DIR = cfg.INTELLIGENCE_DIR
FPI_SIGNALS_FILE = cfg.FPI_DIR / "fpi_sector_signals.csv"
FLOW_SCORES_FILE = INTELLIGENCE_DIR / "sector_flow_scores.csv"
INDEX_STRENGTH = INTELLIGENCE_DIR / "index_strength.csv"
SECTOR_ROTATION = INTELLIGENCE_DIR / "sector_rotation.csv"
SNAPSHOT_OUTPUT = INTELLIGENCE_DIR / "sector_rotation_intelligence.csv"
HISTORY_OUTPUT = INTELLIGENCE_DIR / "sector_rotation_history.csv"
CLASSIFICATION_FILE = cfg.DATA_DIR / "reference" / "company_classification_v4.csv"
BENCHMARK_FILE = cfg.INDICES_DIR / "nifty_50_constituents.csv"

SECTOR_CONTRACT_VERSION = "sector-rotation-1.1"
PRICE_HISTORY_DAYS = 21
RETURN_WINDOWS = (1, 3, 5, 10, 20)
INSTITUTIONAL_CONTEXT_SCOPE = "MARKET_LEVEL_CONTEXT_ONLY"
INSTITUTIONAL_EVIDENCE_TYPE = "WEIGHT_ALLOCATED_MARKET_PARTICIPANT_CONTEXT"

# Best-fit NSE index names are retained for legacy compatibility and source
# traceability. They are not used as a substitute for current constituent
# breadth when an index file is stale.
NSE_TO_PLATFORM = {
    "NIFTY BANK": "BANKING",
    "NIFTY PSU BANK": "BANKING",
    "NIFTY PRIVATE BANK": "BANKING",
    "NIFTY FINANCIAL SERVICES": "FINANCIAL_SERVICES",
    "NIFTY FINANCIAL SERVICES 25/50": "FINANCIAL_SERVICES",
    "NIFTY FINANCIAL SERVICES EX-BANK": "FINANCIAL_SERVICES",
    "NIFTY CAPITAL MARKETS": "AMC",
    "NIFTY IT": "IT",
    "NIFTY MIDSMALL IT & TELECOM": "IT",
    "NIFTY PHARMA": "PHARMA",
    "NIFTY HEALTHCARE INDEX": "HEALTHCARE",
    "NIFTY MIDSMALL HEALTHCARE": "HEALTHCARE",
    "NIFTY500 HEALTHCARE": "HEALTHCARE",
    "NIFTY FMCG": "FMCG",
    "NIFTY NON-CYCLICAL CONSUMER": "FMCG",
    "NIFTY AUTO": "AUTO",
    "NIFTY CONSUMER DURABLES": "CAPITAL_GOODS",
    "NIFTY METAL": "METAL",
    "NIFTY COMMODITIES": "METAL",
    "NIFTY REALTY": "REALTY",
    "NIFTY REITS & REALTY": "REALTY",
    "NIFTY ENERGY": "ENERGY",
    "NIFTY OIL & GAS": "ENERGY",
    "NIFTY INFRASTRUCTURE": "INFRASTRUCTURE",
    "NIFTY MEDIA": "MEDIA",
    "NIFTY SERVICES SECTOR": "FINANCIAL_SERVICES",
    "NIFTY CHEMICALS": "CHEMICALS",
    "NIFTY CEMENT": "CEMENT",
    "NIFTY PSE": "DIVERSIFIED",
    "NIFTY CPSE": "DIVERSIFIED",
    "NIFTY MNC": "DIVERSIFIED",
    "NIFTY MIDSMALL FINANCIAL SERVICES": "FINANCIAL_SERVICES",
}


def _finite(value: object, default: float | None = None) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if np.isfinite(result) else default


def _date_from_file(path: Path) -> str | None:
    match = re.search(r"(\d{8})", path.stem)
    if match:
        raw = match.group(1)
        return f"{raw[:4]}-{raw[4:6]}-{raw[6:]}"
    # The legacy NSE index export uses names such as
    # ``MW-All-Indices-05-Jun-2026.csv``.  Keep this parser scoped to the
    # explicit day-month-year form; other filenames remain undated.
    named = re.search(r"(\d{2}-[A-Za-z]{3}-\d{4})", path.stem)
    if named:
        try:
            return (
                datetime.strptime(named.group(1), "%d-%b-%Y")
                .replace(tzinfo=timezone.utc)
                .date()
                .isoformat()
            )
        except ValueError:
            return None
    return None


def _read_daily_close(path: Path) -> pd.Series:
    """Read one EQ bhavcopy into a symbol-indexed close series."""
    try:
        raw = pd.read_csv(path, low_memory=False)
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        logger.warning("[6C] Could not read %s: %s", path.name, exc)
        return pd.Series(dtype=float)
    raw.columns = [str(column).strip() for column in raw.columns]
    if "SYMBOL" not in raw.columns or "SERIES" not in raw.columns:
        return pd.Series(dtype=float)
    close_column = "CLOSE_PRICE" if "CLOSE_PRICE" in raw.columns else "CLOSE"
    if close_column not in raw.columns:
        return pd.Series(dtype=float)
    raw = raw[raw["SERIES"].astype(str).str.strip().str.upper() == "EQ"]
    raw["SYMBOL"] = raw["SYMBOL"].astype(str).str.strip().str.upper()
    raw[close_column] = pd.to_numeric(raw[close_column], errors="coerce")
    raw = raw[(raw["SYMBOL"] != "") & (raw[close_column] > 0)]
    return raw.drop_duplicates("SYMBOL", keep="last").set_index("SYMBOL")[close_column]


def _rolling_return(series: pd.Series, window: int) -> pd.Series:
    return (
        series.rolling(window, min_periods=window)
        .apply(lambda values: float(np.prod(1.0 + values / 100.0) - 1.0), raw=True)
        .mul(100.0)
    )


def _cross_sectional_score(values: pd.Series) -> pd.Series:
    """Map valid cross-sectional values to -100..100; preserve missing."""
    result = pd.Series(np.nan, index=values.index, dtype=float)
    valid = values.notna()
    if valid.sum() == 0:
        return result
    if valid.sum() == 1:
        result.loc[valid] = 0.0
        return result
    result.loc[valid] = (
        values.loc[valid].rank(method="average", pct=True).mul(200).sub(100)
    )
    return result.round(2)


class SectorRotationIntelligenceEngine:
    """Build the legacy snapshot plus a bounded, explainable sector contract."""

    def run(self) -> bool:
        logger.info("[SectorRotationIntelligence] Starting Phase 6C")
        INTELLIGENCE_DIR.mkdir(parents=True, exist_ok=True)
        sector_map = self._load_sector_map()
        if not sector_map:
            logger.error("[6C] sector classification is empty")
            return False
        benchmark_symbols = self._load_benchmark_symbols()
        price_history, prices = self._build_price_history(sector_map, benchmark_symbols)
        if price_history.empty:
            logger.error("[6C] no usable current constituent price history")
            return False
        flow_scores, institutional_date = self._load_flow_scores()
        fpi_map, fpi_date = self._load_fpi_signals()
        legacy_price_map, legacy_index_date = self._build_price_map()
        snapshot = self._build_snapshot(
            price_history=price_history,
            prices=prices,
            sector_map=sector_map,
            flow_scores=flow_scores,
            fpi_map=fpi_map,
            fpi_date=fpi_date,
            institutional_date=institutional_date,
            legacy_price_map=legacy_price_map,
            legacy_index_date=legacy_index_date,
            benchmark_symbols=benchmark_symbols,
        )
        history = self._build_history_output(price_history, flow_scores)
        self._save_atomic(history, HISTORY_OUTPUT)
        self._save_atomic(snapshot, SNAPSHOT_OUTPUT)
        self._print_summary(snapshot)
        return True

    # ------------------------------------------------------------------
    # Inputs and taxonomy
    # ------------------------------------------------------------------
    @staticmethod
    def _load_sector_map() -> dict[str, str]:
        if not CLASSIFICATION_FILE.exists():
            return {}
        df = pd.read_csv(CLASSIFICATION_FILE, usecols=["SYMBOL", "SECTOR"])
        df["SYMBOL"] = df["SYMBOL"].astype(str).str.strip().str.upper()
        df["SECTOR"] = df["SECTOR"].astype(str).str.strip().str.upper()
        df = df[(df["SYMBOL"] != "") & (df["SECTOR"] != "") & (df["SECTOR"] != "NAN")]
        return (
            df.drop_duplicates("SYMBOL", keep="first")
            .set_index("SYMBOL")["SECTOR"]
            .to_dict()
        )

    @staticmethod
    def _load_benchmark_symbols() -> set[str]:
        if not BENCHMARK_FILE.exists():
            return set()
        df = pd.read_csv(BENCHMARK_FILE, low_memory=False)
        column = next(
            (c for c in ("symbol", "SYMBOL", "Symbol") if c in df.columns), None
        )
        if not column:
            return set()
        return {
            str(value).strip().upper()
            for value in df[column].dropna()
            if str(value).strip()
        }

    def _build_price_history(
        self, sector_map: dict[str, str], benchmark_symbols: set[str]
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        candidates = []
        for path in cfg.NSE_EQUITY_BHAVCOPY_DIR.rglob("*.csv"):
            date = _date_from_file(path)
            if date:
                candidates.append((date, path))
        candidates = sorted(candidates, key=lambda item: item[0])[
            -(PRICE_HISTORY_DAYS + 1) :
        ]
        frames: dict[str, pd.Series] = {}
        for date, path in candidates:
            closes = _read_daily_close(path)
            if not closes.empty:
                frames[date] = closes
        if len(frames) < 2:
            return pd.DataFrame(), pd.DataFrame()
        prices = pd.DataFrame(frames).T.sort_index()
        prices = prices[~prices.index.duplicated(keep="last")]
        daily = prices.pct_change(fill_method=None).mul(100.0)
        sectors = sorted(set(sector_map.values()))
        sector_counts = pd.Series(sector_map).value_counts().to_dict()
        benchmark = sorted(benchmark_symbols & set(prices.columns))
        rows: list[dict[str, object]] = []
        for date in daily.index:
            day = daily.loc[date]
            benchmark_values = day.reindex(benchmark)
            benchmark_usable = int(benchmark_values.notna().sum())
            benchmark_return = _finite(benchmark_values.mean(), None)
            for sector in sectors:
                symbols = [
                    symbol for symbol, value in sector_map.items() if value == sector
                ]
                values = day.reindex(symbols)
                usable = int(values.notna().sum())
                expected = int(sector_counts.get(sector, 0))
                rows.append(
                    {
                        "date": str(date),
                        "sector": sector,
                        "sector_return_1d": _finite(values.mean(), None),
                        "benchmark_return_1d": benchmark_return,
                        "constituent_expected": expected,
                        "constituent_usable": usable,
                        "constituent_coverage_pct": round(usable / expected * 100, 2)
                        if expected
                        else 0.0,
                        "benchmark_expected": len(benchmark_symbols),
                        "benchmark_usable": benchmark_usable,
                        "benchmark_coverage_pct": round(
                            benchmark_usable / len(benchmark_symbols) * 100, 2
                        )
                        if benchmark_symbols
                        else 0.0,
                    }
                )
        history = (
            pd.DataFrame(rows).sort_values(["sector", "date"]).reset_index(drop=True)
        )
        for window in RETURN_WINDOWS:
            history[f"sector_return_{window}d"] = history.groupby("sector")[
                "sector_return_1d"
            ].transform(lambda series, w=window: _rolling_return(series, w))
            history[f"benchmark_return_{window}d"] = history.groupby("sector")[
                "benchmark_return_1d"
            ].transform(lambda series, w=window: _rolling_return(series, w))
            history[f"relative_return_{window}d"] = (
                history[f"sector_return_{window}d"]
                - history[f"benchmark_return_{window}d"]
            ).round(4)
        history["relative_strength_rank_5d"] = history.groupby("date")[
            "relative_return_5d"
        ].rank(ascending=False, method="min")
        history = history.sort_values(["sector", "date"]).reset_index(drop=True)
        history["prior_relative_strength_rank_5d"] = history.groupby("sector")[
            "relative_strength_rank_5d"
        ].shift(1)
        history["rank_change_5d"] = (
            history["prior_relative_strength_rank_5d"]
            - history["relative_strength_rank_5d"]
        ).round(2)
        return history.sort_values(["date", "sector"]).reset_index(drop=True), prices

    # ------------------------------------------------------------------
    # Existing source layers (kept for compatibility, newly labelled)
    # ------------------------------------------------------------------
    @staticmethod
    def _load_flow_scores() -> tuple[pd.DataFrame, str | None]:
        if not FLOW_SCORES_FILE.exists():
            return pd.DataFrame(), None
        df = pd.read_csv(FLOW_SCORES_FILE, low_memory=False)
        if "date" not in df.columns:
            return pd.DataFrame(), None
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        df = df.dropna(subset=["date", "sector"]).copy()
        return df, str(df["date"].max()) if not df.empty else None

    @staticmethod
    def _load_fpi_signals() -> tuple[dict[str, float], str | None]:
        if not FPI_SIGNALS_FILE.exists():
            return {}, None
        try:
            fpi = pd.read_csv(FPI_SIGNALS_FILE, parse_dates=["date"])
            if fpi.empty:
                return {}, None
            latest = fpi["date"].max()
            recent = fpi[fpi["date"] == latest].copy()
            recent["fpi_norm"] = (
                pd.to_numeric(recent["signal_score"], errors="coerce").fillna(0) * 33
            ).clip(-100, 100)
            return dict(
                zip(recent["sector_normalized"], recent["fpi_norm"])
            ), latest.strftime("%Y-%m-%d")
        except (OSError, KeyError, ValueError, pd.errors.ParserError) as exc:
            logger.warning("[6C] Could not load FPI signals: %s", exc)
            return {}, None

    @staticmethod
    def _build_price_map() -> tuple[dict[str, float], str | None]:
        price_map: dict[str, float] = {}
        if SECTOR_ROTATION.exists():
            sr = pd.read_csv(SECTOR_ROTATION, low_memory=False)
            for _, row in sr.iterrows():
                platform = NSE_TO_PLATFORM.get(
                    str(row.get("INDEX_NAME", "")).strip().upper()
                )
                if not platform:
                    continue
                score = _finite(row.get("MOMENTUM_SCORE"), 0.0) or 0.0
                if platform not in price_map or score > price_map[platform]:
                    price_map[platform] = score
        source_dates = [
            date
            for path in cfg.INDICES_DIR.glob("MW-All-Indices-*.csv")
            if (date := _date_from_file(path))
        ]
        return price_map, max(source_dates) if source_dates else None

    # ------------------------------------------------------------------
    # Contract construction
    # ------------------------------------------------------------------
    @staticmethod
    def _breadth(
        prices: pd.DataFrame, sector_map: dict[str, str], sector: str, expected: int
    ) -> dict[str, object]:
        symbols = [symbol for symbol, value in sector_map.items() if value == sector]
        current_position = len(prices.index) - 1
        result: dict[str, object] = {}
        returns_for_top: pd.Series | None = None
        for window in (1, 5, 20):
            if current_position < window:
                values = pd.Series(dtype=float)
            else:
                previous = prices.iloc[current_position - window].reindex(symbols)
                current = prices.iloc[current_position].reindex(symbols)
                values = (
                    current.div(previous)
                    .sub(1)
                    .mul(100)
                    .replace([np.inf, -np.inf], np.nan)
                )
            valid = values.dropna()
            usable = int(valid.size)
            result[f"breadth_{window}d_expected"] = expected
            result[f"breadth_{window}d_usable"] = usable
            result[f"breadth_{window}d_coverage_pct"] = (
                round(usable / expected * 100, 2) if expected else 0.0
            )
            result[f"breadth_{window}d_positive_pct"] = (
                round((valid > 0).mean() * 100, 2) if usable else None
            )
            if window == 5:
                returns_for_top = valid.sort_values(ascending=False)
        result["top_constituents_json"] = json.dumps(
            [
                {"symbol": str(symbol), "return_5d_pct": round(float(value), 2)}
                for symbol, value in (
                    returns_for_top.head(5).items()
                    if returns_for_top is not None
                    else []
                )
            ],
            separators=(",", ":"),
        )
        result["lagging_constituents_json"] = json.dumps(
            [
                {"symbol": str(symbol), "return_5d_pct": round(float(value), 2)}
                for symbol, value in (
                    returns_for_top.tail(5).sort_values().items()
                    if returns_for_top is not None
                    else []
                )
            ],
            separators=(",", ":"),
        )
        return result

    @staticmethod
    def _persistence_state(
        history: pd.DataFrame, sector: str, total_sectors: int
    ) -> tuple[str, int, float]:
        subset = history[
            (history["sector"] == sector) & history["relative_strength_rank_5d"].notna()
        ].sort_values("date")
        observations = len(subset)
        if observations < 3:
            return "INSUFFICIENT_HISTORY", observations, 0.0
        rank = subset["relative_strength_rank_5d"]
        top_cutoff = max(1, int(np.ceil(total_sectors * 0.4)))
        bottom_cutoff = max(top_cutoff, int(np.floor(total_sectors * 0.6)))
        top_rate = float((rank <= top_cutoff).mean())
        bottom_rate = float((rank > bottom_cutoff).mean())
        current_rank = _finite(rank.iloc[-1], None)
        if current_rank is not None and current_rank <= top_cutoff and top_rate >= 0.6:
            return "PERSISTENT_LEADER", observations, round(top_rate * 100, 2)
        if (
            current_rank is not None
            and current_rank > bottom_cutoff
            and bottom_rate >= 0.6
        ):
            return "PERSISTENT_LAGGARD", observations, round((1 - bottom_rate) * 100, 2)
        return "MIXED", observations, round(top_rate * 100, 2)

    def _build_snapshot(
        self,
        *,
        price_history: pd.DataFrame,
        prices: pd.DataFrame,
        sector_map: dict[str, str],
        flow_scores: pd.DataFrame,
        fpi_map: dict[str, float],
        fpi_date: str | None,
        institutional_date: str | None,
        legacy_price_map: dict[str, float],
        legacy_index_date: str | None,
        benchmark_symbols: set[str],
    ) -> pd.DataFrame:
        latest_price_date = str(price_history["date"].max())
        current = price_history[price_history["date"] == latest_price_date].copy()
        if not flow_scores.empty:
            flow_latest = flow_scores[flow_scores["date"] == institutional_date].copy()
            # ``date`` is already the price as-of field in the snapshot.  The
            # participant date is retained explicitly as institutional_as_of;
            # do not leak a confusing pandas ``date_flow`` compatibility field.
            flow_latest = flow_latest.drop(columns=["date"], errors="ignore")
            current = current.merge(
                flow_latest, on="sector", how="left", suffixes=("", "_flow")
            )
        for column in (
            "FII_flow_score",
            "DII_flow_score",
            "FII_rolling_5d",
            "DII_rolling_5d",
        ):
            if column not in current:
                current[column] = np.nan
        current["fpi_score"] = current["sector"].map(fpi_map)
        current["nse_index"] = (
            current["sector"]
            .map({value: key for key, value in NSE_TO_PLATFORM.items()})
            .fillna("")
        )
        current["legacy_index_momentum_score"] = current["sector"].map(legacy_price_map)
        current["price_momentum_score"] = current["legacy_index_momentum_score"]
        fii = pd.to_numeric(current.get("FII_flow_score"), errors="coerce")
        fpi = pd.to_numeric(current["fpi_score"], errors="coerce")
        price = pd.to_numeric(current["price_momentum_score"], errors="coerce")
        current["combined_score"] = (
            fii.fillna(0) * 0.40
            + fpi.fillna(0) * 0.35
            + price.fillna(0).clip(-10, 10) / 10 * 100 * 0.25
        ).round(2)
        current["rotation_signal"] = [
            self._legacy_rotation_signal(flow, score) for flow, score in zip(fpi, price)
        ]
        current["capital_flow_alignment"] = [
            "UNKNOWN"
            if pd.isna(flow) or pd.isna(score)
            else ("ALIGNED" if (flow > 0) == (score > 0) else "DIVERGENT")
            for flow, score in zip(fii, price)
        ]
        current["price_rank"] = price.rank(ascending=False, method="min")
        current["combined_rank"] = current["combined_score"].rank(
            ascending=False, method="min"
        )
        current["last_date"] = latest_price_date
        current["relative_strength_score"] = _cross_sectional_score(
            current["relative_return_5d"]
        )
        breadth_rows = []
        for _, row in current.iterrows():
            breadth_rows.append(
                self._breadth(
                    prices,
                    sector_map,
                    str(row["sector"]),
                    int(row["constituent_expected"]),
                )
            )
        breadth = pd.DataFrame(breadth_rows, index=current.index)
        current = pd.concat([current, breadth], axis=1)
        current["breadth_5d_score"] = (
            pd.to_numeric(current["breadth_5d_positive_pct"], errors="coerce")
            .sub(50)
            .mul(2)
            .round(2)
        )
        current["leadership_score"] = (
            current["relative_strength_score"] * 0.60
            + current["breadth_5d_score"] * 0.40
        ).round(2)
        current["sector_price_as_of"] = latest_price_date
        current["benchmark_price_as_of"] = (
            latest_price_date if benchmark_symbols else None
        )
        current["institutional_as_of"] = institutional_date
        current["fpi_as_of"] = fpi_date
        current["date_alignment_state"] = (
            "ALIGNED"
            if institutional_date in {None, latest_price_date}
            else "PARTIALLY_ALIGNED"
        )
        current["institutional_context_scope"] = INSTITUTIONAL_CONTEXT_SCOPE
        current["institutional_evidence_type"] = INSTITUTIONAL_EVIDENCE_TYPE
        current["benchmark"] = "NIFTY 50 equal-weight constituent return proxy"
        current["taxonomy"] = "company_classification_v4 / platform sector taxonomy"
        current["constituent_universe"] = "CURRENT_CONSTITUENT_UNIVERSE"
        current["contract_version"] = SECTOR_CONTRACT_VERSION
        current["legacy_index_as_of"] = legacy_index_date

        total_sectors = len(current)
        states, persistence_states, observation_counts, persistence_rates = (
            [],
            [],
            [],
            [],
        )
        acceleration_states, limitations, facts, signals, interpretations = (
            [],
            [],
            [],
            [],
            [],
        )
        for _, row in current.iterrows():
            sector = str(row["sector"])
            persistence, observations, persistence_rate = self._persistence_state(
                price_history, sector, total_sectors
            )
            rank_change, rel5, rel20 = (
                _finite(row.get("rank_change_5d")),
                _finite(row.get("relative_return_5d")),
                _finite(row.get("relative_return_20d")),
            )
            acceleration = (
                round(rel5 - rel20 / 4, 4)
                if rel5 is not None and rel20 is not None
                else None
            )
            acceleration_state = (
                "ACCELERATING"
                if acceleration is not None and acceleration > 0.5
                else "DECELERATING"
                if acceleration is not None and acceleration < -0.5
                else "STABLE"
                if acceleration is not None
                else "UNAVAILABLE"
            )
            if observations < 3:
                state = "INSUFFICIENT_HISTORY"
            elif rank_change is not None and rank_change >= 2 and (rel5 or 0) > 0:
                state = "IMPROVING"
            elif rank_change is not None and rank_change <= -2:
                state = "WEAKENING"
            elif persistence == "PERSISTENT_LEADER":
                state = "LEADING"
            elif persistence == "PERSISTENT_LAGGARD":
                state = "LAGGING"
            else:
                state = "MIXED"
            states.append(state)
            persistence_states.append(persistence)
            observation_counts.append(observations)
            persistence_rates.append(persistence_rate)
            acceleration_states.append(acceleration_state)
            coverage = _finite(row.get("breadth_5d_coverage_pct"), 0.0) or 0.0
            row_limitations = [
                "Historical membership snapshots are unavailable; breadth uses CURRENT_CONSTITUENT_UNIVERSE.",
                "Institutional participant values are market-level weighted context, not sector-specific FII/DII attribution.",
                "Sector returns and breadth are equal-weight constituent calculations; official index weights are not used.",
            ]
            if coverage < 90:
                row_limitations.append(
                    f"5D constituent breadth coverage is {coverage:.1f}%."
                )
            if institutional_date and institutional_date != latest_price_date:
                row_limitations.append(
                    f"Institutional context is dated {institutional_date}; constituent prices are dated {latest_price_date}."
                )
            limitations.append(json.dumps(row_limitations, separators=(",", ":")))
            facts.append(
                json.dumps(
                    {
                        "sector_return_1d_pct": _finite(row.get("sector_return_1d")),
                        "sector_return_5d_pct": _finite(row.get("sector_return_5d")),
                        "sector_return_20d_pct": _finite(row.get("sector_return_20d")),
                        "benchmark_return_5d_pct": _finite(
                            row.get("benchmark_return_5d")
                        ),
                        "relative_return_5d_pct": rel5,
                        "relative_return_20d_pct": rel20,
                    },
                    separators=(",", ":"),
                )
            )
            signals.append(
                json.dumps(
                    {
                        "relative_strength_score": _finite(
                            row.get("relative_strength_score")
                        ),
                        "breadth_5d_positive_pct": _finite(
                            row.get("breadth_5d_positive_pct")
                        ),
                        "relative_strength_rank_5d": _finite(
                            row.get("relative_strength_rank_5d")
                        ),
                        "rank_change_5d": rank_change,
                        "persistence_state": persistence,
                        "acceleration_state": acceleration_state,
                    },
                    separators=(",", ":"),
                )
            )
            interpretations.append(
                f"{sector} is {state.lower().replace('_', ' ')} on current relative performance, breadth and bounded history; this is not a forecast."
            )
        current["leadership_state"] = states
        current["persistence_state"] = persistence_states
        current["persistence_observations"] = observation_counts
        current["persistence_top_band_rate_pct"] = persistence_rates
        current["acceleration_state"] = acceleration_states
        current["rotation_state"] = states
        current["evidence_quality"] = current.apply(self._quality_state, axis=1)
        current["facts_json"] = facts
        current["signals_json"] = signals
        current["interpretation"] = interpretations
        current["limitations_json"] = limitations
        current["leaders_json"] = current["top_constituents_json"]
        current["laggards_json"] = current["lagging_constituents_json"]
        return current.sort_values("combined_rank", na_position="last").reset_index(
            drop=True
        )

    @staticmethod
    def _quality_state(row: pd.Series) -> str:
        coverage = _finite(row.get("breadth_5d_coverage_pct"), 0.0) or 0.0
        twenty = _finite(row.get("relative_return_20d"), None)
        benchmark = _finite(row.get("benchmark_usable"), 0.0) or 0.0
        if coverage >= 90 and twenty is not None and benchmark > 0:
            return "MEDIUM"
        if coverage >= 60 and benchmark > 0:
            return "LIMITED"
        return "INSUFFICIENT"

    @staticmethod
    def _build_history_output(
        price_history: pd.DataFrame, flow_scores: pd.DataFrame
    ) -> pd.DataFrame:
        history = price_history.copy()
        if not flow_scores.empty:
            keep = [
                c
                for c in [
                    "date",
                    "sector",
                    "FII_flow_score",
                    "DII_flow_score",
                    "PRO_flow_score",
                    "CLIENT_flow_score",
                    "Smart_Money_Score",
                    "Retail_Score",
                ]
                if c in flow_scores.columns
            ]
            history = history.merge(
                flow_scores[keep], on=["date", "sector"], how="left"
            )
        history["contract_version"] = SECTOR_CONTRACT_VERSION
        history["institutional_context_scope"] = INSTITUTIONAL_CONTEXT_SCOPE
        history["constituent_universe"] = "CURRENT_CONSTITUENT_UNIVERSE"
        return history.sort_values(["date", "sector"]).reset_index(drop=True)

    @staticmethod
    def _legacy_rotation_signal(flow_score: object, price_score: object) -> str:
        flow, price = _finite(flow_score), _finite(price_score)
        if flow is None or price is None:
            return "NEUTRAL"
        if flow > 15 and price > 0:
            return "STRONG_ACCUMULATION"
        if flow > 15 and price < 0:
            return "EARLY_ROTATION"
        if flow < -15 and price < 0:
            return "DISTRIBUTION"
        if flow < -15 and price > 0:
            return "PRICE_LED"
        return "NEUTRAL"

    @staticmethod
    def _save_atomic(df: pd.DataFrame, path: Path) -> None:
        if df.empty:
            raise ValueError(f"G-D-03: refusing to write empty {path.name}")
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))
        logger.info(
            "[6C] Saved: %s (%d rows, %d cols)", path.name, len(df), len(df.columns)
        )

    @staticmethod
    def _print_summary(snapshot: pd.DataFrame) -> None:
        print()
        print("=" * 78)
        print("SECTOR ROTATION INTELLIGENCE ENGINE -- PHASE 6C HARDENED")
        print("=" * 78)
        print(f"Contract      : {SECTOR_CONTRACT_VERSION}")
        print(f"Price as-of   : {snapshot['sector_price_as_of'].iloc[0]}")
        print(f"Sectors       : {len(snapshot)}")
        print("Top leadership:")
        for _, row in (
            snapshot.sort_values("leadership_score", ascending=False).head(5).iterrows()
        ):
            print(
                f"  {row['sector']:22s} {row['leadership_state']:22s} score={row['leadership_score']}"
            )
        print("=" * 78)


if __name__ == "__main__":
    SectorRotationIntelligenceEngine().run()
