"""
Kundli Router — Phase KU-4
Vedic natal chart + Gann analysis endpoints.

GET  /api/stocks/{symbol}/kundli          Stock natal chart (IPO date)
POST /api/kundli/human                    Human natal chart
GET  /api/kundli/country/{name}           Country inception chart
GET  /api/kundli/gann/{symbol}            Gann price levels for a stock
GET  /api/kundli/bulk/status              Bulk run status
POST /api/kundli/bulk/run                 Trigger bulk kundli computation
"""

from __future__ import annotations
import json
import threading
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from engines.common import config as cfg

router = APIRouter(prefix='/api', tags=['kundli'])

# ── Lazy singletons ────────────────────────────────────────────────────────────
_ke = None
_ge = None
_ki = None
_ke_lock = threading.Lock()


def _get_engines():
    global _ke, _ge, _ki
    with _ke_lock:
        if _ke is None:
            from engines.intelligence.kundli_engine import KundliEngine
            from engines.intelligence.gann_engine import GannEngine
            from engines.intelligence.kundli_interpretator import KundliInterpretator
            _ke = KundliEngine()
            _ge = GannEngine()
            _ki = KundliInterpretator()
    return _ke, _ge, _ki


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_equity_master() -> pd.DataFrame:
    path = cfg.NSE_DIR / 'equity_master' / 'equity_master.csv'
    if not path.exists():
        raise HTTPException(status_code=503, detail='equity_master.csv not found')
    df = pd.read_csv(path)
    df.columns = [c.lower() for c in df.columns]   # normalize to lowercase
    return df[df['series'] == 'EQ'].set_index('symbol')


def _latest_price(symbol: str) -> Optional[float]:
    p = cfg.INTELLIGENCE_DIR / 'price_momentum.csv'
    if not p.exists():
        return None
    try:
        df = pd.read_csv(p)
        # column is 'close_now' in price_momentum.csv
        price_col = 'close_now' if 'close_now' in df.columns else 'close'
        row = df[df['symbol'] == symbol]
        if not row.empty:
            return float(row.iloc[0][price_col])
    except Exception:
        pass
    return None


# ── Models ─────────────────────────────────────────────────────────────────────

class HumanKundliRequest(BaseModel):
    name:       str
    date_str:   str       # YYYY-MM-DD
    time_str:   str       # HH:MM:SS
    lat:        float
    lon:        float
    tz_offset:  float     # UTC offset e.g. 5.5 for IST


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get('/stocks/{symbol}/kundli')
async def stock_kundli(
    symbol: str,
    exchange: str = 'NSE',
    include_gann: bool = True,
    generate_narrative: bool = False,
):
    """
    Return Vedic natal chart for a stock based on its IPO/listing date.
    Optionally includes Gann Square of 9 levels at current price.
    """
    symbol = symbol.upper()

    # Load cached per-symbol kundli if available
    kundli_cache_path = cfg.INTELLIGENCE_DIR / 'kundli' / f'{symbol}_kundli.json'
    chart = None

    if kundli_cache_path.exists():
        try:
            with open(kundli_cache_path, encoding='utf-8') as f:
                chart = json.load(f)
        except Exception:
            chart = None

    # Fall back to live computation if cache miss
    if chart is None:
        try:
            em = _load_equity_master()
            if symbol not in em.index:
                raise HTTPException(status_code=404, detail=f'Symbol {symbol} not found')

            listing_date = str(em.loc[symbol, 'listing_date'])[:10]
            if listing_date in ('nan', 'NaT', 'None', ''):
                raise HTTPException(status_code=422, detail=f'No listing date for {symbol}')

            ke, ge, ki = _get_engines()
            chart = ke.compute_stock(symbol, listing_date, exchange)
            if chart is None:
                raise HTTPException(status_code=500, detail='Kundli computation failed')

        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    # Gann analysis at current price
    gann_result = None
    if include_gann:
        price = _latest_price(symbol)
        if price and price > 0:
            try:
                ke, ge, ki = _get_engines()
                gann_result = ge.analyse(price)
            except Exception:
                pass

    # Interpretation
    try:
        ke, ge, ki = _get_engines()
        interpretation = ki.interpret(chart, gann_result,
                                      generate_narrative=generate_narrative)
    except Exception:
        interpretation = {}

    return {
        'symbol':         symbol,
        'exchange':       exchange,
        'kundli':         chart,
        'gann':           gann_result,
        'interpretation': interpretation,
    }


