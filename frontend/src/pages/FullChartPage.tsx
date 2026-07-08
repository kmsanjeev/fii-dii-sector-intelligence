/**
 * FullChartPage — full-viewport chart powered by KLineChart Pro
 * Route: /fullchart/:symbol  (outside AppShell — no nav bar)
 *
 * KLineChart Pro handles: period selector, indicator panel,
 * drawing tools bar, multi-pane layout, 30+ built-in indicators.
 * We add: thin top bar, snapshot, watchlist panel.
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { KLineChartPro } from '@klinecharts/pro'
import type { Datafeed, SymbolInfo, Period, DatafeedSubscribeCallback } from '@klinecharts/pro'
import type { KLineData } from 'klinecharts'
import { dispose } from 'klinecharts'
import '@klinecharts/pro/dist/klinecharts-pro.css'
import { api } from '../api/client'

// ── Constants ────────────────────────────────────────────────────────────────

const PERIODS: Period[] = [
  { multiplier: 5,  timespan: 'minute', text: '5M'  },
  { multiplier: 15, timespan: 'minute', text: '15M' },
  { multiplier: 60, timespan: 'minute', text: '1H'  },
  { multiplier: 1,  timespan: 'day',    text: '1D'  },
  { multiplier: 1,  timespan: 'week',   text: '1W'  },
  { multiplier: 1,  timespan: 'month',  text: '1M'  },
  { multiplier: 3,  timespan: 'month',  text: '3M'  },
]

const TF_TO_PERIOD: Record<string, Period> = {
  '5M':  PERIODS[0], '15M': PERIODS[1], '1H':  PERIODS[2],
  '1D':  PERIODS[3], '1W':  PERIODS[4], '1M':  PERIODS[5], '3M': PERIODS[6],
}

// ── Theme palette — matches the platform's dark theme ────────────────────────

const C = {
  bg:     '#0A0D14',
  panel:  '#141720',
  cell:   '#1C2130',
  border: '#1E2332',
  text:   '#E2E8F0',
  sub:    '#64748B',
  dim:    '#374151',
  green:  '#22C55E',
  red:    '#EF4444',
  amber:  '#F59E0B',
  blue:   '#3B82F6',
  purple: '#A78BFA',
}

// ── Period → our TF string ────────────────────────────────────────────────────

function periodToTF(p: Period): string {
  if (p.timespan === 'minute' && p.multiplier === 5)  return '5M'
  if (p.timespan === 'minute' && p.multiplier === 15) return '15M'
  if (p.timespan === 'minute' && p.multiplier === 60) return '1H'
  if (p.timespan === 'hour'   && p.multiplier === 1)  return '1H'
  if (p.timespan === 'day')                            return '1D'
  if (p.timespan === 'week')                           return '1W'
  if (p.timespan === 'month'  && p.multiplier === 1)  return '1M'
  if (p.timespan === 'month'  && p.multiplier === 3)  return '3M'
  return '1D'
}

// ── Bar time string → Unix ms ─────────────────────────────────────────────────
//
// KLineChart Pro's built-in timezone list skips UTC+5:30 entirely (jumps from
// UTC+5 Ashkhabad to UTC+6 Almaty), so "Asia/Kolkata" is unavailable in the
// picker UI. We use chart timezone = "UTC" instead, then bake IST into the
// timestamps by stripping any tz-offset and appending Z — so "09:15 IST"
// renders as "09:15" on the UTC axis, which is exactly what NSE users expect.

function barTimeToMs(t: string | number): number {
  if (typeof t === 'number') return t > 1e12 ? t : t * 1000
  if (t.includes('T')) {
    // Strip tz offset (+05:30, +00:00, Z) and force UTC so the clock reading
    // matches IST wall-clock time (09:15 → shows "09:15" not "03:45").
    const bare = t.replace(/([+-]\d{2}:\d{2}|Z)$/, '')
    return new Date(bare + 'Z').getTime()
  }
  // "2026-07-08" — daily bar: UTC midnight keeps the date label correct.
  return new Date(t + 'T00:00:00Z').getTime()
}

// ── Custom Datafeed — wires our /charts/ohlcv API ───────────────────────────

class OurDatafeed implements Datafeed {
  private _timers = new Map<string, ReturnType<typeof setInterval>>()

  async searchSymbols(search?: string): Promise<SymbolInfo[]> {
    if (!search || search.trim().length < 1) return []
    try {
      const r = await api.get<{ symbols: { SYMBOL: string; COMPANY_NAME: string }[] }>(
        '/charts/symbols', { params: { q: search.trim().toUpperCase() } }
      )
      return (r.data.symbols ?? []).map(s => ({
        ticker:    s.SYMBOL,
        shortName: s.SYMBOL,
        name:      s.COMPANY_NAME ?? s.SYMBOL,
        exchange:  'NSE',
        market:    'stocks',
      }))
    } catch { return [] }
  }

  async getHistoryKLineData(
    symbol: SymbolInfo, period: Period,
    _from: number, _to: number,   // we fetch full history, ignoring range
  ): Promise<KLineData[]> {
    const tf = periodToTF(period)
    try {
      const r = await api.get<{ bars: Array<{ time: string | number; open: number; high: number; low: number; close: number; volume: number }> }>(
        '/charts/ohlcv', { params: { symbol: symbol.ticker, timeframe: tf } }
      )
      return (r.data.bars ?? []).map(b => ({
        timestamp: barTimeToMs(b.time),
        open:  b.open,
        high:  b.high,
        low:   b.low,
        close: b.close,
        volume: b.volume ?? 0,
      }))
    } catch { return [] }
  }

  subscribe(symbol: SymbolInfo, period: Period, callback: DatafeedSubscribeCallback): void {
    // Poll every 60 s for the latest bar (no WebSocket backend yet)
    const key = `${symbol.ticker}_${period.text}`
    this._timers.set(key, setInterval(async () => {
      try {
        const tf = periodToTF(period)
        const r  = await api.get<{ bars: any[] }>('/charts/ohlcv', { params: { symbol: symbol.ticker, timeframe: tf } })
        const bars = r.data.bars ?? []
        if (!bars.length) return
        const last = bars[bars.length - 1]
        callback({
          timestamp: barTimeToMs(last.time),
          open: last.open, high: last.high, low: last.low, close: last.close,
          volume: last.volume ?? 0,
        })
      } catch { /* ignore */ }
    }, 60_000))
  }

  unsubscribe(symbol: SymbolInfo, period: Period): void {
    const key = `${symbol.ticker}_${period.text}`
    const t = this._timers.get(key)
    if (t) { clearInterval(t); this._timers.delete(key) }
  }
}

