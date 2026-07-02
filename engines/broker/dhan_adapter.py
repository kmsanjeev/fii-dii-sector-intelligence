"""
Dhan Broker Adapter -- Phase 22
Wraps dhanhq SDK (v2.2.0) for read-only portfolio access.

Auth: dhanhq(client_id, access_token) -- token valid for ~30 days.
Credentials stored in data/portfolio/broker_auth.json (gitignored).

Dhan API docs: https://dhanhq.co/docs/v2/
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.broker.base import BrokerAdapter, Holding, Position, Trade
from engines.common.logger import get_logger

logger = get_logger(__name__)

# Exchange segment normalisation: Dhan uses NSE_EQ / BSE_EQ suffixes
_EXCHANGE_MAP = {
    "NSE_EQ":  "NSE",
    "BSE_EQ":  "BSE",
    "NSE_FNO": "NFO",
    "BSE_FNO": "BFO",
    "MCX_COMM": "MCX",
    "IDX_I":   "NSE",
}


def _exch(raw: str) -> str:
    return _EXCHANGE_MAP.get(str(raw).upper(), str(raw))


def _f(val, default: float = 0.0) -> float:
    try:
        return round(float(val), 2)
    except (TypeError, ValueError):
        return default


def _i(val, default: int = 0) -> int:
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


class DhanAdapter(BrokerAdapter):

    def __init__(self, client_id: str, access_token: str):
        from dhanhq import dhanhq as DhanHQ
        self._client = DhanHQ(str(client_id), str(access_token))
        logger.info("[Dhan] Adapter initialised for client %s", client_id[:4] + "****")

    def ping(self) -> bool:
        """Validate credentials by calling get_fund_limits."""
        try:
            r = self._client.get_fund_limits()
            ok = isinstance(r, dict) and r.get("status") == "success"
            logger.info("[Dhan] ping -> %s", "OK" if ok else "FAIL")
            return ok
        except Exception as exc:
            logger.warning("[Dhan] ping failed: %s", exc)
            return False

    def get_holdings(self) -> list[Holding]:
        """Fetch long-term CNC holdings."""
        r = self._client.get_holdings()
        if not isinstance(r, dict) or r.get("status") != "success":
            raise RuntimeError(f"Dhan get_holdings: {r.get('remarks', 'unknown error') if isinstance(r, dict) else r}")

        holdings = []
        for h in (r.get("data") or []):
            qty  = _i(h.get("totalQty"))
            avg  = _f(h.get("avgCostPrice"))
            ltp  = _f(h.get("lastTradedPrice"))
            cur  = round(ltp * qty, 2)
            cost = round(avg * qty, 2)
            pnl  = round(cur - cost, 2)
            pct  = round(pnl / cost * 100, 2) if cost > 0 else 0.0

            holdings.append(Holding(
                symbol        = str(h.get("tradingSymbol") or ""),
                exchange      = _exch(h.get("exchangeSegment") or "NSE_EQ"),
                isin          = str(h.get("isin") or ""),
                qty           = qty,
                avg_cost      = avg,
                ltp           = ltp,
                current_value = cur,
                pnl           = pnl,
                pnl_pct       = pct,
            ))

        logger.info("[Dhan] get_holdings: %d positions", len(holdings))
        return holdings

    def get_positions(self) -> list[Position]:
        """Fetch open intraday / F&O positions (today only)."""
        r = self._client.get_positions()
        if not isinstance(r, dict) or r.get("status") != "success":
            raise RuntimeError(f"Dhan get_positions: {r.get('remarks', 'unknown error') if isinstance(r, dict) else r}")

        positions = []
        for p in (r.get("data") or []):
            net_qty = _i(p.get("netQty"))
            if net_qty == 0:
                continue
            realized   = _f(p.get("realizedProfit"))
            unrealized = _f(p.get("unrealizedProfit"))
            positions.append(Position(
                symbol   = str(p.get("tradingSymbol") or ""),
                exchange = _exch(p.get("exchangeSegment") or "NSE_EQ"),
                qty      = net_qty,
                avg_cost = _f(p.get("costPrice")),
                ltp      = _f(p.get("lastTradedPrice")),
                pnl      = round(realized + unrealized, 2),
                product  = str(p.get("productType") or "CNC"),
            ))

        logger.info("[Dhan] get_positions: %d open", len(positions))
        return positions

    def get_trade_history(self, from_date: str, to_date: str) -> list[Trade]:
        """
        Fetch executed trades page-by-page.
        Dhan returns up to 50 trades per page; pages indexed from 0.
        """
        all_trades: list[Trade] = []
        page = 0

        while True:
            r = self._client.get_trade_history(from_date, to_date, page)
            if not isinstance(r, dict) or r.get("status") != "success":
                logger.warning("[Dhan] get_trade_history page %d: %s", page,
                               r.get("remarks") if isinstance(r, dict) else r)
                break

            data = r.get("data") or []
            if not data:
                break

            for t in data:
                raw_date = str(t.get("exchangeTime") or t.get("createTime") or "")
                date_str = raw_date[:10] if len(raw_date) >= 10 else ""
                txn_type = str(t.get("transactionType") or "BUY").upper()
                qty      = _i(t.get("tradedQuantity"))
                price    = _f(t.get("tradedPrice"))

                if qty <= 0 or price <= 0 or not date_str:
                    continue

                all_trades.append(Trade(
                    date     = date_str,
                    symbol   = str(t.get("tradingSymbol") or ""),
                    exchange = _exch(t.get("exchangeSegment") or "NSE_EQ"),
                    action   = "BUY" if txn_type == "BUY" else "SELL",
                    qty      = qty,
                    price    = price,
                    order_id = str(t.get("orderId") or ""),
                ))

            page += 1
            if len(data) < 50:
                break

        logger.info("[Dhan] get_trade_history %s..%s: %d trades", from_date, to_date, len(all_trades))
        return all_trades
