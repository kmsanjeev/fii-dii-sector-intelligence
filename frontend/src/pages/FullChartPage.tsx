/**
 * FullChartPage — full-viewport chart powered by KLineChart Pro
 * Route: /fullchart/:symbol  (outside AppShell)
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { KLineChartPro } from '@klinecharts/pro'
import type { Datafeed, SymbolInfo, Period, DatafeedSubscribeCallback } from '@klinecharts/pro'
import type { KLineData } from 'klinecharts'
import { dispose } from 'klinecharts'
import '@klinecharts/pro/dist/klinecharts-pro.css'
import '../indicators/customIndicators'   // registers VWAP, Supertrend, HMA into Pro's picker
import { api } from '../api/client'

// ── Periods ───────────────────────────────────────────────────────────────────

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
  '5M': PERIODS[0], '15M': PERIODS[1], '1H': PERIODS[2],
  '1D': PERIODS[3], '1W':  PERIODS[4], '1M': PERIODS[5], '3M': PERIODS[6],
}

// ── UI palette — TradingView dark ─────────────────────────────────────────────

const C = {
  bg:     '#131722',
  panel:  '#1e222d',
  cell:   '#2a2e39',
  border: '#2a2e39',
  text:   '#d1d4dc',
  sub:    '#787b86',
  dim:    '#434651',
  green:  '#26a69a',
  red:    '#ef5350',
  amber:  '#f7a600',
  blue:   '#1976d2',
  purple: '#7b61ff',
  orange: '#f97316',
}

// ── Period → TF ───────────────────────────────────────────────────────────────

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

// ── Bar time → Unix ms ────────────────────────────────────────────────────────
// KLineChart Pro's picker skips UTC+5:30; chart is set to UTC and IST times are
// baked in directly so "09:15 IST" renders as "09:15" on the UTC axis.

function barTimeToMs(t: string | number): number {
  if (typeof t === 'number') return t > 1e12 ? t : t * 1000
  if (t.includes('T')) {
    const bare = t.replace(/([+-]\d{2}:\d{2}|Z)$/, '')
    return new Date(bare + 'Z').getTime()
  }
  return new Date(t + 'T00:00:00Z').getTime()
}

// ── Datafeed ──────────────────────────────────────────────────────────────────

class OurDatafeed implements Datafeed {
  private _timers = new Map<string, ReturnType<typeof setInterval>>()

  async searchSymbols(search?: string): Promise<SymbolInfo[]> {
    if (!search?.trim()) return []
    try {
      const r = await api.get<{ symbols: { SYMBOL: string; COMPANY_NAME: string }[] }>(
        '/charts/symbols', { params: { q: search.trim().toUpperCase() } }
      )
      return (r.data.symbols ?? []).map(s => ({
        ticker: s.SYMBOL, shortName: s.SYMBOL,
        name: s.COMPANY_NAME ?? s.SYMBOL, exchange: 'NSE', market: 'stocks',
      }))
    } catch { return [] }
  }

  async getHistoryKLineData(symbol: SymbolInfo, period: Period, _from: number, _to: number): Promise<KLineData[]> {
    try {
      const r = await api.get<{ bars: Array<{ time: string | number; open: number; high: number; low: number; close: number; volume: number }> }>(
        '/charts/ohlcv', { params: { symbol: symbol.ticker, timeframe: periodToTF(period) } }
      )
      return (r.data.bars ?? []).map(b => ({
        timestamp: barTimeToMs(b.time),
        open: b.open, high: b.high, low: b.low, close: b.close, volume: b.volume ?? 0,
      }))
    } catch { return [] }
  }

  subscribe(symbol: SymbolInfo, period: Period, callback: DatafeedSubscribeCallback): void {
    const key = `${symbol.ticker}_${period.text}`
    this._timers.set(key, setInterval(async () => {
      try {
        const r = await api.get<{ bars: any[] }>('/charts/ohlcv', { params: { symbol: symbol.ticker, timeframe: periodToTF(period) } })
        const bars = r.data.bars ?? []; if (!bars.length) return
        const last = bars[bars.length - 1]
        callback({ timestamp: barTimeToMs(last.time), open: last.open, high: last.high, low: last.low, close: last.close, volume: last.volume ?? 0 })
      } catch { /* ignore */ }
    }, 60_000))
  }

  unsubscribe(symbol: SymbolInfo, period: Period): void {
    const key = `${symbol.ticker}_${period.text}`
    const t = this._timers.get(key); if (t) { clearInterval(t); this._timers.delete(key) }
  }
}

