import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fetchAllStocks, type Stock } from '../api/client'
import { ScoreGauge } from '../components/platform/ScoreGauge'
import { CapFlowBadge } from '../components/platform/CapFlowBadge'
import { Link, useNavigate } from 'react-router-dom'

const LABELS   = ['ALL', 'STRONG_CANDIDATE', 'EMERGING', 'WATCHLIST', 'NEUTRAL', 'AVOID']
const PER_PAGE = 100

type SortKey = 'bull_run_score' | 'close_now' | 'ret_30d' | 'ret_365d' | 'vol_ratio'
type SortDir = 'asc' | 'desc'

function SortHeader({
  label, col, active, dir, onClick,
}: { label: string; col: SortKey; active: boolean; dir: SortDir; onClick: () => void }) {
  return (
    <th
      onClick={onClick}
      style={{
        padding: '6px 10px', textAlign: col === 'bull_run_score' ? 'center' : 'right',
        fontSize: 10, fontWeight: 600, color: active ? '#22C55E' : '#64748B',
        whiteSpace: 'nowrap', borderBottom: '1px solid #1E2332', cursor: 'pointer',
        userSelect: 'none',
      }}
    >
      {label} {active ? (dir === 'desc' ? ' v' : ' ^') : ''}
    </th>
  )
}

function ActionBadge({ label, trend, oi }: { label: string; trend?: string; oi?: string }) {
  // Quick action signal from available bulk fields
  const bullishTrend = trend === 'STRONG_UPTREND' || trend === 'UPTREND'
  const bearishTrend = trend === 'DOWNTREND'
  const bullishOI    = oi === 'LONG_BUILDUP' || oi === 'SHORT_COVERING'
  const bearishOI    = oi === 'SHORT_BUILDUP' || oi === 'LONG_UNWINDING'
  const avoidLabel   = label === 'AVOID'
  const strongLabel  = label === 'STRONG_CANDIDATE'

  let text = 'WATCH'
  let color = '#64748B'
  let bg    = '#1E2332'

  if (avoidLabel || (bearishTrend && bearishOI)) {
    text = 'EXIT'; color = '#EF4444'; bg = '#1c0000'
  } else if (bearishTrend || (bearishOI && !bullishTrend)) {
    text = 'REDUCE'; color = '#F97316'; bg = '#1c0a00'
  } else if (strongLabel && bullishTrend && bullishOI) {
    text = 'STR BUY'; color = '#22C55E'; bg = '#052e16'
  } else if ((strongLabel || label === 'EMERGING') && bullishTrend) {
    text = 'BUY'; color = '#10B981'; bg = '#022c22'
  } else if (bullishTrend) {
    text = 'HOLD'; color = '#F59E0B'; bg = '#1c1400'
  }

  return (
    <span style={{
      fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 2,
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
      fontSize: 8, fontWeight: 700, padding: '1px 5px', borderRadius: 2,
      border: `1px solid ${m.color}44`, color: m.color, background: `${m.color}18`,
    }}>
      {m.short}
    </span>
  )
}

