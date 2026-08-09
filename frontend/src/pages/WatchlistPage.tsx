import { useState, useMemo, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { fetchAllStocks, type Stock } from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
import { Link } from 'react-router-dom'

const LABELS   = ['ALL', 'BULL_RUN', 'EMERGING', 'ACCUMULATION', 'WATCHLIST', 'NEUTRAL', 'MARKDOWN']
const PER_PAGE = 100

type SortKey = 'bull_run_score' | 'close_now' | 'ret_30d' | 'ret_365d' | 'vol_ratio'
             | 'forward_return_score' | 'rs_30d' | 'delivery_5d_pct' | 'rvol' | 'conviction_score'
type SortDir = 'asc' | 'desc'

function SortHeader({
  label, col, active, dir, onClick, amber,
}: { label: string; col: SortKey; active: boolean; dir: SortDir; onClick: () => void; amber?: boolean }) {
  const isCentered = col === 'bull_run_score' || col === 'forward_return_score'
  return (
    <th
      onClick={onClick}
      style={{
        padding: '6px 10px', textAlign: isCentered ? 'center' : 'right',
        fontSize: 12, fontWeight: 600,
        color: active ? (amber ? '#F59E0B' : '#22C55E') : (amber ? '#92653A' : '#64748B'),
        whiteSpace: 'nowrap', borderBottom: '1px solid #1E2332', cursor: 'pointer',
        userSelect: 'none',
      }}
    >
      {label} {active ? (dir === 'desc' ? ' v' : ' ^') : ''}
    </th>
  )
}

function ActionBadge({ label, trend, oi, rvol, rs30, vsDma50 }: {
  label: string; trend?: string; oi?: string
  rvol?: number | null; rs30?: number | null; vsDma50?: number | null
}) {
  // Algorithmic execution triggers (Phase WL-1) layered over the base signal
  const bullishTrend = trend === 'STRONG_UPTREND' || trend === 'UPTREND'
  const bearishTrend = trend === 'DOWNTREND'
  const bullishOI    = oi === 'LONG_BUILDUP' || oi === 'SHORT_COVERING'
  const bearishOI    = oi === 'SHORT_BUILDUP' || oi === 'LONG_UNWINDING'
  const avoidLabel   = label === 'MARKDOWN'
  const accumLabel   = label === 'ACCUMULATION'
  const strongLabel  = label === 'BULL_RUN'

  let text = 'WATCH'
  let color = '#64748B'
  let bg    = '#1E2332'

  // Priority 1: institutional execution triggers (volume + RS confirmed)
  if (strongLabel && (rvol ?? 0) >= 2.0 && (rs30 ?? -1) > 0) {
    text = 'BUY BRKOUT'; color = '#22D35E'; bg = '#052e16'
  } else if (label === 'EMERGING' && vsDma50 != null && Math.abs(vsDma50) <= 3.0
             && !bearishTrend) {
    text = 'LOW RISK ENTRY'; color = '#0EC4A0'; bg = '#023323'
  // Priority 2: base label/trend/OI logic (unchanged fallbacks)
  } else if (avoidLabel || (bearishTrend && bearishOI)) {
    text = 'EXIT'; color = '#EF4444'; bg = '#1c0000'
  } else if (bearishTrend || (bearishOI && !bullishTrend)) {
    text = 'REDUCE'; color = '#F97316'; bg = '#1c0a00'
  } else if (strongLabel && bullishTrend && bullishOI) {
    text = 'STR BUY'; color = '#22C55E'; bg = '#052e16'
  } else if ((strongLabel || label === 'EMERGING') && bullishTrend) {
    text = 'BUY'; color = '#10B981'; bg = '#022c22'
  } else if (accumLabel) {
    text = 'ACCUM'; color = '#9575CD'; bg = '#1a0a2e'
  } else if (bullishTrend) {
    text = 'HOLD'; color = '#F59E0B'; bg = '#1c1400'
  }

  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: '1px 5px', borderRadius: 2,
      border: `1px solid ${color}44`, color, background: bg,
    }}>
      {text}
    </span>
  )
}

