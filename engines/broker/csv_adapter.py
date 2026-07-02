"""
CSV Broker Adapter -- Phase 22
Parses broker-exported holdings/trade CSVs without needing API credentials.

Supports Dhan's export format; also auto-detects common column naming patterns
from Zerodha, HDFC SKY, and generic broker statement exports.

Usage:
    adapter = CsvAdapter(holdings_csv="path/to/holdings.csv")
    holdings = adapter.get_holdings()
"""

import sys
from pathlib import Path
from typing import Optional
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.broker.base import BrokerAdapter, Holding, Position, Trade
from engines.common.logger import get_logger

logger = get_logger(__name__)

# Column name synonyms for each field (tried in order)
_COL_SYMBOL = ["tradingsymbol", "trading symbol", "symbol", "script", "scrip name",
               "script name", "security name", "stock"]
_COL_QTY    = ["totalqty", "total qty", "quantity", "qty", "net quantity", "net qty",
               "balance qty"]
_COL_AVG    = ["avgcostprice", "avg cost price", "avg cost", "average cost",
               "buy average", "purchase price", "average price", "buy avg"]
_COL_LTP    = ["lasttradedprice", "ltp", "current market price", "market price",
               "cmp", "last price", "current price"]
_COL_ISIN   = ["isin"]
_COL_EXCH   = ["exchangesegment", "exchange", "exch"]


def _find_col(df: pd.DataFrame, candidates: list[str]) -> Optional[str]:
    """Return the first candidate column name that exists in df (case-insensitive)."""
    lower_cols = {c.lower().strip(): c for c in df.columns}
    for cand in candidates:
        if cand in lower_cols:
            return lower_cols[cand]
    return None


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip() for c in df.columns]
    return df


class CsvAdapter(BrokerAdapter):

    def __init__(self, holdings_csv: str = "", trades_csv: str = ""):
        self._holdings_path = holdings_csv
        self._trades_path   = trades_csv

    def ping(self) -> bool:
        return bool(self._holdings_path or self._trades_path)

    def get_holdings(self) -> list[Holding]:
        if not self._holdings_path or not Path(self._holdings_path).exists():
            logger.warning("[CSV] Holdings CSV not provided or not found")
            return []

        try:
            df = _clean(pd.read_csv(self._holdings_path, dtype=str))
        except Exception as exc:
            raise RuntimeError(f"Cannot read holdings CSV: {exc}") from exc

        sym_col  = _find_col(df, _COL_SYMBOL)
        qty_col  = _find_col(df, _COL_QTY)
        avg_col  = _find_col(df, _COL_AVG)
        ltp_col  = _find_col(df, _COL_LTP)
        isin_col = _find_col(df, _COL_ISIN)
        exch_col = _find_col(df, _COL_EXCH)

        if not sym_col or not qty_col:
            raise RuntimeError(
                f"Holdings CSV missing required columns. "
                f"Found: {list(df.columns)[:10]}. "
                f"Need at least: symbol + quantity columns."
            )

        holdings = []
        for _, row in df.iterrows():
            sym = str(row.get(sym_col) or "").strip().upper()
            if not sym or sym in ("NAN", "SYMBOL", "TRADING SYMBOL"):
                continue
            try:
                qty  = int(float(str(row.get(qty_col) or 0).replace(",", "")))
                avg  = float(str(row.get(avg_col) or 0).replace(",", "")) if avg_col else 0.0
                ltp  = float(str(row.get(ltp_col) or 0).replace(",", "")) if ltp_col else 0.0
                isin = str(row.get(isin_col) or "") if isin_col else ""
                exch = str(row.get(exch_col) or "NSE") if exch_col else "NSE"
            except (ValueError, TypeError):
                continue

            if qty <= 0:
                continue

            cur = round(ltp * qty, 2)
            cost = round(avg * qty, 2)
            pnl  = round(cur - cost, 2)
            pct  = round(pnl / cost * 100, 2) if cost > 0 else 0.0

            holdings.append(Holding(
                symbol        = sym,
                exchange      = exch.replace("_EQ", "").split("_")[0],
                isin          = isin,
                qty           = qty,
                avg_cost      = round(avg, 2),
                ltp           = round(ltp, 2),
                current_value = cur,
                pnl           = pnl,
                pnl_pct       = pct,
            ))

        logger.info("[CSV] Parsed %d holdings from %s", len(holdings), self._holdings_path)
        return holdings

    def get_positions(self) -> list[Position]:
        return []   # CSV export doesn't carry intraday positions

    def get_trade_history(self, from_date: str, to_date: str) -> list[Trade]:
        if not self._trades_path or not Path(self._trades_path).exists():
            return []

        try:
            df = _clean(pd.read_csv(self._trades_path, dtype=str))
        except Exception as exc:
            raise RuntimeError(f"Cannot read trades CSV: {exc}") from exc

        # Auto-detect columns
        sym_col    = _find_col(df, _COL_SYMBOL)
        qty_col    = _find_col(df, _COL_QTY + ["traded quantity", "trade qty"])
        price_col  = _find_col(df, ["tradedprice", "traded price", "price", "trade price",
                                    "execution price", "avg price"])
        action_col = _find_col(df, ["transactiontype", "transaction type", "action",
                                    "buy/sell", "type", "side"])
        date_col   = _find_col(df, ["exchangetime", "exchange time", "trade date",
                                    "date", "order time", "create time"])

        if not sym_col or not qty_col or not price_col:
            raise RuntimeError(
                f"Trades CSV missing required columns. Found: {list(df.columns)[:10]}"
            )

        trades = []
        for _, row in df.iterrows():
            try:
                sym   = str(row.get(sym_col) or "").strip().upper()
                qty   = int(float(str(row.get(qty_col) or 0).replace(",", "")))
                price = float(str(row.get(price_col) or 0).replace(",", ""))
                if not sym or qty <= 0 or price <= 0:
                    continue

                raw_date = str(row.get(date_col) or "") if date_col else ""
                date_str = raw_date[:10] if len(raw_date) >= 10 else ""
                # Filter by date range
                if date_str and from_date and to_date:
                    if not (from_date <= date_str <= to_date):
                        continue

                raw_action = str(row.get(action_col) or "BUY").upper() if action_col else "BUY"
                action = "SELL" if "SELL" in raw_action or raw_action == "S" else "BUY"

                trades.append(Trade(
                    date     = date_str,
                    symbol   = sym,
                    exchange = "NSE",
                    action   = action,
                    qty      = qty,
                    price    = round(price, 2),
                ))
            except (ValueError, TypeError):
                continue

        logger.info("[CSV] Parsed %d trades from %s", len(trades), self._trades_path)
        return trades
