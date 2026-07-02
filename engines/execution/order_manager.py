"""
Order Manager -- Phase 24
Order lifecycle: place, cancel, status poll, blotter.

Paper mode: simulates immediate fill at LTP (MARKET) or limit price (LIMIT).
Live mode:  routes through DhanOrderAdapter; requires security_master.json.

All orders (paper + live) are appended to data/execution/orders.csv.
"""

import csv
import shutil
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger
from engines.execution.risk_engine import RiskResult, check_order, load_config

logger = get_logger(__name__)

EXEC_DIR   = cfg.DATA_DIR / "execution"
ORDERS_CSV = EXEC_DIR / "orders.csv"

_COLS = [
    "order_id", "created_at", "symbol", "sector", "exchange",
    "action", "qty", "price", "order_type",
    "status", "paper", "filled_qty", "avg_fill_price",
    "broker_order_id", "reject_reason", "notes",
]


@dataclass
class Order:
    order_id:        str
    created_at:      str
    symbol:          str
    sector:          str
    exchange:        str
    action:          str
    qty:             int
    price:           float
    order_type:      str
    status:          str        # PENDING | FILLED | CANCELLED | REJECTED
    paper:           bool
    filled_qty:      int   = 0
    avg_fill_price:  float = 0.0
    broker_order_id: str   = ""
    reject_reason:   str   = ""
    notes:           str   = ""


# ── Persistence ───────────────────────────────────────────────────────────────

def _ensure() -> None:
    EXEC_DIR.mkdir(parents=True, exist_ok=True)


def _load_orders() -> list[Order]:
    _ensure()
    if not ORDERS_CSV.exists():
        return []
    orders: list[Order] = []
    with open(ORDERS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                orders.append(Order(
                    order_id        = row.get("order_id", ""),
                    created_at      = row.get("created_at", ""),
                    symbol          = row.get("symbol", ""),
                    sector          = row.get("sector", ""),
                    exchange        = row.get("exchange", "NSE"),
                    action          = row.get("action", "BUY"),
                    qty             = int(row.get("qty") or 0),
                    price           = float(row.get("price") or 0),
                    order_type      = row.get("order_type", "MARKET"),
                    status          = row.get("status", "PENDING"),
                    paper           = str(row.get("paper", "true")).lower() in ("true", "1", "yes"),
                    filled_qty      = int(row.get("filled_qty") or 0),
                    avg_fill_price  = float(row.get("avg_fill_price") or 0),
                    broker_order_id = row.get("broker_order_id", ""),
                    reject_reason   = row.get("reject_reason", ""),
                    notes           = row.get("notes", ""),
                ))
            except Exception as exc:
                logger.warning("[OrderMgr] Skipping malformed row: %s", exc)
    return orders


def _save_orders(orders: list[Order]) -> None:
    _ensure()
    tmp = ORDERS_CSV.with_suffix(".tmp")
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_COLS)
        w.writeheader()
        for o in orders:
            row = asdict(o)
            row["paper"] = "true" if o.paper else "false"
            w.writerow(row)
    shutil.move(str(tmp), str(ORDERS_CSV))


def _append_order(order: Order) -> None:
    _ensure()
    write_header = not ORDERS_CSV.exists()
    with open(ORDERS_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_COLS)
        if write_header:
            w.writeheader()
        row = asdict(order)
        row["paper"] = "true" if order.paper else "false"
        w.writerow(row)


# ── Public API ────────────────────────────────────────────────────────────────

def get_blotter(status_filter: Optional[str] = None, limit: int = 200) -> list[dict]:
    """Return orders most-recent first, optionally filtered by status."""
    orders = _load_orders()
    if status_filter and status_filter.upper() != "ALL":
        orders = [o for o in orders if o.status == status_filter.upper()]
    orders.sort(key=lambda o: o.created_at, reverse=True)
    result = []
    for o in orders[:limit]:
        d = asdict(o)
        d["order_value"] = round(o.qty * (o.avg_fill_price or o.price), 2)
        result.append(d)
    return result


def get_pending_symbols() -> list[str]:
    return [o.symbol for o in _load_orders() if o.status == "PENDING"]