// ── Chart Settings ────────────────────────────────────────────────────────────

export interface ChartSettings {
  candleType:    'candle_solid' | 'candle_stroke' | 'ohlc' | 'area'
  upColor:       string
  downColor:     string
  noChangeColor: string
  upWickColor:   string
  downWickColor: string
  showGridH:     boolean
  showGridV:     boolean
  gridColor:     string
  fontFamily:    string
  fontSize:      number
  fontWeight:    string
  axisTextColor: string
  axisLineColor: string
  yAxisRight:    boolean
  crosshairColor:  string
  crosshairTextBg: string
  showLastPrice:   boolean
  showHighLow:     boolean
}

// TradingView canonical dark palette
const TV_PRESET: ChartSettings = {
  candleType:    'candle_solid',
  upColor:       '#26a69a',
  downColor:     '#ef5350',
  noChangeColor: '#999999',
  upWickColor:   '#26a69a',
  downWickColor: '#ef5350',
  showGridH:     true,
  showGridV:     false,
  gridColor:     '#1e222d',
  fontFamily:    "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  fontSize:      11,
  fontWeight:    'normal',
  axisTextColor: '#b2b5be',
  axisLineColor: '#2a2e39',
  yAxisRight:    true,
  crosshairColor:  '#758696',
  crosshairTextBg: '#131722',
  showLastPrice:   true,
  showHighLow:     true,
}

// Platform signature palette
const PLATFORM_PRESET: ChartSettings = {
  candleType:    'candle_solid',
  upColor:       '#22C55E',
  downColor:     '#EF4444',
  noChangeColor: '#64748B',
  upWickColor:   '#22C55E',
  downWickColor: '#EF4444',
  showGridH:     true,
  showGridV:     false,
  gridColor:     '#1E2332',
  fontFamily:    'monospace',
  fontSize:      11,
  fontWeight:    'normal',
  axisTextColor: '#64748B',
  axisLineColor: '#1E2332',
  yAxisRight:    true,
  crosshairColor:  '#374151',
  crosshairTextBg: '#1C2130',
  showLastPrice:   true,
  showHighLow:     true,
}

const DEFAULT_SETTINGS = TV_PRESET
const SETTINGS_KEY = 'cfip-chart-settings'

function loadSettings(): ChartSettings {
  try {
    const raw = localStorage.getItem(SETTINGS_KEY)
    if (raw) return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) }
  } catch { /* ignore */ }
  return DEFAULT_SETTINGS
}
function saveSettings(s: ChartSettings) {
  try { localStorage.setItem(SETTINGS_KEY, JSON.stringify(s)) } catch { /* ignore */ }
}