@router.post('/kundli/human')
async def human_kundli(req: HumanKundliRequest, generate_narrative: bool = False):
    """
    Compute Vedic natal chart for a human being.
    """
    ke, ge, ki = _get_engines()
    chart = ke.compute_human(
        name=req.name,
        date_str=req.date_str,
        time_str=req.time_str,
        lat=req.lat,
        lon=req.lon,
        tz_offset=req.tz_offset,
    )
    if chart is None:
        raise HTTPException(status_code=500, detail='Kundli computation failed')

    interpretation = ki.interpret(chart, generate_narrative=generate_narrative)
    return {'kundli': chart, 'interpretation': interpretation}


@router.get('/kundli/country/{name}')
async def country_kundli(name: str, generate_narrative: bool = False):
    """
    Return inception chart for a country.
    Available: India, USA, UK, China, Japan, Germany, Pakistan, Russia, France, Brazil
    """
    ke, ge, ki = _get_engines()
    chart = ke.compute_country(name)
    if chart is None or 'error' in chart:
        raise HTTPException(
            status_code=404,
            detail=chart.get('error', 'Country not found') if chart else 'Computation failed',
        )
    interpretation = ki.interpret(chart, generate_narrative=generate_narrative)
    return {'country': name, 'kundli': chart, 'interpretation': interpretation}


@router.get('/kundli/gann/{symbol}')
async def gann_analysis(symbol: str, price: Optional[float] = None):
    """
    Return Gann Square of 9 levels + planetary lines for a stock's current price.
    """
    symbol = symbol.upper()
    if price is None or price <= 0:
        price = _latest_price(symbol)
        if price is None or price <= 0:
            raise HTTPException(status_code=404, detail=f'No price data for {symbol}')

    ke, ge, ki = _get_engines()
    result = ge.analyse(price)
    return {'symbol': symbol, 'price': price, 'gann': result}


@router.get('/kundli/gann/market/planetary-lines')
async def market_planetary_lines(price_factor: float = 1.0):
    """
    Return current planetary longitude → price mappings for the market.
    """
    from datetime import datetime
    ke, ge, ki = _get_engines()
    jd = ge._date_to_jd(datetime.now().strftime('%Y-%m-%d'))
    lines = ge.planetary_lines(jd, price_factor)
    cycles = ge.solar_time_cycles(datetime.now().strftime('%Y-%m-%d'))
    return {'planetary_lines': lines, 'time_cycles': cycles}


@router.get('/kundli/bulk/status')
async def bulk_status():
    """Return status of bulk kundli computation."""
    csv_path = cfg.INTELLIGENCE_DIR / 'kundli_signals.csv'
    kundli_dir = cfg.INTELLIGENCE_DIR / 'kundli'

    json_files = list(kundli_dir.glob('*_kundli.json')) if kundli_dir.exists() else []

    if csv_path.exists():
        import os
        stat     = csv_path.stat()
        df       = pd.read_csv(csv_path)
        return {
            'status':       'complete',
            'symbols_done': len(df),
            'json_files':   len(json_files),
            'last_updated': stat.st_mtime,
            'csv_path':     str(csv_path),
        }
    return {'status': 'not_run', 'symbols_done': 0, 'json_files': len(json_files)}


@router.post('/kundli/bulk/run')
async def bulk_run(background_tasks: BackgroundTasks):
    """
    Trigger bulk kundli computation for all NSE stocks (runs in background).
    """
    def _run():
        ke, ge, ki = _get_engines()
        ke.run()
        ge.run()

    background_tasks.add_task(_run)
    return {'status': 'started', 'message': 'Bulk kundli computation started in background'}
