"""
Insider Trade Intelligence Engine — Phase F
Fetches NSE PIT (Prohibition of Insider Trading) disclosures for all F&O stocks,
computes 30-day net buy/sell conviction per symbol.

Source: NSE API  /api/corporates-pit?symbol=X&from_date=DD-MM-YYYY&to_date=DD-MM-YYYY
        Filters to Promoter, Director, KMP transactions only.

Run:
    py -3.11 engines/intelligence/insider_trade_engine.py

Outputs:
    data/intelligence/insider_trades.csv    — raw transaction rows (rolling 90D)
    data/intelligence/insider_signals.csv   — 30D aggregated conviction per symbol

Guardrails: G-D-02 atomic writes, G-A-01 rate limiting, G-A-02 retry+backoff
"""

import shutil
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

TRADES_PATH  = cfg.INTELLIGENCE_DIR / "insider_trades.csv"
SIGNALS_PATH = cfg.INTELLIGENCE_DIR / "insider_signals.csv"

LOOKBACK_DAYS  = 90
SIGNAL_DAYS    = 30
API_DELAY      = cfg.API_DELAY        # 1.0s between requests
MAX_RETRIES    = cfg.MAX_RETRIES      # 3
RETRY_DELAY    = cfg.RETRY_DELAY      # 3s

# Only trust these person categories as informed-insider signals
HIGH_CONVICTION_CATEGORIES = {
    "promoter", "promoter group", "director", "key managerial personnel",
    "managing director", "whole time director", "chairperson", "ceo", "cfo", "coo",
}

NSE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.nseindia.com/",
}


