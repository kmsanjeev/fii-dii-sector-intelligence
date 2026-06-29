"""
Participant Acquisition Engine
Phase 5A — Incremental downloader for all participant data sources

Downloads:
  F&O data    : participant_wise_open_interest, participant_wise_trading_volume,
                fii_derivatives_statistics (nselib.derivatives)
  Cash market : category_turnover_cash (nselib.capital_market)

Updates (incremental — only missing dates):
  data/historical/institutional/institutional_positioning_history.csv  (F&O)
  data/historical/institutional/cash_market_flows_history.csv          (cash)

Guardrails: G-A-01 (rate limit), G-A-02 (retry+backoff), G-A-03 (recovery queue),
            G-D-02 (atomic writes), G-D-03 (no empty writes)
"""

import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger("participant_acquisition")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HISTORICAL_DIR = ROOT / "data" / "historical" / "institutional"
FNO_HISTORY = HISTORICAL_DIR / "institutional_positioning_history.csv"
CASH_HISTORY = HISTORICAL_DIR / "cash_market_flows_history.csv"
RECOVERY_QUEUE = HISTORICAL_DIR / "participant_recovery_queue.csv"

# Pre-2016 F&O participant data is not available (ADR-016 guardrail)
FNO_MIN_DATE = "2016-01-01"
# Cash market history: start from 2024 (NSE archives depth)
CASH_MIN_DATE = "2024-01-01"

# F&O output schema (matches existing institutional_positioning_history.csv)
FNO_SCHEMA = [
    "Date",
    "FII_OI_Net", "DII_OI_Net", "PRO_OI_Net", "CLIENT_OI_Net",
    "FII_Volume_Net", "DII_Volume_Net", "PRO_Volume_Net", "CLIENT_Volume_Net",
    "FII_Derivatives_Net",
    "FII_OI_Score", "DII_OI_Score", "PRO_OI_Score", "CLIENT_OI_Score",
    "FII_Volume_Score", "DII_Volume_Score", "PRO_Volume_Score", "CLIENT_Volume_Score",
    "FII_Derivatives_Score",
    "Institutional_Score", "Regime",
]

CASH_SCHEMA = [
    "date",
    "FPI_buy_cr", "FPI_sell_cr", "FPI_net_cr",
    "MF_buy_cr", "MF_sell_cr", "MF_net_cr",
    "INSURANCE_buy_cr", "INSURANCE_sell_cr", "INSURANCE_net_cr",
    "RETAIL_buy_cr", "RETAIL_sell_cr", "RETAIL_net_cr",
    "OTHERS_buy_cr", "OTHERS_sell_cr", "OTHERS_net_cr",
]

# nselib category → platform label
CASH_CATEGORY_MAP = {
    "FPI": "FPI",
    "Mutual Funds": "MF",
    "Insurance Companies": "INSURANCE",
    "RETAIL": "RETAIL",
    "OTHERS": "OTHERS",
    "Bank": "BANK",
    "AIF": "AIF",
    "PMS": "PMS",
}


def _safe_float(value) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return 0.0


def _net_futures(row: pd.Series) -> float:
    """Futures-only net long = (Index Long + Stock Long) - (Index Short + Stock Short)."""
    row.index = row.index.astype(str).str.strip()
    return (
        _safe_float(row.get("Future Index Long", 0))
        + _safe_float(row.get("Future Stock Long", 0))
        - _safe_float(row.get("Future Index Short", 0))
        - _safe_float(row.get("Future Stock Short", 0))
    )


def _institutional_score(fii_oi, dii_oi, pro_oi, fii_vol, dii_vol, pro_vol, fii_deriv) -> float:
    return round(
        fii_oi * 0.35 + dii_oi * 0.20 + pro_oi * 0.15
        + fii_vol * 0.15 + dii_vol * 0.05 + pro_vol * 0.05
        + fii_deriv * 0.05,
        2,
    )


