"""
Dhan Order Adapter -- Phase 24
Write-capable extension for the Dhan broker: order placement, cancellation, status.
Kept separate from dhan_adapter.py (R/O) -- the base BrokerAdapter never exposes
order methods.

Dhan API docs: https://dhanhq.co/docs/v2/orders/
"""

import json
import shutil
import sys
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

# Exchange segment codes for order placement (Dhan notation)
_ORDER_EXCHANGE: dict[str, str] = {
    "NSE": "NSE_EQ",
    "BSE": "BSE_EQ",
}

# Order type mapping
_ORDER_TYPE: dict[str, str] = {
    "MARKET": "MARKET",
    "LIMIT":  "LIMIT",
    "SL":     "STOP_LOSS",
    "SL-M":   "STOP_LOSS_MARKET",
}

SECURITY_MASTER_PATH = cfg.DATA_DIR / "execution" / "security_master.json"
SCRIP_MASTER_URL     = "https://images.dhan.co/api-data/api-scrip-master.csv"


class DhanOrderAdapter:
    """
    Write interface for Dhan: place / cancel / status.
    Instantiated with the same credentials as DhanAdapter (Phase 22).
    """

    def __init__(self, client_id: str, access_token: str):
        from dhanhq import dhanhq as DhanHQ
        self._client = DhanHQ(str(client_id), str(access_token))
        logger.info("[DhanOrder] Adapter ready for client %s", client_id[:4] + "****")

    # ── Order placement ────────────────────────────────────────────────────────

    def place_order(
        self,
        security_id: str,
        exchange: str,
        action: str,
        qty: int,
        order_type: str = "MARKET",
        price: float = 0.0,
        product_type: str = "CNC",
        tag: str = "CFIP",
    ) -> tuple[str, str]:
        """
        Place an order via Dhan API.
        Returns (broker_order_id, error_str). error_str is "" on success.
        """
        segment  = _ORDER_EXCHANGE.get(exchange.upper(), "NSE_EQ")
        otype    = _ORDER_TYPE.get(order_type.upper(), "MARKET")
        txn_type = action.upper()

        try:
            r = self._client.place_order(
                security_id      = str(security_id),
                exchange_segment = segment,
                transaction_type = txn_type,
                quantity         = qty,
                order_type       = otype,
                product_type     = product_type,
                price            = price if otype == "LIMIT" else 0,
                trigger_price    = 0,
                tag              = tag,
            )
            if not isinstance(r, dict):
                return ("", f"Unexpected Dhan response: {r}")
            if r.get("status") != "success":
                remarks = r.get("remarks", {})
                msg = remarks.get("message", str(remarks)) if isinstance(remarks, dict) else str(remarks)
                return ("", msg or "Dhan rejected the order")
            order_id = str((r.get("data") or {}).get("orderId", ""))
            logger.info("[DhanOrder] Placed %s %d × sec=%s -> orderId=%s", txn_type, qty, security_id, order_id)
            return (order_id, "")
        except Exception as exc:
            logger.error("[DhanOrder] place_order error: %s", exc)
            return ("", str(exc))

    def cancel_order(self, broker_order_id: str) -> str:
        """Cancel an order. Returns error_str ("" on success)."""
        try:
            r = self._client.cancel_order(broker_order_id)
            if not isinstance(r, dict):
                return f"Unexpected response: {r}"
            if r.get("status") != "success":
                remarks = r.get("remarks", {})
                return remarks.get("message", str(remarks)) if isinstance(remarks, dict) else str(remarks)
            logger.info("[DhanOrder] Cancelled %s", broker_order_id)
            return ""
        except Exception as exc:
            logger.error("[DhanOrder] cancel_order error: %s", exc)
            return str(exc)

    def get_order_status(self, broker_order_id: str) -> Optional[dict]:
        """
        Fetch live order status from Dhan.
        Returns normalised dict {status, filled_qty, avg_price} or None.
        """
        _STATUS_MAP = {
            "TRADED":      "FILLED",
            "TRANSIT":     "PENDING",
            "PENDING":     "PENDING",
            "CANCELLED":   "CANCELLED",
            "REJECTED":    "REJECTED",
            "PART_TRADED": "PENDING",
        }
        try:
            r = self._client.get_order_by_id(broker_order_id)
            if not isinstance(r, dict) or r.get("status") != "success":
                return None
            data = r.get("data") or {}
            raw  = str(data.get("orderStatus", "")).upper()
            return {
                "status":     _STATUS_MAP.get(raw, raw),
                "filled_qty": int(data.get("filledQty", 0)),
                "avg_price":  float(data.get("price", 0.0)),
            }
        except Exception as exc:
            logger.warning("[DhanOrder] get_order_status error: %s", exc)
            return None

    # ── Security master ────────────────────────────────────────────────────────

    @staticmethod
    def refresh_security_master() -> dict[str, str]:
        """
        Download Dhan's scrip master CSV and build symbol:EXCH -> security_id map.
        Saves to data/execution/security_master.json.
        Returns the mapping dict.
        """
        import pandas as pd

        SECURITY_MASTER_PATH.parent.mkdir(parents=True, exist_ok=True)
        logger.info("[DhanOrder] Downloading scrip master from Dhan...")
        try:
            df = pd.read_csv(SCRIP_MASTER_URL, low_memory=False)
        except Exception as exc:
            logger.error("[DhanOrder] scrip master download failed: %s", exc)
            return {}

        # Locate key columns (Dhan column names may vary slightly across versions)
        col_map: dict[str, Optional[str]] = {"sid": None, "sym": None, "seg": None}
        for col in df.columns:
            cl = col.upper()
            if "SECURITY_ID" in cl and col_map["sid"] is None:
                col_map["sid"] = col
            elif "TRADING_SYMBOL" in cl and col_map["sym"] is None:
                col_map["sym"] = col
            elif "SEGMENT" in cl and col_map["seg"] is None:
                col_map["seg"] = col

        if not all(col_map.values()):
            logger.error("[DhanOrder] Unexpected scrip master columns: %s", list(df.columns[:10]))
            return {}

        df = df[df[col_map["seg"]].isin(["NSE_EQ", "BSE_EQ"])].copy()
        mapping: dict[str, str] = {}
        for _, row in df.iterrows():
            sym = str(row[col_map["sym"]]).strip().upper()
            seg = str(row[col_map["seg"]]).strip().upper()
            sid = str(row[col_map["sid"]]).strip()
            exch = "NSE" if seg == "NSE_EQ" else "BSE"
            if sym and sid:
                mapping[f"{sym}:{exch}"] = sid

        tmp = SECURITY_MASTER_PATH.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(mapping, f)
        shutil.move(str(tmp), str(SECURITY_MASTER_PATH))
        logger.info("[DhanOrder] Security master cached: %d symbols", len(mapping))
        return mapping

    @staticmethod
    def get_security_id(symbol: str, exchange: str = "NSE") -> Optional[str]:
        """Look up cached security_id for symbol:exchange."""
        if not SECURITY_MASTER_PATH.exists():
            return None
        try:
            with open(SECURITY_MASTER_PATH, encoding="utf-8") as f:
                sm = json.load(f)
            return sm.get(f"{symbol.upper()}:{exchange.upper()}")
        except Exception:
            return None