function buildStyles(s: ChartSettings): object {
  const font = { family: s.fontFamily, size: s.fontSize, weight: s.fontWeight }
  return {
    grid: {
      horizontal: { show: s.showGridH, color: s.gridColor },
      vertical:   { show: s.showGridV, color: s.gridColor },
    },
    candle: {
      type: s.candleType,
      bar: {
        upColor:             s.upColor,
        downColor:           s.downColor,
        noChangeColor:       s.noChangeColor,
        upBorderColor:       s.upColor,
        downBorderColor:     s.downColor,
        noChangeBorderColor: s.noChangeColor,
        upWickColor:         s.upWickColor,
        downWickColor:       s.downWickColor,
        noChangeWickColor:   s.noChangeColor,
      },
      area: {
        lineColor: s.upColor,
        backgroundColor: [
          { offset: 0, color: s.upColor + '28' },
          { offset: 1, color: s.upColor + '00' },
        ],
      },
      priceMark: {
        show: true,
        high: { show: s.showHighLow, color: s.axisTextColor, textFamily: s.fontFamily, textSize: s.fontSize, textWeight: s.fontWeight },
        low:  { show: s.showHighLow, color: s.axisTextColor, textFamily: s.fontFamily, textSize: s.fontSize, textWeight: s.fontWeight },
        last: {
          show: s.showLastPrice,
          line: { show: s.showLastPrice },
          text: { show: s.showLastPrice, ...font },
        },
      },
      tooltip: { text: { ...font, color: s.axisTextColor } },
    },
    indicator: {
      ohlc: { upColor: s.upColor, downColor: s.downColor, noChangeColor: s.noChangeColor },
      lastValueMark: {
        show: true,
        text: { show: true, ...font, color: s.axisTextColor, borderColor: s.axisLineColor, backgroundColor: s.crosshairTextBg },
      },
      tooltip: { text: { ...font, color: s.axisTextColor } },
    },
    xAxis: {
      axisLine: { color: s.axisLineColor },
      tickLine: { color: s.axisLineColor },
      tickText: { ...font, color: s.axisTextColor },
    },
    yAxis: {
      position: s.yAxisRight ? 'right' : 'left',
      axisLine: { color: s.axisLineColor },
      tickLine: { color: s.axisLineColor },
      tickText: { ...font, color: s.axisTextColor },
    },
    separator: { color: s.axisLineColor },
    crosshair: {
      horizontal: {
        line: { color: s.crosshairColor },
        text: { ...font, backgroundColor: s.crosshairTextBg, color: s.axisTextColor, borderColor: s.crosshairColor },
      },
      vertical: {
        line: { color: s.crosshairColor },
        text: { ...font, backgroundColor: s.crosshairTextBg, color: s.axisTextColor, borderColor: s.crosshairColor },
      },
    },
  }
}

// ── Settings Panel ────────────────────────────────────────────────────────────