def place_order(
    symbol: str,
    sector: str,
    action: str,
    qty: int,
    price: float = 0.0,
    order_type: str = "MARKET",
    exchange: str = "NSE",
    notes: str = "",
    portfolio_value: float = 0.0,
) -> dict:
    """
    Place a paper or live order after risk checks.
    Returns {"success": bool, "order_id": str, "message": str}
    """
    risk_cfg = load_config()
    paper    = risk_cfg.get("paper_mode", True)

    # Use config portfolio_value if caller did not supply one
    if portfolio_value <= 0:
        portfolio_value = float(risk_cfg.get("portfolio_value", 0.0))

    ltp         = _fetch_ltp(symbol)
    order_value = qty * (price if price > 0 else ltp)

    # Risk check
    risk: RiskResult = check_order(
        symbol             = symbol,
        sector             = sector or "UNKNOWN",
        order_value        = order_value,
        portfolio_value    = portfolio_value,
        cash_available     = portfolio_value * 0.9,   # conservative; improved when Portfolio engine is live
        pending_symbols    = get_pending_symbols(),
        holdings_by_sector = {},
    )

    if not risk.passed:
        logger.warning("[OrderMgr] Risk FAIL %s: %s", symbol, risk.reason)
        return {"success": False, "order_id": "", "message": risk.reason}

    order_id   = str(uuid.uuid4())[:8].upper()
    created_at = datetime.now(timezone.utc).isoformat()

    if paper:
        fill_price = price if (order_type == "LIMIT" and price > 0) else ltp
        order = Order(
            order_id       = order_id,
            created_at     = created_at,
            symbol         = symbol.upper(),
            sector         = sector or "UNKNOWN",
            exchange       = exchange,
            action         = action.upper(),
            qty            = qty,
            price          = price,
            order_type     = order_type,
            status         = "FILLED",
            paper          = True,
            filled_qty     = qty,
            avg_fill_price = fill_price,
            notes          = notes,
        )
        _append_order(order)
        msg = f"[PAPER] {action.upper()} {qty} {symbol} @ {fill_price:.2f} filled"
        logger.info("[OrderMgr] %s", msg)
        return {"success": True, "order_id": order_id, "message": msg}

    # Live order via Dhan
    broker_oid, err = _place_dhan(symbol, action, qty, price, order_type, exchange)
    status = "REJECTED" if err else "PENDING"
    order = Order(
        order_id        = order_id,
        created_at      = created_at,
        symbol          = symbol.upper(),
        sector          = sector or "UNKNOWN",
        exchange        = exchange,
        action          = action.upper(),
        qty             = qty,
        price           = price,
        order_type      = order_type,
        status          = status,
        paper           = False,
        broker_order_id = broker_oid,
        reject_reason   = err,
        notes           = notes,
    )
    _append_order(order)
    if err:
        return {"success": False, "order_id": order_id, "message": err}
    msg = f"[LIVE] {action.upper()} {qty} {symbol} placed (broker_id={broker_oid})"
    logger.info("[OrderMgr] %s", msg)
    return {"success": True, "order_id": order_id, "message": msg}


def cancel_order(order_id: str) -> dict:
    orders = _load_orders()
    target = next((o for o in orders if o.order_id == order_id), None)
    if not target:
        return {"success": False, "message": f"Order {order_id} not found"}
    if target.status != "PENDING":
        return {"success": False, "message": f"Order {order_id} is {target.status} -- cannot cancel"}

    if target.paper:
        target.status = "CANCELLED"
        _save_orders(orders)
        return {"success": True, "message": f"Paper order {order_id} cancelled"}

    err = _cancel_dhan(target.broker_order_id)
    if err:
        return {"success": False, "message": err}
    target.status = "CANCELLED"
    _save_orders(orders)
    return {"success": True, "message": f"Live order {order_id} cancelled"}


def get_order_status(order_id: str) -> Optional[dict]:
    orders = _load_orders()
    target = next((o for o in orders if o.order_id == order_id), None)
    if not target:
        return None
    # Poll broker for live pending orders
    if not target.paper and target.status == "PENDING":
        _poll_status(target, orders)
    d = asdict(target)
    d["order_value"] = round(target.qty * (target.avg_fill_price or target.price), 2)
    return d


# ── Internal helpers ──────────────────────────────────────────────────────────

def _fetch_ltp(symbol: str) -> float:
    """Best-effort LTP from bull_run_probability.csv for paper MARKET fills."""
    try:
        import pandas as pd
        br = cfg.INTELLIGENCE_DIR / "bull_run_probability.csv"
        if br.exists():
            df = pd.read_csv(br, usecols=["symbol", "close_now"])
            row = df[df["symbol"].str.upper() == symbol.upper()]
            if not row.empty:
                return float(row.iloc[0]["close_now"])
    except Exception:
        pass
    return 0.0


def _place_dhan(
    symbol: str, action: str, qty: int,
    price: float, order_type: str, exchange: str,
) -> tuple[str, str]:
    """Returns (broker_order_id, error_str)."""
    try:
        from engines.broker.sync_engine import load_credentials
        from engines.execution.dhan_order_adapter import DhanOrderAdapter
        creds = load_credentials()
    except Exception as exc:
        return ("", f"No broker credentials: {exc}")

    if creds.get("broker") != "dhan":
        return ("", f"Live orders require Dhan credentials (current: {creds.get('broker')})")

    from engines.execution.dhan_order_adapter import DhanOrderAdapter
    sec_id = DhanOrderAdapter.get_security_id(symbol, exchange)
    if not sec_id:
        return ("", f"security_id not found for {symbol}:{exchange} -- run security-master refresh")

    adapter = DhanOrderAdapter(creds["client_id"], creds["access_token"])
    return adapter.place_order(
        security_id = sec_id,
        exchange    = exchange,
        action      = action,
        qty         = qty,
        order_type  = order_type,
        price       = price if order_type == "LIMIT" else 0.0,
    )


def _cancel_dhan(broker_order_id: str) -> str:
    """Returns error_str ("" on success)."""
    try:
        from engines.broker.sync_engine import load_credentials
        from engines.execution.dhan_order_adapter import DhanOrderAdapter
        creds = load_credentials()
        adapter = DhanOrderAdapter(creds["client_id"], creds["access_token"])
        return adapter.cancel_order(broker_order_id)
    except Exception as exc:
        return str(exc)


def _poll_status(order: Order, all_orders: list[Order]) -> None:
    try:
        from engines.broker.sync_engine import load_credentials
        from engines.execution.dhan_order_adapter import DhanOrderAdapter
        creds   = load_credentials()
        adapter = DhanOrderAdapter(creds["client_id"], creds["access_token"])
        s = adapter.get_order_status(order.broker_order_id)
        if s:
            order.status          = s.get("status", order.status)
            order.filled_qty      = int(s.get("filled_qty", 0))
            order.avg_fill_price  = float(s.get("avg_price", 0.0))
            _save_orders(all_orders)
    except Exception as exc:
        logger.warning("[OrderMgr] Status poll failed: %s", exc)