def _regime(score: float) -> str:
    if score > 0:
        return "ACCUMULATION"
    if score < 0:
        return "DISTRIBUTION"
    return "NEUTRAL"


def _weekdays_between(start: str, end: str):
    """Return Mon–Fri dates between start and end (inclusive), as 'YYYY-MM-DD' strings."""
    d = datetime.strptime(start, "%Y-%m-%d")
    end_d = datetime.strptime(end, "%Y-%m-%d")
    while d <= end_d:
        if d.weekday() < 5:  # Mon=0 … Fri=4
            yield d.strftime("%Y-%m-%d")
        d += timedelta(days=1)


def _to_nse_fmt(date_str: str) -> str:
    """'2026-06-16' → '16-06-2026'"""
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%m-%Y")


class ParticipantAcquisitionEngine:
    """
    Phase 5A — Incremental downloader for F&O and cash market participant data.

    Run daily (after 18:00 IST per G-A-04) to keep both history files current.
    First run downloads from CASH_MIN_DATE for cash (F&O from FNO_MIN_DATE already exists).
    """

    def __init__(self):
        HISTORICAL_DIR.mkdir(parents=True, exist_ok=True)
        self.failed_dates = []

    def run(self) -> bool:
        logger.info("[ParticipantAcquisition] Starting Phase 5A")
        try:
            fno_updated = self._update_fno_history()
            cash_updated = self._update_cash_history()
            if self.failed_dates:
                self._save_recovery_queue()
            self._print_summary(fno_updated, cash_updated)
            return True
        except Exception as exc:
            logger.error("[ParticipantAcquisition] Failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # F&O history update
    # ------------------------------------------------------------------
    def _update_fno_history(self) -> int:
        from nselib import derivatives

        existing = self._load_existing(FNO_HISTORY, date_col="Date")
        last_date = existing["Date"].max() if not existing.empty else FNO_MIN_DATE
        today = datetime.now().strftime("%Y-%m-%d")
        missing_dates = [
            d for d in _weekdays_between(last_date, today)
            if d > last_date and d <= today
        ]

        if not missing_dates:
            logger.info("[5A] F&O history is current (%s)", last_date)
            return 0

        logger.info("[5A] Downloading F&O data for %d dates (from %s to %s)",
                    len(missing_dates), missing_dates[0], missing_dates[-1])

        new_rows = []
        for date_str in missing_dates:
            nse_fmt = _to_nse_fmt(date_str)
            row = self._fetch_fno_day(derivatives, date_str, nse_fmt)
            if row:
                new_rows.append(row)
            time.sleep(cfg.API_DELAY)

        if not new_rows:
            logger.info("[5A] No new F&O rows added (all dates were holidays or unavailable)")
            return 0

        new_df = pd.DataFrame(new_rows)[FNO_SCHEMA]
        updated = pd.concat([existing, new_df], ignore_index=True)
        updated = updated.drop_duplicates(subset=["Date"]).sort_values("Date").reset_index(drop=True)
        self._save_atomic(updated, FNO_HISTORY)
        logger.info("[5A] F&O history updated: +%d rows → %d total", len(new_rows), len(updated))
        return len(new_rows)

    def _fetch_fno_day(self, derivatives, date_str: str, nse_fmt: str) -> dict | None:
        """Fetch one day's F&O participant data. Returns None if holiday / data unavailable."""
        for attempt in range(1, cfg.MAX_RETRIES + 1):
            try:
                oi_df = derivatives.participant_wise_open_interest(trade_date=nse_fmt)
                vol_df = derivatives.participant_wise_trading_volume(trade_date=nse_fmt)
                fii_deriv_df = derivatives.fii_derivatives_statistics(trade_date=nse_fmt)
                break
            except Exception as exc:
                msg = str(exc).lower()
                if any(kw in msg for kw in ["no data", "not found", "nse", "404"]):
                    return None  # holiday or data not yet available
                if attempt < cfg.MAX_RETRIES:
                    time.sleep(cfg.RETRY_DELAY * attempt)
                else:
                    logger.warning("[5A] F&O %s failed after %d attempts: %s", date_str, attempt, exc)
                    self.failed_dates.append({"date": date_str, "source": "fno", "error": str(exc)})
                    return None

        # Strip column names (nselib returns some with trailing spaces)
        for df in (oi_df, vol_df, fii_deriv_df):
            df.columns = df.columns.astype(str).str.strip()

        def _participant(df, label):
            rows = df[df["Client Type"].astype(str).str.strip() == label]
            return rows.iloc[0] if not rows.empty else pd.Series(dtype=float)

        fii_oi   = _participant(oi_df, "FII")
        dii_oi   = _participant(oi_df, "DII")
        pro_oi   = _participant(oi_df, "Pro")
        client_oi = _participant(oi_df, "Client")
        fii_vol  = _participant(vol_df, "FII")
        dii_vol  = _participant(vol_df, "DII")
        pro_vol  = _participant(vol_df, "Pro")
        client_vol = _participant(vol_df, "Client")

        fii_oi_net     = _net_futures(fii_oi)
        dii_oi_net     = _net_futures(dii_oi)
        pro_oi_net     = _net_futures(pro_oi)
        client_oi_net  = _net_futures(client_oi)
        fii_vol_net    = _net_futures(fii_vol)
        dii_vol_net    = _net_futures(dii_vol)
        pro_vol_net    = _net_futures(pro_vol)
        client_vol_net = _net_futures(client_vol)

        futures_mask = fii_deriv_df["fii_derivatives"].astype(str).str.upper().str.contains("FUTURES", na=False)
        fii_deriv_net = (
            _safe_float(fii_deriv_df.loc[futures_mask, "buy_contracts"].sum())
            - _safe_float(fii_deriv_df.loc[futures_mask, "sell_contracts"].sum())
        )

        inst_score = _institutional_score(
            fii_oi_net, dii_oi_net, pro_oi_net,
            fii_vol_net, dii_vol_net, pro_vol_net,
            fii_deriv_net,
        )

        return {
            "Date": date_str,
            "FII_OI_Net": fii_oi_net, "DII_OI_Net": dii_oi_net,
            "PRO_OI_Net": pro_oi_net, "CLIENT_OI_Net": client_oi_net,
            "FII_Volume_Net": fii_vol_net, "DII_Volume_Net": dii_vol_net,
            "PRO_Volume_Net": pro_vol_net, "CLIENT_Volume_Net": client_vol_net,
            "FII_Derivatives_Net": fii_deriv_net,
            # Score cols = same raw values (backward compat with Phase 7)
            "FII_OI_Score": fii_oi_net, "DII_OI_Score": dii_oi_net,
            "PRO_OI_Score": pro_oi_net, "CLIENT_OI_Score": client_oi_net,
            "FII_Volume_Score": fii_vol_net, "DII_Volume_Score": dii_vol_net,
            "PRO_Volume_Score": pro_vol_net, "CLIENT_Volume_Score": client_vol_net,
            "FII_Derivatives_Score": fii_deriv_net,
            "Institutional_Score": inst_score,
            "Regime": _regime(inst_score),
        }

    # ------------------------------------------------------------------
    # Cash market history update
    # ------------------------------------------------------------------
    def _update_cash_history(self) -> int:
        from nselib import capital_market

        existing = self._load_existing(CASH_HISTORY, date_col="date")
        last_date = existing["date"].max() if not existing.empty else ""
        start_date = CASH_MIN_DATE if not last_date else last_date
        today = datetime.now().strftime("%Y-%m-%d")

        missing_dates = [
            d for d in _weekdays_between(start_date, today)
            if d > last_date and d <= today
        ]

        if not missing_dates:
            logger.info("[5A] Cash history is current (%s)", last_date or CASH_MIN_DATE)
            return 0

        logger.info("[5A] Downloading cash market data for %d dates (from %s to %s)",
                    len(missing_dates), missing_dates[0], missing_dates[-1])

        new_rows = []
        for date_str in missing_dates:
            nse_fmt = _to_nse_fmt(date_str)
            row = self._fetch_cash_day(capital_market, date_str, nse_fmt)
            if row:
                new_rows.append(row)
            time.sleep(cfg.API_DELAY)

        if not new_rows:
            logger.info("[5A] No new cash rows added")
            return 0

        new_df = pd.DataFrame(new_rows)
        for col in CASH_SCHEMA:
            if col not in new_df.columns:
                new_df[col] = 0.0

        updated = pd.concat([existing, new_df[CASH_SCHEMA]], ignore_index=True)
        updated = updated.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
        self._save_atomic(updated, CASH_HISTORY)
        logger.info("[5A] Cash history updated: +%d rows → %d total", len(new_rows), len(updated))
        return len(new_rows)

    def _fetch_cash_day(self, capital_market, date_str: str, nse_fmt: str) -> dict | None:
        for attempt in range(1, cfg.MAX_RETRIES + 1):
            try:
                df = capital_market.category_turnover_cash(trade_date=nse_fmt)
                if df is None or df.empty:
                    return None
                break
            except Exception as exc:
                msg = str(exc).lower()
                if any(kw in msg for kw in ["no data", "not found", "404", "available"]):
                    return None
                if attempt < cfg.MAX_RETRIES:
                    time.sleep(cfg.RETRY_DELAY * attempt)
                else:
                    logger.warning("[5A] Cash %s failed: %s", date_str, exc)
                    self.failed_dates.append({"date": date_str, "source": "cash", "error": str(exc)})
                    return None

        df.columns = df.columns.astype(str).str.strip()
        if "Category" not in df.columns:
            return None

        row = {"date": date_str}
        for _, r in df.iterrows():
            cat_raw = str(r.get("Category", "")).strip()
            label = CASH_CATEGORY_MAP.get(cat_raw, "")
            if not label:
                continue
            buy  = _safe_float(r.get("Buy Value in Rs.Crores", 0))
            sell = _safe_float(r.get("Sell Value in Rs.Crores", 0))
            net  = _safe_float(r.get("Net Value in Rs.Crores", buy - sell))
            row[f"{label}_buy_cr"]  = buy
            row[f"{label}_sell_cr"] = sell
            row[f"{label}_net_cr"]  = net

        return row if len(row) > 1 else None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _load_existing(self, path: Path, date_col: str) -> pd.DataFrame:
        if not path.exists():
            return pd.DataFrame()
        df = pd.read_csv(path, dtype=str).fillna("")
        if date_col not in df.columns:
            return pd.DataFrame()
        return df

    def _save_atomic(self, df: pd.DataFrame, path: Path):
        if df.empty:
            raise ValueError(f"G-D-03: refusing to write empty DataFrame to {path.name}")
        tmp = path.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(path))

    def _save_recovery_queue(self):
        df = pd.DataFrame(self.failed_dates)
        df["flagged_date"] = datetime.now().strftime("%Y-%m-%d")
        tmp = RECOVERY_QUEUE.with_suffix(".tmp")
        df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(RECOVERY_QUEUE))
        logger.warning("[5A] Recovery queue: %d entries → %s", len(df), RECOVERY_QUEUE)

    def _print_summary(self, fno_added: int, cash_added: int):
        print()
        print("=" * 60)
        print("PARTICIPANT ACQUISITION ENGINE — PHASE 5A COMPLETE")
        print("=" * 60)
        print(f"F&O rows added    : {fno_added}")
        print(f"Cash rows added   : {cash_added}")
        print(f"Failed dates      : {len(self.failed_dates)}")
        print("=" * 60)


if __name__ == "__main__":
    engine = ParticipantAcquisitionEngine()
    engine.run()
