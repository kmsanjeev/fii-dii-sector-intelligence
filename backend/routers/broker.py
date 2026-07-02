"""
Broker Router -- Phase 22

GET  /api/broker/status          connection status + last sync
POST /api/broker/auth            save credentials (Dhan client_id + access_token)
POST /api/broker/sync            trigger live sync from Dhan
POST /api/broker/sync-trades     sync + import trade history into transactions.csv
GET  /api/broker/holdings        current broker holdings + intelligence overlay
POST /api/broker/import-csv      upload holdings/trades CSV (no API key needed)
DELETE /api/broker/auth          clear stored credentials
"""

import shutil
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from engines.broker.sync_engine import (
    save_credentials,
    get_status,
    run as sync_run,
    load_broker_holdings,
    overlay_intelligence,
    PORTFOLIO_DIR,
    BROKER_AUTH,
)

router = APIRouter(prefix="/api/broker", tags=["broker"])


# ── Request models ─────────────────────────────────────────────────────────────

class AuthRequest(BaseModel):
    broker:       str = "dhan"
    client_id:    str
    access_token: str


class SyncTradesRequest(BaseModel):
    from_date: Optional[str] = None
    to_date:   Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("/status")
def broker_status():
    return get_status()


@router.post("/auth")
def save_broker_auth(req: AuthRequest):
    """Save broker credentials to broker_auth.json (never committed to git)."""
    if not req.client_id.strip() or not req.access_token.strip():
        raise HTTPException(status_code=400, detail="client_id and access_token are required")
    try:
        save_credentials(req.broker, req.client_id.strip(), req.access_token.strip())
        # Quick ping to validate
        from engines.broker.sync_engine import get_adapter, load_credentials
        adapter = get_adapter(load_credentials())
        valid = adapter.ping() if adapter else False
        return {
            "status":  "SAVED",
            "broker":  req.broker,
            "valid":   valid,
            "message": "Credentials saved and validated." if valid else "Saved but ping failed -- check client_id / access_token.",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/sync")
def sync_holdings():
    """Pull current holdings from broker and refresh intelligence overlay."""
    result = sync_run(import_trades=False)
    if result["status"] == "NO_CREDENTIALS":
        raise HTTPException(status_code=400, detail="No broker credentials saved. POST /api/broker/auth first.")
    if result["status"] == "FAILED":
        raise HTTPException(status_code=502, detail=result.get("error", "Sync failed"))
    return result


@router.post("/sync-trades")
def sync_with_trades(req: SyncTradesRequest):
    """Pull holdings AND import trade history into transactions.csv."""
    result = sync_run(
        import_trades = True,
        from_date     = req.from_date or "",
        to_date       = req.to_date   or "",
    )
    if result["status"] == "NO_CREDENTIALS":
        raise HTTPException(status_code=400, detail="No broker credentials saved. POST /api/broker/auth first.")
    if result["status"] == "FAILED":
        raise HTTPException(status_code=502, detail=result.get("error", "Sync failed"))
    return result


@router.get("/holdings")
def get_broker_holdings():
    """Return broker holdings with intelligence overlay."""
    df = load_broker_holdings()
    if df.empty:
        return {"holdings": [], "total": 0, "last_synced": None,
                "message": "No holdings synced yet. Click Sync to pull from broker."}
    enriched = overlay_intelligence(df)
    records  = enriched.where(enriched.notna(), None).to_dict(orient="records")
    last_synced = str(df["last_synced"].iloc[0]) if "last_synced" in df.columns else None
    return {
        "holdings":    records,
        "total":       len(records),
        "last_synced": last_synced,
    }


@router.post("/import-csv")
async def import_csv(
    holdings_file: Optional[UploadFile] = File(default=None),
    trades_file:   Optional[UploadFile] = File(default=None),
):
    """
    Upload broker-exported CSV files without needing API credentials.
    holdings_file: positions export (symbol, qty, avg_cost, LTP)
    trades_file:   trade history export (optional)
    """
    from engines.broker.csv_adapter import CsvAdapter
    from engines.broker.sync_engine import _save_holdings, _merge_trades

    if not holdings_file and not trades_file:
        raise HTTPException(status_code=400, detail="Provide at least a holdings CSV file")

    tmp_holdings = tmp_trades = ""
    try:
        PORTFOLIO_DIR.mkdir(parents=True, exist_ok=True)

        if holdings_file:
            contents = await holdings_file.read()
            tmp_holdings = str(PORTFOLIO_DIR / f"_upload_holdings_{holdings_file.filename}")
            Path(tmp_holdings).write_bytes(contents)

        if trades_file:
            contents = await trades_file.read()
            tmp_trades = str(PORTFOLIO_DIR / f"_upload_trades_{trades_file.filename}")
            Path(tmp_trades).write_bytes(contents)

        adapter = CsvAdapter(holdings_csv=tmp_holdings, trades_csv=tmp_trades)
        holdings = adapter.get_holdings() if tmp_holdings else []
        if holdings:
            _save_holdings(holdings)

        trades_imported = 0
        if tmp_trades:
            trades = adapter.get_trade_history("1990-01-01", "2099-12-31")
            trades_imported = _merge_trades(trades)

        # Rebuild portfolio intelligence
        try:
            from engines.portfolio.portfolio_engine import rebuild
            rebuild()
        except Exception:
            pass

        return {
            "status":          "DONE",
            "holdings_count":  len(holdings),
            "trades_imported": trades_imported,
        }

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    finally:
        for tmp in (tmp_holdings, tmp_trades):
            if tmp:
                try:
                    Path(tmp).unlink(missing_ok=True)
                except Exception:
                    pass


@router.delete("/auth")
def clear_broker_auth():
    """Remove stored broker credentials."""
    if BROKER_AUTH.exists():
        BROKER_AUTH.unlink()
    return {"status": "CLEARED"}
