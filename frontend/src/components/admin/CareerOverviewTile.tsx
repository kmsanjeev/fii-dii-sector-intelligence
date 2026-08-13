import { useQuery } from '@tanstack/react-query'
import { fetchCareerValidatedProfiles } from '../../api/researchAdmin'

const panel = {
  background: '#141720',
  border: '1px solid #1E2332',
  borderRadius: 8,
}

const text = '#E2E8F0'
const muted = '#64748B'
const accent = '#22C55E'
const info = '#60A5FA'
const warn = '#F59E0B'

function formatPercent(value: number) {
  return `${(value * 100).toFixed(1)}%`
}

function badge(color: string) {
  return {
    border: `1px solid ${color}44`,
    background: `${color}18`,
    color,
    borderRadius: 999,
    fontSize: 10,
    fontWeight: 700,
    padding: '2px 8px',
    whiteSpace: 'nowrap' as const,
  }
}

export function CareerOverviewTile() {
  const query = useQuery({
    queryKey: ['career-validated-summary'],
    queryFn: () => fetchCareerValidatedProfiles({ limit: 1, offset: 0 }),
    staleTime: 60_000,
  })

  if (query.isLoading) {
    return (
      <div style={{ ...panel, padding: 14 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 8 }}>CAREER / PROFESSION VALIDATION</div>
        <div style={{ color: muted, fontSize: 12 }}>Loading career governance metrics…</div>
      </div>
    )
  }

  if (query.isError || !query.data) {
    return (
      <div style={{ ...panel, padding: 14 }}>
        <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 8 }}>CAREER / PROFESSION VALIDATION</div>
        <div style={{ color: warn, fontSize: 12 }}>Career metrics are unavailable.</div>
      </div>
    )
  }

  const summary = query.data.summary
  const topIndustries = summary.top_industries.slice(0, 3)

  return (
    <div style={{ ...panel, padding: 14 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
        <div>
          <div style={{ color: '#94A3B8', fontSize: 11, fontWeight: 700, marginBottom: 4 }}>CAREER / PROFESSION VALIDATION</div>
          <div style={{ color: text, fontSize: 13, fontWeight: 700 }}>Shadow synthesis across governed chart, industry, and timing signals</div>
        </div>
        <span style={badge(summary.synthetic_rate >= 0.8 ? warn : accent)}>
          {formatPercent(summary.synthetic_rate)} synthetic
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 10, marginBottom: 12 }}>
        <div>
          <div style={{ color: muted, fontSize: 10, marginBottom: 4 }}>Profiles</div>
          <div style={{ color: accent, fontSize: 20, fontWeight: 700 }}>{summary.profiles_total.toLocaleString()}</div>
        </div>
        <div>
          <div style={{ color: muted, fontSize: 10, marginBottom: 4 }}>Canonical</div>
          <div style={{ color: info, fontSize: 20, fontWeight: 700 }}>{summary.canonical_rows.toLocaleString()}</div>
        </div>
        <div>
          <div style={{ color: muted, fontSize: 10, marginBottom: 4 }}>Synthetic</div>
          <div style={{ color: warn, fontSize: 20, fontWeight: 700 }}>{summary.synthetic_rows.toLocaleString()}</div>
        </div>
        <div>
          <div style={{ color: muted, fontSize: 10, marginBottom: 4 }}>Industries</div>
          <div style={{ color: text, fontSize: 20, fontWeight: 700 }}>{summary.industries_covered.toLocaleString()}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gap: 8 }}>
        {topIndustries.map(item => (
          <div key={item.industry} style={{ display: 'flex', justifyContent: 'space-between', gap: 8, borderBottom: '1px solid #1E2332', paddingBottom: 6 }}>
            <div style={{ color: text, fontSize: 12, fontWeight: 700 }}>{item.industry}</div>
            <div style={{ color: muted, fontSize: 12 }}>{item.count.toLocaleString()}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

