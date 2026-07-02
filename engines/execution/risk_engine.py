"""
Risk Engine -- Phase 24
Pre-trade risk checks applied to every order before execution.

Rules (all configurable via data/execution/execution_config.json):
  paper_mode          : simulated fills, no real orders (default True)
  portfolio_value     : total INR portfolio value used for sizing (default 0 = skip % checks)
  max_position_pct    : single position <= N% of portfolio (default 10)
  max_sector_pct      : sector total <= N% of portfolio (default 25)
  min_cash_pct        : cash >= N% of portfolio (default 10)
  allow_duplicate_orders : reject if pending order exists for same symbol (default False)
"""

import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from engines.common import config as cfg
from engines.common.logger import get_logger

logger = get_logger(__name__)

CONFIG_FILE = cfg.DATA_DIR / "execution" / "execution_config.json"

DEFAULT_CONFIG: dict = {
    "paper_mode":             True,
    "portfolio_value":        0.0,
    "max_position_pct":       10.0,
    "max_sector_pct":         25.0,
    "min_cash_pct":           10.0,
    "allow_duplicate_orders": False,
}


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, encoding="utf-8") as f:
                stored = json.load(f)
            return {**DEFAULT_CONFIG, **stored}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(updates: dict) -> dict:
    data = load_config()
    data.update({k: v for k, v in updates.items() if v is not None})
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    shutil.move(str(tmp), str(CONFIG_FILE))
    logger.info("[Risk] Config saved: %s", data)
    return data


@dataclass
class RiskResult:
    passed: bool
    reason: str = ""


def check_order(
    symbol: str,
    sector: str,
    order_value: float,
    portfolio_value: float,
    cash_available: float,
    pending_symbols: list,
    holdings_by_sector: dict,
) -> RiskResult:
    """
    Run all pre-trade risk checks. Returns on first failure.
    If portfolio_value == 0, size/sector/cash checks are skipped.
    """
    risk_cfg = load_config()

    # 1. Duplicate order guard
    if not risk_cfg.get("allow_duplicate_orders", False):
        if symbol.upper() in [s.upper() for s in pending_symbols]:
            return RiskResult(False, f"Duplicate: pending order already exists for {symbol}")

    # Skip % checks when portfolio value is not configured
    if portfolio_value <= 0:
        return RiskResult(True, "Portfolio value not set -- size checks skipped")

    # 2. Position size
    max_pos = risk_cfg.get("max_position_pct", 10.0) / 100.0
    if order_value / portfolio_value > max_pos:
        allowed = round(max_pos * portfolio_value, 2)
        return RiskResult(
            False,
            f"Position size {order_value:,.0f} exceeds {max_pos*100:.0f}% cap "
            f"(max {allowed:,.0f} INR)"
        )

    # 3. Sector concentration
    max_sec = risk_cfg.get("max_sector_pct", 25.0) / 100.0
    current_sec = holdings_by_sector.get(sector, 0.0)
    if (current_sec + order_value) / portfolio_value > max_sec:
        headroom = max(0.0, round(max_sec * portfolio_value - current_sec, 2))
        return RiskResult(
            False,
            f"Sector {sector} would exceed {max_sec*100:.0f}% cap "
            f"({headroom:,.0f} INR headroom)"
        )

    # 4. Cash reserve floor
    min_cash = risk_cfg.get("min_cash_pct", 10.0) / 100.0
    if cash_available > 0 and (cash_available - order_value) / portfolio_value < min_cash:
        floor = round(min_cash * portfolio_value, 2)
        return RiskResult(
            False,
            f"Order would breach {min_cash*100:.0f}% cash floor "
            f"({floor:,.0f} INR required)"
        )

    return RiskResult(True, "All risk checks passed")