class InsiderTradeEngine:

    def __init__(self):
        self._session: requests.Session | None = None

    def _get_session(self) -> requests.Session:
        if self._session is None:
            s = requests.Session()
            s.headers.update(NSE_HEADERS)
            s.get("https://www.nseindia.com", timeout=15)
            time.sleep(1.0)
            self._session = s
        return self._session

    def _fetch_pit(self, symbol: str, from_dt: str, to_dt: str) -> list[dict]:
        url = (
            f"https://www.nseindia.com/api/corporates-pit"
            f"?symbol={symbol}&from_date={from_dt}&to_date={to_dt}"
        )
        for attempt in range(MAX_RETRIES):
            try:
                r = self._get_session().get(url, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    return data.get("data", []) if isinstance(data, dict) else []
                elif r.status_code == 429:
                    logger.warning(f"[InsiderTrade] Rate limited on {symbol}, sleeping 10s")
                    time.sleep(10)
                else:
                    logger.debug(f"[InsiderTrade] {symbol}: HTTP {r.status_code}")
                    return []
            except requests.RequestException as e:
                wait = RETRY_DELAY * (2 ** attempt)
                logger.warning(f"[InsiderTrade] {symbol} attempt {attempt+1}: {e} — retry in {wait}s")
                time.sleep(wait)
                self._session = None  # reset session on connection error
        return []

    def _is_high_conviction(self, row: dict) -> bool:
        cat = str(row.get("personCategory", "")).lower().strip()
        return any(hc in cat for hc in HIGH_CONVICTION_CATEGORIES)

    def _parse_value(self, v) -> float:
        try:
            return float(str(v).replace(",", "")) if v else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _parse_date(self, raw: str) -> str:
        for fmt in ("%d-%b-%Y", "%d-%m-%Y", "%Y-%m-%d", "%d-%b-%Y %H:%M"):
            try:
                return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
            except (ValueError, AttributeError):
                continue
        return raw[:10] if raw else ""

    def run(self):
        logger.info("[InsiderTrade] Starting Phase F insider trade intelligence engine")

        # Load F&O universe (most liquid, most relevant for insider activity)
        fno_path = cfg.INTELLIGENCE_DIR / "fno_intelligence.csv"
        bull_path = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"

        symbols: list[str] = []
        if fno_path.exists():
            fno_df = pd.read_csv(fno_path)
            symbols = fno_df["symbol"].str.upper().dropna().unique().tolist()
            logger.info(f"[InsiderTrade] F&O universe: {len(symbols)} symbols")
        elif bull_path.exists():
            bull_df = pd.read_csv(bull_path)
            # Take top 300 by score for cost/time efficiency
            symbols = (
                bull_df.nlargest(300, "bull_run_score")["symbol"]
                .str.upper().dropna().unique().tolist()
            )
            logger.info(f"[InsiderTrade] Bull-run top-300 fallback: {len(symbols)} symbols")

        if not symbols:
            logger.error("[InsiderTrade] No symbol universe found")
            return None

        # Date range
        to_dt   = date.today()
        from_dt = to_dt - timedelta(days=LOOKBACK_DAYS)
        from_str = from_dt.strftime("%d-%m-%Y")
        to_str   = to_dt.strftime("%d-%m-%Y")
        logger.info(f"[InsiderTrade] Fetching {from_str} → {to_str} for {len(symbols)} symbols")

        rows = []
        skipped = 0
        for i, symbol in enumerate(symbols):
            data = self._fetch_pit(symbol, from_str, to_str)
            time.sleep(API_DELAY)

            for rec in data:
                if not self._is_high_conviction(rec):
                    continue
                buy_val  = self._parse_value(rec.get("buyValue",  0))
                sell_val = self._parse_value(rec.get("sellValue", 0))
                if buy_val == 0 and sell_val == 0:
                    continue

                rows.append({
                    "symbol":          symbol,
                    "date":            self._parse_date(str(rec.get("intimDt", ""))),
                    "acq_name":        str(rec.get("acqName", ""))[:80],
                    "person_category": str(rec.get("personCategory", ""))[:50],
                    "buy_qty":         self._parse_value(rec.get("buyQuantity", 0)),
                    "buy_value_cr":    round(buy_val / 1e7, 4),   # rupees → crores
                    "sell_qty":        self._parse_value(rec.get("sellquantity", rec.get("sellQuantity", 0))),
                    "sell_value_cr":   round(sell_val / 1e7, 4),
                    "after_shares_pct": self._parse_value(rec.get("afterAcqSharesPer", 0)),
                    "sec_type":        str(rec.get("secType", "Equity"))[:30],
                    "fetched_at":      datetime.now().strftime("%Y-%m-%d"),
                })

            if (i + 1) % 25 == 0:
                logger.info(f"[InsiderTrade] {i+1}/{len(symbols)} done — {len(rows)} trades so far")

            if data:
                pass
            else:
                skipped += 1

        if not rows:
            logger.warning("[InsiderTrade] No insider transactions found in universe")
            print("[InsiderTrade] No insider transactions found")
            return None

        trades_df = pd.DataFrame(rows)
        trades_df = trades_df[trades_df["date"] != ""].copy()
        trades_df["date"] = pd.to_datetime(trades_df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        trades_df = trades_df.dropna(subset=["date"])

        # Atomic write
        tmp = TRADES_PATH.with_suffix(".tmp")
        trades_df.to_csv(tmp, index=False)
        shutil.move(str(tmp), str(TRADES_PATH))
        logger.info(f"[InsiderTrade] Wrote {len(trades_df)} trades to {TRADES_PATH}")

        # ── 30D conviction signals ──────────────────────────────────────────────
        cutoff_30d = (date.today() - timedelta(days=SIGNAL_DAYS)).strftime("%Y-%m-%d")
        recent = trades_df[trades_df["date"] >= cutoff_30d].copy()

        if recent.empty:
            logger.warning("[InsiderTrade] No trades in last 30 days for signals")
            return trades_df

        signals = (
            recent.groupby("symbol")
            .agg(
                buy_value_30d_cr  = ("buy_value_cr",  "sum"),
                sell_value_30d_cr = ("sell_value_cr", "sum"),
                buy_count_30d     = ("buy_qty",        lambda x: (x > 0).sum()),
                sell_count_30d    = ("sell_qty",       lambda x: (x > 0).sum()),
                latest_date       = ("date",            "max"),
                acquirers         = ("acq_name",       lambda x: "|".join(x.unique()[:3])),
            )
            .reset_index()
        )

        signals["net_value_30d_cr"] = signals["buy_value_30d_cr"] - signals["sell_value_30d_cr"]

        def _conviction(row) -> str:
            net = row["net_value_30d_cr"]
            if net > 5:    return "STRONG_BUY"
            if net > 1:    return "BUY"
            if net > 0:    return "MILD_BUY"
            if net > -1:   return "MILD_SELL"
            if net > -5:   return "SELL"
            return "STRONG_SELL"

        signals["insider_conviction"]  = signals.apply(_conviction, axis=1)
        signals["insider_score"]       = signals["net_value_30d_cr"].clip(-20, 20)
        signals["as_of_date"]          = date.today().strftime("%Y-%m-%d")

        tmp2 = SIGNALS_PATH.with_suffix(".tmp")
        signals.to_csv(tmp2, index=False)
        shutil.move(str(tmp2), str(SIGNALS_PATH))

        # Summary
        buy_syms  = (signals["net_value_30d_cr"] > 0).sum()
        sell_syms = (signals["net_value_30d_cr"] < 0).sum()
        print(f"\n[InsiderTrade] Phase F insider trade intelligence complete")
        print(f"  Symbols scanned    : {len(symbols)}")
        print(f"  Trades found (90D) : {len(trades_df)}")
        print(f"  Symbols with signal: {len(signals)}")
        print(f"  Net buyers (30D)   : {buy_syms}")
        print(f"  Net sellers (30D)  : {sell_syms}")
        print()
        print("  Top insider BUYS (30D net Cr):")
        top_buys = signals.nlargest(8, "net_value_30d_cr")[["symbol", "net_value_30d_cr", "insider_conviction"]]
        for _, r in top_buys.iterrows():
            print(f"    {r['symbol']:<15} +{r['net_value_30d_cr']:.2f} Cr  {r['insider_conviction']}")

        logger.info(f"[InsiderTrade] Done — {len(signals)} symbol signals written")
        return signals


if __name__ == "__main__":
    engine = InsiderTradeEngine()
    engine.run()