export function WatchlistPage() {
  const navigate = useNavigate()
  const [page,        setPage]        = useState(1)
  const [labelFilter, setLabelFilter] = useState('EMERGING')
  const [search,      setSearch]      = useState('')
  const [sectorFilter,setSectorFilter]= useState('ALL')
  const [sortKey,     setSortKey]     = useState<SortKey>('bull_run_score')
  const [sortDir,     setSortDir]     = useState<SortDir>('desc')

  // Fetch all matching pages (up to 2000 symbols) for client-side sort/search
  const { data, isLoading } = useQuery({
    queryKey: ['all_stocks', page, labelFilter, sectorFilter],
    queryFn:  () => fetchAllStocks(page, PER_PAGE, labelFilter, sectorFilter === 'ALL' ? undefined : sectorFilter),
    refetchInterval: 300000,
    keepPreviousData: true,
  } as any)

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
      const av = (a as any)[sortKey] ?? (sortKey === 'close_now' ? a.close_now : null) ?? -Infinity
      const bv = (b as any)[sortKey] ?? (sortKey === 'close_now' ? b.close_now : null) ?? -Infinity
      const va = typeof av === 'number' ? av : (a.price as any)?.[sortKey] ?? -Infinity
      const vb = typeof bv === 'number' ? bv : (b.price as any)?.[sortKey] ?? -Infinity
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
      <button onClick={() => navigate(-1)} style={{
        display: 'flex', alignItems: 'center', gap: 6, background: 'none',
        border: '1px solid #1E2332', color: '#64748B', cursor: 'pointer',
        padding: '4px 12px', borderRadius: 4, fontSize: 11,
      }}>&larr; Back</button>

      {/* Header + filters */}
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
        <h1 className="text-lg font-bold tracking-widest" style={{ color: '#E2E8F0' }}>
          WATCHLIST <span style={{ color: '#64748B', fontSize: 12, fontWeight: 400 }}>{data?.total ?? 0} symbols</span>
        </h1>

        {/* Search */}
        <input
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search symbol / sector..."
          style={{
            background: '#141720', border: '1px solid #1E2332', borderRadius: 4,
            color: '#E2E8F0', padding: '5px 10px', fontSize: 11, outline: 'none', width: 200,
          }}
        />

        {/* Sector filter */}
        <select
          value={sectorFilter}
          onChange={e => { setSectorFilter(e.target.value); setPage(1) }}
          style={{
            background: '#141720', border: '1px solid #1E2332', borderRadius: 4,
            color: sectorFilter === 'ALL' ? '#64748B' : '#E2E8F0', padding: '5px 8px', fontSize: 11,
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
        <table style={{ width: '100%', fontSize: 11, borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ padding: '6px 10px', textAlign: 'left', fontSize: 10, fontWeight: 600, color: '#64748B', borderBottom: '1px solid #1E2332', whiteSpace: 'nowrap' }}>Symbol</th>
              <th style={{ padding: '6px 10px', textAlign: 'left', fontSize: 10, fontWeight: 600, color: '#64748B', borderBottom: '1px solid #1E2332' }}>Sector</th>
              <SortHeader label="LTP"    col="close_now"     active={sortKey === 'close_now'}     dir={sortDir} onClick={() => toggleSort('close_now')} />
              <SortHeader label="Score"  col="bull_run_score" active={sortKey === 'bull_run_score'} dir={sortDir} onClick={() => toggleSort('bull_run_score')} />
              <th style={{ padding: '6px 10px', textAlign: 'left', fontSize: 10, fontWeight: 600, color: '#64748B', borderBottom: '1px solid #1E2332' }}>Label</th>
              <th style={{ padding: '6px 10px', textAlign: 'center', fontSize: 10, fontWeight: 600, color: '#64748B', borderBottom: '1px solid #1E2332' }}>Trend</th>
              <th style={{ padding: '6px 10px', textAlign: 'center', fontSize: 10, fontWeight: 600, color: '#64748B', borderBottom: '1px solid #1E2332' }}>Action</th>
              <SortHeader label="30D"   col="ret_30d"   active={sortKey === 'ret_30d'}   dir={sortDir} onClick={() => toggleSort('ret_30d')} />
              <SortHeader label="365D"  col="ret_365d"  active={sortKey === 'ret_365d'}  dir={sortDir} onClick={() => toggleSort('ret_365d')} />
              <SortHeader label="Vol"   col="vol_ratio" active={sortKey === 'vol_ratio'} dir={sortDir} onClick={() => toggleSort('vol_ratio')} />
            </tr>
          </thead>
          <tbody>
            {displayed.map(s => (
              <tr key={s.symbol} style={{ borderBottom: '1px solid #1E233220' }} className="hover:brightness-125 transition-all">
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
                <td style={{ padding: '6px 10px' }}><CapFlowBadge label={s.label} /></td>
                <td style={{ padding: '6px 10px', textAlign: 'center' }}>
                  <TrendBadge signal={s.trend_signal ?? (s as any).technical?.trend_signal} />
                </td>
                <td style={{ padding: '6px 10px', textAlign: 'center' }}>
                  <ActionBadge
                    label={s.label}
                    trend={s.trend_signal ?? (s as any).technical?.trend_signal}
                    oi={s.oi_signal ?? (s as any).fno?.oi_signal}
                  />
                </td>
                <td style={{ padding: '6px 10px', textAlign: 'right' }}>{pct(s.price?.ret_30d)}</td>
                <td style={{ padding: '6px 10px', textAlign: 'right' }}>{pct(s.price?.ret_365d)}</td>
                <td style={{ padding: '6px 10px', textAlign: 'right', color: '#64748B' }}>
                  {s.price?.vol_ratio != null ? `${s.price.vol_ratio.toFixed(1)}x` : '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex gap-2 justify-center">
        {page > 1 && (
          <button onClick={() => setPage(p => p - 1)} style={{ padding: '4px 12px', borderRadius: 4, fontSize: 11, background: '#141720', color: '#64748B', border: '1px solid #1E2332', cursor: 'pointer' }}>
            Prev
          </button>
        )}
        <span style={{ padding: '4px 12px', fontSize: 11, color: '#64748B' }}>Page {page}</span>
        {(data?.stocks?.length ?? 0) === PER_PAGE && (
          <button onClick={() => setPage(p => p + 1)} style={{ padding: '4px 12px', borderRadius: 4, fontSize: 11, background: '#141720', color: '#64748B', border: '1px solid #1E2332', cursor: 'pointer' }}>
            Next
          </button>
        )}
      </div>
    </div>
  )
}