function TrendBadge({ signal }: { signal?: string }) {
  if (!signal) return null
  const MAP: Record<string, { color: string; short: string }> = {
    STRONG_UPTREND:    { color: '#22C55E', short: 'SUP' },
    UPTREND:           { color: '#10B981', short: 'UP'  },
    CONSOLIDATING:     { color: '#F59E0B', short: 'CON' },
    DOWNTREND:         { color: '#EF4444', short: 'DWN' },
    INSUFFICIENT_DATA: { color: '#334155', short: '---' },
  }
  const m = MAP[signal] ?? { color: '#334155', short: '?' }
  return (
    <span style={{
      fontSize: 10, fontWeight: 700, padding: '1px 5px', borderRadius: 2,
      border: `1px solid ${m.color}44`, color: m.color, background: `${m.color}18`,
    }}>
      {m.short}
    </span>
  )
}

export function WatchlistPage() {
  type StocksResponse = Awaited<ReturnType<typeof fetchAllStocks>>

  // Deep-linkable label filter: /watchlist?label=BULL_RUN etc.
  // (Dashboard universe-breadth segments link here.)
  const [searchParams, setSearchParams] = useSearchParams()
  const urlLabel = (searchParams.get('label') ?? '').toUpperCase()

  const [page,        setPage]        = useState(1)
  const [labelFilter, setLabelFilterState] = useState(
    LABELS.includes(urlLabel) ? urlLabel : 'EMERGING'
  )
  const setLabelFilter = (l: string) => {
    setLabelFilterState(l)
    setPage(1)
    setSearchParams(l === 'EMERGING' ? {} : { label: l }, { replace: true })
  }
  const [search,      setSearch]      = useState('')
  const [sectorFilter,setSectorFilter]= useState('ALL')
  const [sortKey,     setSortKey]     = useState<SortKey>('bull_run_score')
  const [sortDir,     setSortDir]     = useState<SortDir>('desc')

  // Follow URL changes made while already mounted (e.g. Dashboard link clicks)
  useEffect(() => {
    if (LABELS.includes(urlLabel) && urlLabel !== labelFilter) {
      setLabelFilterState(urlLabel)
      setPage(1)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [urlLabel])

  // Fetch all matching pages (up to 2000 symbols) for client-side sort/search
  const { data, isLoading } = useQuery<StocksResponse>({
    queryKey: ['all_stocks', page, labelFilter, sectorFilter],
    queryFn:  () => fetchAllStocks(page, PER_PAGE, labelFilter, sectorFilter === 'ALL' ? undefined : sectorFilter),
    refetchInterval: 300000,
    placeholderData: previous => previous,
  })

  const stocks: Stock[] = data?.stocks ?? []

  // Unique sectors for dropdown
  const sectors = useMemo(() => {
    const s = new Set(stocks.map(s => s.sector).filter(Boolean))
    return ['ALL', ...Array.from(s).sort()]
  }, [stocks])

  // Client-side search + sort (within the fetched page)
  const displayed = useMemo(() => {
    let rows = stocks
    if (search.trim()) {
      const q = search.trim().toUpperCase()
      rows = rows.filter(s => s.symbol.includes(q) || (s.sector ?? '').toUpperCase().includes(q))
    }
    rows = [...rows].sort((a, b) => {
      const resolve = (s: Stock) => {
        const top = (s as any)[sortKey]
        if (typeof top === 'number') return top
        const price = (s.price as any)?.[sortKey]
        if (typeof price === 'number') return price
        return -Infinity
      }
      const va = resolve(a)
      const vb = resolve(b)
      return sortDir === 'desc' ? vb - va : va - vb
    })
    return rows
  }, [stocks, search, sortKey, sortDir])

  const toggleSort = (col: SortKey) => {
    if (sortKey === col) {
      setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    } else {
      setSortKey(col)
      setSortDir('desc')
    }
  }

  const pct = (v: number | null | undefined) => {
    if (v == null) return <span style={{ color: '#334155' }}>--</span>
    const c = v >= 0 ? '#22C55E' : '#EF4444'
    return <span style={{ color: c }}>{v >= 0 ? '+' : ''}{v.toFixed(1)}%</span>
  }

  return (
    <div className="space-y-4">
      {/* Header + filters */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <h1 className="text-lg font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
          WATCHLIST <span style={{ color: '#64748B', fontSize: 14, fontWeight: 400 }}>{data?.total ?? 0} symbols</span>
        </h1>

        {/* Search */}
        <input
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search symbol / sector..."
          style={{
            background: '#141720', border: '1px solid #1E2332', borderRadius: 4,
            color: '#E2E8F0', padding: '5px 10px', fontSize: 13, outline: 'none', width: 200,
          }}
        />

        {/* Sector filter */}
        <select
          value={sectorFilter}
          onChange={e => { setSectorFilter(e.target.value); setPage(1) }}
          style={{
            background: '#141720', border: '1px solid #1E2332', borderRadius: 4,
            color: sectorFilter === 'ALL' ? '#64748B' : '#E2E8F0', padding: '5px 8px', fontSize: 13,
          }}
        >
          {sectors.map(s => <option key={s} value={s}>{s === 'ALL' ? 'All sectors' : s}</option>)}
        </select>
      </div>

      {/* Label pills */}
      <div className="flex gap-2 flex-wrap">
        {LABELS.map(l => (
          <button
            key={l}
            className="px-2 py-1 rounded text-xs border transition-all"
            style={{
              borderColor: labelFilter === l ? '#22C55E' : '#1E2332',
              color: labelFilter === l ? '#22C55E' : '#64748B',
              backgroundColor: '#141720',
            }}
            onClick={() => { setLabelFilter(l); setPage(1) }}
          >
            {l === 'ALL' ? 'All' : l.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {isLoading && <div className="text-center py-20" style={{ color: '#64748B' }}>Loading...</div>}

      <div className="overflow-x-auto">
        {/* Row-hover outline: rounded amber rectangle around the whole row.
            HTML rows cannot take border-radius, so the outline is drawn on
            the row's cells (top/bottom on all, sides + radii on the ends).
            Requires border-collapse: separate. */}
        <style>{`
          .wl-table { border-collapse: separate; border-spacing: 0; }
          .wl-row td {
            border-top: 1px solid transparent;
            border-bottom: 1px solid #1E233220;
            transition: border-color 0.12s;
          }
          .wl-row td:first-child { border-left: 1px solid transparent; }
          .wl-row td:last-child  { border-right: 1px solid transparent; }
          .wl-row:hover td {
            border-top-color: #F59E0BCC;
            border-bottom-color: #F59E0BCC;
          }
          .wl-row:hover td:first-child {
            border-left-color: #F59E0BCC;
            border-top-left-radius: 8px;
            border-bottom-left-radius: 8px;
          }
          .wl-row:hover td:last-child {
            border-right-color: #F59E0BCC;
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
          }
        `}</style>
        <table className="wl-table" style={{ width: '100%', fontSize: 13 }}>
          <thead>
            <tr>
              <th style={{ padding: '6px 10px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#64748B', borderBottom: '1px solid #1E2332', whiteSpace: 'nowrap' }}>Symbol</th>
              <th style={{ padding: '6px 10px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#64748B', borderBottom: '1px solid #1E2332' }}>Sector</th>
              <SortHeader label="LTP"    col="close_now"     active={sortKey === 'close_now'}     dir={sortDir} onClick={() => toggleSort('close_now')} />
              <SortHeader label="Score"  col="bull_run_score"       active={sortKey === 'bull_run_score'}       dir={sortDir} onClick={() => toggleSort('bull_run_score')} />
              <SortHeader label="FWD 45D" col="forward_return_score" active={sortKey === 'forward_return_score'} dir={sortDir} onClick={() => toggleSort('forward_return_score')} amber />
              <th style={{ padding: '6px 10px', textAlign: 'left', fontSize: 12, fontWeight: 600, color: '#64748B', borderBottom: '1px solid #1E2332' }}>Label</th>
              <th style={{ padding: '6px 10px', textAlign: 'center', fontSize: 12, fontWeight: 600, color: '#64748B', borderBottom: '1px solid #1E2332' }}>Trend</th>
              <th style={{ padding: '6px 10px', textAlign: 'center', fontSize: 12, fontWeight: 600, color: '#64748B', borderBottom: '1px solid #1E2332' }}>Action</th>
              <SortHeader label="RS 30D"   col="rs_30d"          active={sortKey === 'rs_30d'}          dir={sortDir} onClick={() => toggleSort('rs_30d')} />
              <SortHeader label="DELIV 5D" col="delivery_5d_pct" active={sortKey === 'delivery_5d_pct'} dir={sortDir} onClick={() => toggleSort('delivery_5d_pct')} />
              <SortHeader label="RVOL"     col="rvol"            active={sortKey === 'rvol'}            dir={sortDir} onClick={() => toggleSort('rvol')} />
              <SortHeader label="CONV"     col="conviction_score" active={sortKey === 'conviction_score'} dir={sortDir} onClick={() => toggleSort('conviction_score')} amber />
            </tr>
          </thead>
          <tbody>
            {displayed.map(s => (
              <tr key={s.symbol} className="wl-row">
                <td style={{ padding: '6px 10px', fontWeight: 700 }}>
                  <Link to={`/stocks/${s.symbol}`} style={{ color: '#E2E8F0', textDecoration: 'none' }}>
                    {s.symbol}
                  </Link>
                </td>
                <td style={{ padding: '6px 10px', color: '#64748B', whiteSpace: 'nowrap' }}>{s.sector}</td>
                <td style={{ padding: '6px 10px', textAlign: 'right', color: '#94A3B8', fontWeight: 600 }}>
                  {s.close_now != null
                    ? <>&#8377;{s.close_now.toLocaleString('en-IN', { maximumFractionDigits: 2 })}</>
                    : <span style={{ color: '#334155' }}>--</span>}
                </td>
                <td style={{ padding: '6px 10px', textAlign: 'center' }}>
                  <ScoreGauge score={s.bull_run_score} size={36} />
                </td>
                <td style={{ padding: '6px 10px', textAlign: 'center' }}>
                  {(s as any).forward_return_score != null ? (
                    <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                      <span style={{
                        fontSize: 14, fontWeight: 800, fontFamily: 'monospace',
                        color: (s as any).forward_return_score >= 60 ? '#F59E0B'
                             : (s as any).forward_return_score >= 40 ? '#D97706'
                             : '#92653A',
                        fontVariantNumeric: 'tabular-nums',
                      }}>
                        {((s as any).forward_return_score as number).toFixed(0)}
                      </span>
                      <div style={{ width: 28, height: 2, background: '#1E2332', borderRadius: 1 }}>
                        <div style={{
                          width: `${Math.min((s as any).forward_return_score, 100)}%`,
                          height: '100%', borderRadius: 1,
                          background: (s as any).forward_return_score >= 60 ? '#F59E0B' : '#92653A',
                        }} />
                      </div>
                    </div>
                  ) : <span style={{ color: '#334155' }}>--</span>}
                </td>
                <td style={{ padding: '6px 10px' }}><CapFlowBadge label={s.label} /></td>
                <td style={{ padding: '6px 10px', textAlign: 'center' }}>
                  <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                    <TrendBadge signal={s.trend_signal ?? (s as any).technical?.trend_signal} />
                    {/* Distance from 50DMA -- overextension gauge (WL-1) */}
                    {(s as any).vs_dma_50 != null && (
                      <span style={{
                        fontSize: 11, fontFamily: 'monospace',
                        color: (s as any).vs_dma_50 > 15 ? '#F59E0B'
                             : (s as any).vs_dma_50 >= 0 ? '#64748B' : '#EF4444',
                      }} title="Distance from 50-day moving average">
                        {(s as any).vs_dma_50 >= 0 ? '+' : ''}{((s as any).vs_dma_50 as number).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </td>
                <td style={{ padding: '6px 10px', textAlign: 'center' }}>
                  <ActionBadge
                    label={s.label}
                    trend={s.trend_signal ?? (s as any).technical?.trend_signal}
                    oi={s.oi_signal ?? (s as any).fno?.oi_signal}
                    rvol={(s as any).rvol}
                    rs30={(s as any).rs_30d}
                    vsDma50={(s as any).vs_dma_50}
                  />
                </td>
                {/* RS 30D vs NIFTY 50 (WL-1) */}
                <td style={{ padding: '6px 10px', textAlign: 'right' }}
                    title="30-day return minus NIFTY 50 return">
                  {pct((s as any).rs_30d)}
                </td>
                {/* 5-session average delivery % (WL-1) */}
                <td style={{ padding: '6px 10px', textAlign: 'right' }}
                    title="5-session average delivery percentage">
                  {(s as any).delivery_5d_pct != null ? (
                    <span style={{
                      color: (s as any).delivery_5d_pct >= 60 ? '#22C55E'
                           : (s as any).delivery_5d_pct >= 40 ? '#94A3B8' : '#F97316',
                    }}>{((s as any).delivery_5d_pct as number).toFixed(0)}%</span>
                  ) : <span style={{ color: '#334155' }}>--</span>}
                </td>
                {/* Relative volume vs 20d average (WL-1); >= 2x highlighted */}
                <td style={{ padding: '6px 10px', textAlign: 'right' }}
                    title="Today's volume / 20-day average volume">
                  {(s as any).rvol != null ? (
                    <span style={{
                      color: (s as any).rvol >= 2.0 ? '#22D35E' : '#64748B',
                      fontWeight: (s as any).rvol >= 2.0 ? 800 : 400,
                      background: (s as any).rvol >= 2.0 ? '#052e16' : 'transparent',
                      padding: '1px 5px', borderRadius: 3,
                    }}>{((s as any).rvol as number).toFixed(1)}x</span>
                  ) : <span style={{ color: '#334155' }}>--</span>}
                </td>
                {/* Conviction score (SA-1 screener) -- decision-view enrichment */}
                <td style={{ padding: '6px 10px', textAlign: 'right' }}
                    title="7-factor trade conviction score">
                  {(s as any).conviction_score != null ? (
                    <span style={{
                      fontFamily: 'monospace', fontWeight: 700,
                      color: (s as any).conviction_score >= 70 ? '#F59E0B'
                           : (s as any).conviction_score >= 55 ? '#D97706' : '#64748B',
                    }}>{((s as any).conviction_score as number).toFixed(0)}</span>
                  ) : <span style={{ color: '#334155' }}>--</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex gap-2 justify-center">
        {page > 1 && (
          <button onClick={() => setPage(p => p - 1)} style={{ padding: '4px 12px', borderRadius: 4, fontSize: 13, background: '#141720', color: '#64748B', border: '1px solid #1E2332', cursor: 'pointer' }}>
            Prev
          </button>
        )}
        <span style={{ padding: '4px 12px', fontSize: 13, color: '#64748B' }}>Page {page}</span>
        {(data?.stocks?.length ?? 0) === PER_PAGE && (
          <button onClick={() => setPage(p => p + 1)} style={{ padding: '4px 12px', borderRadius: 4, fontSize: 13, background: '#141720', color: '#64748B', border: '1px solid #1E2332', cursor: 'pointer' }}>
            Next
          </button>
        )}
      </div>
    </div>
  )
}