const FONT_FAMILIES = [
  { label: 'System UI (TradingView)',  value: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" },
  { label: 'Monospace (platform)',     value: 'monospace' },
  { label: 'Courier New',             value: "'Courier New', monospace" },
  { label: 'Arial',                   value: "'Arial', sans-serif" },
  { label: 'Georgia (serif)',         value: "'Georgia', serif" },
  { label: 'Verdana',                 value: "'Verdana', sans-serif" },
]

const FONT_WEIGHTS = [
  { label: 'Normal',    value: 'normal' },
  { label: 'Medium',    value: '500' },
  { label: 'SemiBold',  value: '600' },
  { label: 'Bold',      value: 'bold' },
]

const CANDLE_TYPES: { label: string; value: ChartSettings['candleType'] }[] = [
  { label: 'Solid',  value: 'candle_solid'  },
  { label: 'Hollow', value: 'candle_stroke' },
  { label: 'OHLC',   value: 'ohlc'          },
  { label: 'Area',   value: 'area'          },
]

function SettingsPanel({ settings, onChange }: {
  settings: ChartSettings
  onChange: (patch: Partial<ChartSettings>) => void
}) {
  const upd = onChange

  const row: React.CSSProperties = { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 12px', borderBottom: `1px solid ${C.border}` }
  const lbl: React.CSSProperties = { fontSize: 11, color: C.sub, flex: 1 }
  const ctrl: React.CSSProperties = { display: 'flex', alignItems: 'center', gap: 6 }

  const Section = ({ title }: { title: string }) => (
    <div style={{ padding: '7px 12px 5px', background: C.cell + 'aa', borderBottom: `1px solid ${C.border}` }}>
      <span style={{ fontSize: 9, fontWeight: 800, color: C.blue, letterSpacing: '0.12em', textTransform: 'uppercase' }}>{title}</span>
    </div>
  )

  const ColorSwatch = ({ value, onChange: oc }: { value: string; onChange: (v: string) => void }) => (
    <label style={{ position: 'relative', display: 'inline-block', cursor: 'pointer' }}>
      <div style={{ width: 22, height: 22, borderRadius: 4, background: value, border: `2px solid ${C.border}` }} />
      <input type="color" value={value} onChange={e => oc(e.target.value)}
        style={{ position: 'absolute', inset: 0, opacity: 0, cursor: 'pointer', width: '100%', height: '100%' }} />
    </label>
  )

  const Toggle = ({ value, onChange: oc }: { value: boolean; onChange: (v: boolean) => void }) => (
    <div onClick={() => oc(!value)} style={{ width: 34, height: 18, borderRadius: 9, cursor: 'pointer', position: 'relative', background: value ? C.green : C.dim, transition: 'background .2s' }}>
      <div style={{ position: 'absolute', top: 2, left: value ? 16 : 2, width: 14, height: 14, borderRadius: '50%', background: C.text, transition: 'left .2s' }} />
    </div>
  )

  const sel: React.CSSProperties = { padding: '3px 6px', borderRadius: 3, border: `1px solid ${C.border}`, background: C.cell, color: C.text, fontSize: 10, cursor: 'pointer', outline: 'none', width: '100%' }

  const isTV  = JSON.stringify(settings) === JSON.stringify(TV_PRESET)
  const isPlt = JSON.stringify(settings) === JSON.stringify(PLATFORM_PRESET)

  return (
    <div style={{ width: 260, flexShrink: 0, borderLeft: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', background: C.panel, overflowY: 'auto' }}>

      {/* Header */}
      <div style={{ padding: '8px 12px', borderBottom: `1px solid ${C.border}`, display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
        <span style={{ fontSize: 11, fontWeight: 700, color: C.text, letterSpacing: '0.06em', flex: 1 }}>Chart Settings</span>
        <button onClick={() => upd({ ...DEFAULT_SETTINGS })} style={{ padding: '2px 7px', borderRadius: 3, fontSize: 9, cursor: 'pointer', border: `1px solid ${C.dim}`, background: 'transparent', color: C.sub }}>Reset</button>
      </div>

      {/* ── Presets */}
      <Section title="Presets" />
      <div style={{ padding: '8px 12px', borderBottom: `1px solid ${C.border}`, display: 'flex', gap: 6 }}>
        <button onClick={() => upd({ ...TV_PRESET })} style={{
          flex: 1, padding: '6px 4px', borderRadius: 4, fontSize: 10, cursor: 'pointer', fontWeight: isTV ? 700 : 400,
          border: `1px solid ${isTV ? C.green : C.border}`,
          background: isTV ? C.green + '18' : 'transparent', color: isTV ? C.green : C.sub,
        }}>
          <div style={{ width: 10, height: 10, borderRadius: 2, background: '#26a69a', display: 'inline-block', marginRight: 5, verticalAlign: 'middle' }} />
          TradingView
        </button>
        <button onClick={() => upd({ ...PLATFORM_PRESET })} style={{
          flex: 1, padding: '6px 4px', borderRadius: 4, fontSize: 10, cursor: 'pointer', fontWeight: isPlt ? 700 : 400,
          border: `1px solid ${isPlt ? C.purple : C.border}`,
          background: isPlt ? C.purple + '18' : 'transparent', color: isPlt ? C.purple : C.sub,
        }}>
          <div style={{ width: 10, height: 10, borderRadius: 2, background: '#22C55E', display: 'inline-block', marginRight: 5, verticalAlign: 'middle' }} />
          Platform
        </button>
      </div>

      {/* ── Candle Type */}
      <Section title="Candle Style" />
      <div style={{ padding: '8px 12px', borderBottom: `1px solid ${C.border}`, display: 'flex', flexWrap: 'wrap', gap: 5 }}>
        {CANDLE_TYPES.map(ct => (
          <button key={ct.value} onClick={() => upd({ candleType: ct.value })} style={{
            padding: '4px 10px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
            border: `1px solid ${settings.candleType === ct.value ? C.blue : C.border}`,
            background: settings.candleType === ct.value ? C.blue + '22' : 'transparent',
            color: settings.candleType === ct.value ? C.blue : C.sub,
            fontWeight: settings.candleType === ct.value ? 700 : 400,
          }}>{ct.label}</button>
        ))}
      </div>

      {/* ── Candle Colors */}
      <Section title="Candle Colors" />
      {([
        ['Bullish (Up)',   'upColor',       'upWickColor'  ],
        ['Bearish (Down)', 'downColor',     'downWickColor'],
        ['No-change',      'noChangeColor', null           ],
      ] as const).map(([label, key, wickKey]) => (
        <div key={key} style={row}>
          <span style={lbl}>{label}</span>
          <div style={ctrl}>
            {wickKey && <ColorSwatch value={(settings as any)[wickKey]} onChange={v => upd({ [wickKey]: v } as any)} />}
            <ColorSwatch value={(settings as any)[key]}
              onChange={v => upd(wickKey ? { [key]: v, [wickKey]: v } as any : { [key]: v } as any)} />
          </div>
        </div>
      ))}
      <div style={{ padding: '4px 12px 6px', borderBottom: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 9, color: C.dim }}>Left swatch = wick, right = body. Changing body also updates wick.</div>
      </div>

      {/* ── Grid */}
      <Section title="Grid" />
      <div style={row}><span style={lbl}>Horizontal</span><div style={ctrl}><Toggle value={settings.showGridH} onChange={v => upd({ showGridH: v })} /></div></div>
      <div style={row}><span style={lbl}>Vertical</span>  <div style={ctrl}><Toggle value={settings.showGridV} onChange={v => upd({ showGridV: v })} /></div></div>
      <div style={row}><span style={lbl}>Grid Color</span><div style={ctrl}><ColorSwatch value={settings.gridColor} onChange={v => upd({ gridColor: v })} /></div></div>

      {/* ── Font */}
      <Section title="Font" />
      <div style={{ padding: '6px 12px', borderBottom: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 10, color: C.sub, marginBottom: 4 }}>Family</div>
        <select value={settings.fontFamily} onChange={e => upd({ fontFamily: e.target.value })} style={sel}>
          {FONT_FAMILIES.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
      </div>
      <div style={{ padding: '6px 12px', borderBottom: `1px solid ${C.border}` }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
          <span style={{ fontSize: 10, color: C.sub, flex: 1 }}>Size</span>
          <span style={{ fontSize: 11, fontWeight: 700, color: C.text }}>{settings.fontSize}px</span>
        </div>
        <input type="range" min={9} max={16} value={settings.fontSize} onChange={e => upd({ fontSize: Number(e.target.value) })}
          style={{ width: '100%', accentColor: C.blue, cursor: 'pointer' }} />
      </div>
      <div style={{ padding: '6px 12px', borderBottom: `1px solid ${C.border}` }}>
        <div style={{ fontSize: 10, color: C.sub, marginBottom: 4 }}>Weight</div>
        <select value={settings.fontWeight} onChange={e => upd({ fontWeight: e.target.value })} style={sel}>
          {FONT_WEIGHTS.map(w => <option key={w.value} value={w.value}>{w.label}</option>)}
        </select>
      </div>

      {/* ── Axes */}
      <Section title="Axes" />
      <div style={row}><span style={lbl}>Text Color</span> <div style={ctrl}><ColorSwatch value={settings.axisTextColor} onChange={v => upd({ axisTextColor: v })} /></div></div>
      <div style={row}><span style={lbl}>Line Color</span> <div style={ctrl}><ColorSwatch value={settings.axisLineColor} onChange={v => upd({ axisLineColor: v })} /></div></div>
      <div style={row}>
        <span style={lbl}>Y-Axis Side</span>
        <div style={ctrl}>
          {(['Left', 'Right'] as const).map(side => (
            <button key={side} onClick={() => upd({ yAxisRight: side === 'Right' })} style={{
              padding: '3px 10px', borderRadius: 3, fontSize: 10, cursor: 'pointer',
              border: `1px solid ${(side === 'Right') === settings.yAxisRight ? C.orange : C.border}`,
              background: (side === 'Right') === settings.yAxisRight ? C.orange + '22' : 'transparent',
              color: (side === 'Right') === settings.yAxisRight ? C.orange : C.sub,
            }}>{side}</button>
          ))}
        </div>
      </div>

      {/* ── Crosshair */}
      <Section title="Crosshair" />
      <div style={row}><span style={lbl}>Line Color</span>    <div style={ctrl}><ColorSwatch value={settings.crosshairColor}  onChange={v => upd({ crosshairColor: v })} /></div></div>
      <div style={row}><span style={lbl}>Label Background</span><div style={ctrl}><ColorSwatch value={settings.crosshairTextBg} onChange={v => upd({ crosshairTextBg: v })} /></div></div>

      {/* ── Price Marks */}
      <Section title="Price Marks" />
      <div style={row}><span style={lbl}>Last Price Line</span><div style={ctrl}><Toggle value={settings.showLastPrice} onChange={v => upd({ showLastPrice: v })} /></div></div>
      <div style={row}><span style={lbl}>High / Low Labels</span><div style={ctrl}><Toggle value={settings.showHighLow} onChange={v => upd({ showHighLow: v })} /></div></div>

      <div style={{ flex: 1 }} />

      {/* Preview bar */}
      <div style={{ padding: '10px 12px', borderTop: `1px solid ${C.border}`, flexShrink: 0 }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <div style={{ width: 10, height: 18, borderRadius: 2, background: settings.upColor }} />
          <div style={{ width: 10, height: 18, borderRadius: 2, background: settings.downColor }} />
          <span style={{ fontSize: settings.fontSize, fontFamily: settings.fontFamily, fontWeight: settings.fontWeight, color: settings.axisTextColor, marginLeft: 4 }}>
            09:15 NSE
          </span>
        </div>
      </div>
    </div>
  )
}

// ── Watchlist ─────────────────────────────────────────────────────────────────

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

function WatchlistPanel({ currentSym, onNavigate }: { currentSym: string; onNavigate: (s: string) => void }) {
  const [wls,      setWls]      = useState<WLEntry[]>(loadWL)
  const [activeId, setActiveId] = useState<string>(() => loadWL()[0]?.id ?? 'default')
  const [addVal,   setAddVal]   = useState('')
  const [renaming, setRenaming] = useState(false)
  const [rnVal,    setRnVal]    = useState('')

  const active = wls.find(w => w.id === activeId) ?? wls[0]
  const upd = (next: WLEntry[]) => { setWls(next); saveWL(next) }
  const addSym = () => {
    const s = addVal.trim().toUpperCase(); if (!s || !active) return
    if (!active.symbols.includes(s)) upd(wls.map(w => w.id === active.id ? { ...w, symbols: [...w.symbols, s] } : w))
    setAddVal('')
  }
  const removeSym = (s: string) => upd(wls.map(w => w.id === active.id ? { ...w, symbols: w.symbols.filter(x => x !== s) } : w))
  const newList  = () => { const id = Date.now().toString(); const nx = [...wls, { id, name: `List ${wls.length + 1}`, symbols: [] }]; upd(nx); setActiveId(id) }
  const delList  = () => { if (wls.length <= 1) return; const nx = wls.filter(w => w.id !== active.id); upd(nx); setActiveId(nx[0].id) }
  const commitRn = () => { const n = rnVal.trim(); if (n) upd(wls.map(w => w.id === active.id ? { ...w, name: n } : w)); setRenaming(false) }
  const btn = (color = C.sub): React.CSSProperties => ({ padding: '3px 7px', borderRadius: 3, fontSize: 10, cursor: 'pointer', border: `1px solid ${color}33`, background: 'transparent', color })

  return (
    <div style={{ width: 240, flexShrink: 0, borderLeft: `1px solid ${C.border}`, display: 'flex', flexDirection: 'column', background: C.panel }}>
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
            }}>{w.name}</button>
          ))}
        </div>
      </div>
      <div style={{ padding: '6px 10px', borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
        {renaming ? (
          <div style={{ display: 'flex', gap: 4 }}>
            <input value={rnVal} onChange={e => setRnVal(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') commitRn(); if (e.key === 'Escape') setRenaming(false) }}
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
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {active?.symbols.length === 0 && (
          <div style={{ padding: '20px 10px', textAlign: 'center', color: C.dim, fontSize: 10 }}>No symbols yet.<br />Add below.</div>
        )}
        {active?.symbols.map(s => (
          <div key={s} style={{ display: 'flex', alignItems: 'center', padding: '5px 10px', borderBottom: `1px solid ${C.border}`, background: s === currentSym.toUpperCase() ? C.blue + '11' : 'transparent' }}>
            <button onClick={() => onNavigate(s)} style={{ flex: 1, textAlign: 'left', background: 'transparent', border: 'none', color: s === currentSym.toUpperCase() ? C.blue : C.text, fontSize: 12, fontWeight: 700, cursor: 'pointer', fontFamily: 'monospace', letterSpacing: '0.06em' }}>{s}</button>
            <button onClick={() => removeSym(s)} style={{ background: 'transparent', border: 'none', color: C.dim, cursor: 'pointer', fontSize: 13, padding: '0 2px' }}>x</button>
          </div>
        ))}
      </div>
      <div style={{ padding: '8px 10px', borderTop: `1px solid ${C.border}`, flexShrink: 0 }}>
        {currentSym && active && !active.symbols.includes(currentSym.toUpperCase()) && (
          <button onClick={() => upd(wls.map(w => w.id === active.id ? { ...w, symbols: [...w.symbols, currentSym.toUpperCase()] } : w))}
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

// ── FullChartPage ─────────────────────────────────────────────────────────────

export function FullChartPage() {
  const { symbol: sym = '' } = useParams<{ symbol: string }>()
  const [searchParams]       = useSearchParams()
  const navigate             = useNavigate()
  const initTf               = searchParams.get('tf') ?? '1D'

  const [settings,     setSettings]     = useState<ChartSettings>(loadSettings)
  const [showWL,       setShowWL]       = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [snapFlash,    setSnapFlash]    = useState(false)
  const [loading,      setLoading]      = useState(true)

  const containerRef = useRef<HTMLDivElement>(null)
  const proRef       = useRef<KLineChartPro | null>(null)

  // ── Create / destroy chart when symbol changes ──────────────────────────────
  useEffect(() => {
    if (!containerRef.current || !sym) return
    containerRef.current.innerHTML = ''
    proRef.current = null
    setLoading(true)

    const pro = new KLineChartPro({
      container:  containerRef.current,
      theme:      'dark',
      locale:     'en-US',
      timezone:   'UTC',
      watermark:  'NSE',
      symbol: {
        ticker: sym.toUpperCase(), shortName: sym.toUpperCase(),
        name: sym.toUpperCase(), exchange: 'NSE', market: 'stocks', priceCurrency: 'INR',
      },
      period:            TF_TO_PERIOD[initTf] ?? TF_TO_PERIOD['1D'],
      periods:           PERIODS,
      styles:            buildStyles(settings) as any,
      drawingBarVisible: true,
      mainIndicators:    ['EMA'],
      subIndicators:     ['VOL', 'MACD', 'RSI'],
      datafeed:          new OurDatafeed(),
    })

    // ── P1: Symbol URL sync ──────────────────────────────────────────────────
    // When user searches and selects a symbol via Pro's built-in UI, navigate to
    // the new symbol URL instead of letting Pro update internally. This keeps the
    // URL in sync and the Back button correct.
    pro.setSymbol = (symbol: SymbolInfo) => {
      const tf = pro.getPeriod()?.text ?? '1D'
      navigate(`/fullchart/${symbol.ticker.toUpperCase()}?tf=${tf}`, { replace: true })
    }

    // ── P3: Period URL sync ──────────────────────────────────────────────────
    // Keep ?tf= in the URL current so a page refresh restores the same period.
    const origSetPeriod = pro.setPeriod.bind(pro)
    pro.setPeriod = (period: Period) => {
      origSetPeriod(period)
      navigate(`/fullchart/${sym.toUpperCase()}?tf=${period.text}`, { replace: true })
    }

    proRef.current = pro
    setLoading(false)

    return () => {
      const chartApi = (pro as any)?._chartApi
      if (chartApi) { try { dispose(chartApi) } catch { /* ignore */ } }
      if (containerRef.current) containerRef.current.innerHTML = ''
      proRef.current = null
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sym])

  // ── Apply settings live ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!proRef.current) return
    try { proRef.current.setStyles(buildStyles(settings) as any) } catch { /* ignore */ }
    saveSettings(settings)
  }, [settings])

  const handleSettings = useCallback((patch: Partial<ChartSettings>) => {
    setSettings(prev => ({ ...prev, ...patch }))
  }, [])

  const goSymbol = useCallback((s: string) => {
    const tf = proRef.current?.getPeriod()?.text ?? '1D'
    navigate(`/fullchart/${s.toUpperCase()}?tf=${tf}`)
  }, [navigate])

  // ── Snapshot ────────────────────────────────────────────────────────────────
  const takeSnapshot = useCallback(() => {
    const container = containerRef.current; if (!container) return
    try {
      const rect = container.getBoundingClientRect()
      const canvases = Array.from(container.querySelectorAll('canvas')).filter(c => c.width > 100 && c.height > 50)
      if (!canvases.length) return
      const out = document.createElement('canvas')
      out.width = Math.round(rect.width); out.height = Math.round(rect.height)
      const ctx = out.getContext('2d')!
      ctx.fillStyle = C.bg; ctx.fillRect(0, 0, out.width, out.height)
      for (const c of canvases) {
        const cr = c.getBoundingClientRect()
        try { ctx.drawImage(c, Math.round(cr.left - rect.left), Math.round(cr.top - rect.top), Math.round(cr.width), Math.round(cr.height)) } catch { /* ignore */ }
      }
      const a = document.createElement('a')
      a.href = out.toDataURL('image/png')
      a.download = `${sym.toUpperCase()}-${new Date().toISOString().slice(0, 10)}.png`
      document.body.appendChild(a); a.click(); document.body.removeChild(a)
      setSnapFlash(true); setTimeout(() => setSnapFlash(false), 800)
    } catch { /* ignore */ }
  }, [sym])

  const topBtn = (active: boolean, color = C.blue): React.CSSProperties => ({
    padding: '4px 11px', borderRadius: 4, fontSize: 10, cursor: 'pointer',
    border: `1px solid ${active ? color : C.border}`,
    background: active ? color + '1a' : 'transparent',
    color: active ? color : C.sub, fontWeight: active ? 700 : 400,
    fontFamily: 'inherit',
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100dvh', background: C.bg, overflow: 'hidden', fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif" }}>

      {/* ── Top bar */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 14px', background: C.panel, borderBottom: `1px solid ${C.border}`, flexShrink: 0 }}>
        <button onClick={() => navigate(-1)} style={{ padding: '4px 10px', borderRadius: 4, border: `1px solid ${C.border}`, background: 'transparent', color: C.sub, cursor: 'pointer', fontSize: 11, fontFamily: 'inherit' }}>
          &larr; Back
        </button>

        <div style={{ width: 1, height: 14, background: C.border }} />

        <span style={{ fontSize: 14, fontWeight: 700, color: C.text, letterSpacing: 1 }}>{sym.toUpperCase()}</span>
        <span style={{ fontSize: 10, color: C.sub }}>NSE</span>
        <span style={{ fontSize: 10, color: C.dim }}>·</span>
        <span style={{ fontSize: 10, color: C.sub }}>INR</span>

        {loading && <span style={{ fontSize: 10, color: C.amber }}>Loading...</span>}
        <div style={{ flex: 1 }} />

        <button onClick={takeSnapshot} style={topBtn(snapFlash, C.green)}>{snapFlash ? 'Saved!' : 'Snapshot'}</button>
        <button onClick={() => { setShowSettings(v => !v); setShowWL(false) }} style={topBtn(showSettings, C.orange)}>Settings</button>
        <button onClick={() => { setShowWL(v => !v); setShowSettings(false) }} style={topBtn(showWL, C.purple)}>Watchlist</button>
      </div>

      {/* ── Content row */}
      <div style={{ flex: 1, minHeight: 0, display: 'flex', overflow: 'hidden' }}>
        <div ref={containerRef} style={{ flex: 1, minWidth: 0, minHeight: 0 }} />
        {showSettings && <SettingsPanel settings={settings} onChange={handleSettings} />}
        {showWL       && <WatchlistPanel currentSym={sym} onNavigate={goSymbol} />}
      </div>
    </div>
  )
}
