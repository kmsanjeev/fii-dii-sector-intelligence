"""
Alert Store — Phase 9B
Tracks sent alerts, enforces per-(symbol+type) cooldown windows,
prevents duplicate delivery. State persisted to JSON (atomic writes).
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from engines.common import config as cfg
from engines.common.logger import get_logger
from alerts.alert_engine import Alert, PRIORITY_ORDER

logger = get_logger(__name__)

# ── State file ────────────────────────────────────────────────────────────────

ALERT_STATE_FILE = cfg.INTELLIGENCE_DIR / "alert_state.json"

# ── Cooldown windows (hours) per alert type ───────────────────────────────────

COOLDOWN_HOURS = {
    "REGIME_CHANGE":          0,     # always fire — no cooldown
    "STRONG_CANDIDATE":       72,
    "SECTOR_ROTATION":        48,
    "INSTITUTIONAL_DEAL":     48,
    "CORPORATE_CONFIDENCE":   48,
    "PARTICIPANT_DIVERGENCE": 48,
    "DAILY_DIGEST":           24,
}


class AlertStore:
    """
    Loads/saves alert send history. Filters alerts that are within cooldown.
    All writes are atomic (.tmp -> rename) per G-D-02.
    """

    def __init__(self):
        self._state: dict = self._load()

    # ── State I/O ─────────────────────────────────────────────────────────────

    def _load(self) -> dict:
        if not ALERT_STATE_FILE.exists():
            logger.info("[AlertStore] No state file found — starting fresh")
            return {"sent": {}}
        try:
            with open(ALERT_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[AlertStore] Failed to load state: {e} — starting fresh")
            return {"sent": {}}

    def _save(self):
        tmp = ALERT_STATE_FILE.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2)
            shutil.move(str(tmp), str(ALERT_STATE_FILE))
            logger.debug("[AlertStore] State saved")
        except Exception as e:
            logger.error(f"[AlertStore] Failed to save state: {e}")
            if tmp.exists():
                tmp.unlink()

    # ── Cooldown check ────────────────────────────────────────────────────────

    def _cooldown_key(self, alert: Alert) -> str:
        symbol_part = alert.symbol or "_MARKET_"
        sector_part = alert.sector or "_NONE_"
        return f"{alert.alert_type}::{symbol_part}::{sector_part}"

    def _is_in_cooldown(self, alert: Alert) -> bool:
        cooldown_h = COOLDOWN_HOURS.get(alert.alert_type, 48)
        if cooldown_h == 0:
            return False

        key = self._cooldown_key(alert)
        last_sent = self._state.get("sent", {}).get(key)
        if not last_sent:
            return False

        try:
            last_dt = datetime.fromisoformat(last_sent)
            cutoff = datetime.now() - timedelta(hours=cooldown_h)
            return last_dt > cutoff
        except Exception:
            return False

    def mark_sent(self, alert: Alert):
        key = self._cooldown_key(alert)
        if "sent" not in self._state:
            self._state["sent"] = {}
        self._state["sent"][key] = datetime.now().isoformat()
        self._save()

    # ── Filter ────────────────────────────────────────────────────────────────

    def filter_eligible(self, alerts: list) -> list:
        eligible = []
        suppressed = 0
        for alert in alerts:
            if self._is_in_cooldown(alert):
                suppressed += 1
                logger.debug(
                    f"[AlertStore] Suppressed (cooldown): {alert.alert_type} {alert.symbol or ''}"
                )
            else:
                eligible.append(alert)

        logger.info(
            f"[AlertStore] {len(alerts)} alerts in -> "
            f"{len(eligible)} eligible, {suppressed} suppressed"
        )
        return eligible

    # ── Previous regime helper ────────────────────────────────────────────────

    def get_previous_regime(self) -> Optional[str]:
        return self._state.get("last_regime")

    def set_current_regime(self, regime: str):
        self._state["last_regime"] = regime
        self._save()