// ── Watchlist localStorage helpers ────────────────────────────────────────────

const WL_KEY = 'cfip-wl'
type WLEntry = { id: string; name: string; symbols: string[] }

function loadWL(): WLEntry[] {
  try {
    const raw = localStorage.getItem(WL_KEY)
    if (raw) { const p = JSON.parse(raw); if (Array.isArray(p) && p.length) return p }
  } catch { /* ignore */ }
  return [{ id: 'default', name: 'My Watchlist', symbols: [] }]
}
function saveWL(wls: WLEntry[]) {
  try { localStorage.setItem(WL_KEY, JSON.stringify(wls)) } catch { /* ignore */ }
}

// ── Watchlist Panel ───────────────────────────────────────────────────────────

function WatchlistPanel({ currentSym, onNavigate }: { currentSym: string; onNavigate: (s: string) => void }) {
  const [wls,      setWls]      = useState<WLEntry[]>(loadWL)
  const [activeId, setActiveId] = useState<string>(() => loadWL()[0]?.id ?? 'default')
  const [addVal,   setAddVal]   = useState('')
  const [renaming, setRenaming] = useState(false)
  const [rnVal,    setRnVal]    = useState('')

  const active = wls.find(w => w.id === activeId) ?? wls[0]
  function upd(next: WLEntry[]) { setWls(next); saveWL(next) }

  function addSym() {
    const s = addVal.trim().toUpperCase(); if (!s || !active) return
    if (!active.symbols.includes(s)) upd(wls.map(w => w.id === active.id ? { ...w, symbols: [...w.symbols, s] } : w))
    setAddVal('')
  }
  function removeSym(s: string) { upd(wls.map(w => w.id === active.id ? { ...w, symbols: w.symbols.filter(x => x !== s) } : w)) }
  function newList()  { const id = Date.now().toString(), n = `List ${wls.length + 1}`, nx = [...wls, { id, name: n, symbols: [] }]; upd(nx); setActiveId(id) }
  function delList()  { if (wls.length <= 1) return; const nx = wls.filter(w => w.id !== active.id); upd(nx); setActiveId(nx[0].id) }
  function commitRn() { const n = rnVal.trim(); if (n) upd(wls.map(w => w.id === active.id ? { ...w, name: n } : w)); setRenaming(false) }

  const btn = (color = C.sub): React.CSSProperties => ({ padding: '3px 7px', borderRadius: 3, fontSize: 10, cursor: 'pointer', border: `1px solid ${color}33`, background: 'transparent', color })

  return (
    <div style={{ width: 240, flexShrink: 0, borderLeft: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', background: C.panel, overflow: 'hidden' }}>
      {/* List tabs + New/Del */}
      <div style={{ padding: '8px 10px', borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 6 }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: C.text, letterSpacing: '0.08em', flex: 1 }}>WATCHLISTS</span>
          <button onClick={newList} style={btn(C.green)}>+ New</button>
          {wls.length > 1 && <button onClick={delList} style={btn(C.red)}>Del</button>}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
          {wls.map(w => (
            <button key={w.id} onClick={() => { setActiveId(w.id); setRenaming(false) }} style={{
              padding: '3px 8px', borderRadius: 3, fontSize: 10, cursor: 'pointer',
              border: `1px solid ${activeId === w.id ? C.blue : C.border}`,
              background: activeId === w.id ? C.blue + '22' : 'transparent',
              color: activeId === w.id ? C.blue : C.sub, fontWeight: activeId === w.id ? 700 : 400,
              maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>{w.name}</button>
          ))}
        </div>
      </div>

      {/* Active list header / rename */}
      <div style={{ padding: '6px 10px', borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
        {renaming ? (
          <div style={{ display: 'flex', gap: 4 }}>
            <input value={rnVal} onChange={e => setRnVal(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') commitRn(); if (e.key === 'Escape') setRenaming(false) }}
              autoFocus style={{ flex: 1, padding: '3px 6px', borderRadius: 3, border: `1px solid ${C.blue}`, background: C.cell, color: C.text, fontSize: 10, fontFamily: 'monospace' }} />
            <button onClick={commitRn} style={btn(C.green)}>OK</button>
            <button onClick={() => setRenaming(false)} style={btn(C.sub)}>X</button>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: C.text, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{active?.name}</span>
            <button onClick={() => { setRenaming(true); setRnVal(active?.name ?? '') }} style={btn(C.sub)}>Rename</button>
          </div>
        )}
      </div>

      {/* Symbol list */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {active?.symbols.length === 0 && (
          <div style={{ padding: '20px 10px', textAlign: 'center', color: C.dim, fontSize: 10 }}>No symbols yet.<br />Add below.</div>
        )}
        {active?.symbols.map(s => (
          <div key={s} style={{ display: 'flex', alignItems: 'center', padding: '5px 10px', borderBottom: `1px solid ${C.border}`, background: s === currentSym.toUpperCase() ? C.blue + '11' : 'transparent' }}>
            <button onClick={() => onNavigate(s)} style={{ flex: 1, textAlign: 'left', background: 'transparent', border: 'none', color: s === currentSym.toUpperCase() ? C.blue : C.text, fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace', letterSpacing: '0.06em' }}>{s}</button>
            <button onClick={() => removeSym(s)} style={{ background: 'transparent', border: 'none', color: C.dim, cursor: 'pointer', fontSize: 13, padding: '0 2px' }} title="Remove">x</button>
          </div>
        ))}
      </div>

      {/* Add field */}
      <div style={{ padding: '8px 10px', borderTop: `1px solid ${C.border}`, flexShrink: 0 }}>
        {currentSym && active && !active.symbols.includes(currentSym.toUpperCase()) && (
          <button onClick={() => { if (!active.symbols.includes(currentSym.toUpperCase())) upd(wls.map(w => w.id === active.id ? { ...w, symbols: [...w.symbols, currentSym.toUpperCase()] } : w)) }}
            style={{ width: '100%', marginBottom: 6, padding: '4px', borderRadius: 3, fontSize: 10, border: `1px solid ${C.green}44`, background: C.green + '11', color: C.green, cursor: 'pointer', fontFamily: 'monospace' }}>
            + Add {currentSym.toUpperCase()}
          </button>
        )}
        <div style={{ display: 'flex', gap: 4 }}>
          <input value={addVal} onChange={e => setAddVal(e.target.value.toUpperCase())} onKeyDown={e => e.key === 'Enter' && addSym()} placeholder="Symbol..."
            style={{ flex: 1, padding: '4px 6px', borderRadius: 3, border: `1px solid ${C.border}`, background: C.cell, color: C.text, fontSize: 11, fontFamily: 'monospace', outline: 'none' }} />
          <button onClick={addSym} style={{ padding: '4px 9px', borderRadius: 3, fontSize: 10, border: `1px solid ${C.blue}`, background: C.blue + '22', color: C.blue, cursor: 'pointer' }}>Add</button>
        </div>
      </div>
    </div>
  )
}

// ── Chart styles — platform dark theme applied to KLineChart Pro ──────────────

const CHART_STYLES = {
  grid: {
    horizontal: { color: '#1E2332' },
    vertical:   { color: '#1E2332' },
  },
  candle: {
    bar: {
      upColor:       '#22C55E',
      downColor:     '#EF4444',
      noChangeColor: '#64748B',
    },
    area: { lineColor: '#3B82F6', backgroundColor: [{ offset: 0, color: '#3B82F620' }, { offset: 1, color: '#3B82F600' }] },
  },
  indicator: {
    ohlc: { upColor: '#22C55E', downColor: '#EF4444', noChangeColor: '#64748B' },
  },
  xAxis: {
    axisLine:    { color: '#1E2332' },
    tickLine:    { color: '#1E2332' },
    tickText:    { color: '#64748B' },
  },
  yAxis: {
    axisLine:    { color: '#1E2332' },
    tickLine:    { color: '#1E2332' },
    tickText:    { color: '#64748B' },
  },
  crosshair: {
    horizontal: { line: { color: '#374151' }, text: { backgroundColor: '#1C2130', color: '#E2E8F0', borderColor: '#374151' } },
    vertical:   { line: { color: '#374151' }, text: { backgroundColor: '#1C2130', color: '#E2E8F0', borderColor: '#374151' } },
  },
}

// ── FullChartPage ─────────────────────────────────────────────────────────────

export function FullChartPage() {
  const { symbol: sym = '' } = useParams<{ symbol: string }>()
  const [searchParams]       = useSearchParams()
  const navigate             = useNavigate()
  const initTf               = searchParams.get('tf') ?? '1D'

  const [showWL,     setShowWL]     = useState(false)
  const [snapFlash,  setSnapFlash]  = useState(false)
  const [loading,    setLoading]    = useState(true)

  const containerRef = useRef<HTMLDivElement>(null)
  const proRef       = useRef<KLineChartPro | null>(null)

  // ── Create / destroy chart whenever symbol changes ──────────────────────────
  useEffect(() => {
    if (!containerRef.current || !sym) return

    // Clear any previous chart
    if (containerRef.current) containerRef.current.innerHTML = ''
    proRef.current = null
    setLoading(true)

    const initPeriod = TF_TO_PERIOD[initTf] ?? TF_TO_PERIOD['1D']

    const pro = new KLineChartPro({
      container:       containerRef.current,
      theme:           'dark',
      locale:          'en-US',
      timezone:        'UTC',
      symbol: {
        ticker:    sym.toUpperCase(),
        shortName: sym.toUpperCase(),
        name:      sym.toUpperCase(),
        exchange:  'NSE',
        market:    'stocks',
        priceCurrency: 'INR',
      },
      period:  initPeriod,
      periods: PERIODS,
      styles:  CHART_STYLES as any,
      drawingBarVisible: true,
      mainIndicators: ['EMA'],
      subIndicators:  ['VOL', 'MACD'],
      datafeed: new OurDatafeed(),
    })

    proRef.current = pro
    setLoading(false)

    return () => {
      // Dispose underlying klinecharts instance via the private _chartApi ref
      const chartApi = (pro as any)?._chartApi
      if (chartApi) {
        try { dispose(chartApi) } catch { /* ignore */ }
      }
      if (containerRef.current) containerRef.current.innerHTML = ''
      proRef.current = null
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sym])

  // ── Watchlist navigation → change symbol ───────────────────────────────────
  const goSymbol = useCallback((s: string) => {
    // setPeriod on existing instance so it doesn't flicker
    const tf = proRef.current?.getPeriod()?.text ?? '1D'
    navigate(`/fullchart/${s.toUpperCase()}?tf=${tf}`)
  }, [navigate])

  // ── Snapshot — composite all chart canvases by screen position ─────────────
  const takeSnapshot = useCallback(() => {
    const container = containerRef.current
    if (!container) return
    try {
      const rect     = container.getBoundingClientRect()
      const canvases = Array.from(container.querySelectorAll('canvas'))
        .filter(c => c.width > 100 && c.height > 50)
      if (!canvases.length) return

      const out = document.createElement('canvas')
      out.width  = Math.round(rect.width)
      out.height = Math.round(rect.height)
      const ctx = out.getContext('2d')!
      ctx.fillStyle = C.bg
      ctx.fillRect(0, 0, out.width, out.height)

      for (const c of canvases) {
        const cr = c.getBoundingClientRect()
        const x  = Math.round(cr.left - rect.left)
        const y  = Math.round(cr.top  - rect.top)
        try {
          ctx.drawImage(c, x, y, Math.round(cr.width), Math.round(cr.height))
        } catch { /* cross-origin safety */ }
      }

      const url = out.toDataURL('image/png')
      const a   = document.createElement('a')
      a.href     = url
      a.download = `${sym.toUpperCase()}-${new Date().toISOString().slice(0, 10)}.png`
      document.body.appendChild(a); a.click(); document.body.removeChild(a)
      setSnapFlash(true); setTimeout(() => setSnapFlash(false), 800)
    } catch { /* ignore */ }
  }, [sym])

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100dvh', background: C.bg, overflow: 'hidden', fontFamily: 'monospace' }}>

      {/* ── Top bar ─────────────────────────────────────────────────────── */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, padding: '6px 12px',
        background: C.panel, borderBottom: `1px solid ${C.border}`, flexShrink: 0,
        flexWrap: 'wrap',
      }}>
        {/* Back */}
        <button onClick={() => navigate(-1)} style={{
          padding: '4px 10px', borderRadius: 4, border: `1px solid ${C.border}`,
          background: 'transparent', color: C.sub, cursor: 'pointer', fontSize: 11,
        }}>&larr; Back</button>

        {/* Symbol */}
        <span style={{ fontSize: 15, fontWeight: 900, color: C.text, letterSpacing: 2, minWidth: 90 }}>
          {sym.toUpperCase()}
        </span>

        <div style={{ width: 1, height: 16, background: C.border }} />

        <span style={{ fontSize: 10, color: C.sub }}>NSE</span>
        <span style={{ fontSize: 10, color: C.sub }}>INR</span>

        {loading && <span style={{ fontSize: 10, color: C.amber }}>Loading...</span>}

        {/* Right-side actions */}
        <div style={{ flex: 1 }} />

        {/* Snapshot */}
        <button onClick={takeSnapshot} title="Save chart as PNG" style={{
          padding: '4px 12px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
          border: `1px solid ${snapFlash ? C.green : C.border}`,
          background: snapFlash ? C.green + '22' : 'transparent',
          color: snapFlash ? C.green : C.sub, transition: 'all .2s',
        }}>{snapFlash ? 'Saved!' : 'Snapshot PNG'}</button>

        {/* Watchlist toggle */}
        <button onClick={() => setShowWL(v => !v)} style={{
          padding: '4px 12px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
          border: `1px solid ${showWL ? C.purple : C.border}`,
          background: showWL ? C.purple + '22' : 'transparent',
          color: showWL ? C.purple : C.sub, fontWeight: showWL ? 700 : 400,
        }}>
          {showWL ? 'Hide Watchlist' : 'Watchlist'}
        </button>
      </div>

      {/* ── Content row ─────────────────────────────────────────────────── */}
      <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'row', overflow: 'hidden' }}>

        {/* KLineChart Pro renders into this container */}
        <div ref={containerRef} style={{ flex: 1, minWidth: 0, minHeight: 0 }} />

        {/* Watchlist panel */}
        {showWL && <WatchlistPanel currentSym={sym} onNavigate={goSymbol} />}
      </div>
    </div>
  )
}
