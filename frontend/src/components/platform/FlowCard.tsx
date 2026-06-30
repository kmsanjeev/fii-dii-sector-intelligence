interface FlowCardProps {
  participant: string
  score: number
  conviction?: number
}

export function FlowCard({ participant, score, conviction }: FlowCardProps) {
  const positive = score >= 0
  const color = positive ? '#22C55E' : '#EF4444'
  const sign = positive ? '+' : ''
  const bar = Math.min(Math.abs(score) / 3, 1)  // z-score normalized to [0,1]

  return (
    <div
      className="p-3 rounded border"
      style={{ backgroundColor: '#141720', borderColor: '#1E2332' }}
    >
      <div className="text-xs mb-1" style={{ color: '#64748B' }}>{participant}</div>
      <div className="text-lg font-bold" style={{ color }}>
        {sign}{score.toFixed(1)}
      </div>
      <div className="mt-1 h-1 rounded" style={{ backgroundColor: '#1E2332' }}>
        <div
          className="h-1 rounded"
          style={{ width: `${bar * 100}%`, backgroundColor: color }}
        />
      </div>
      {conviction !== undefined && (
        <div className="text-xs mt-1" style={{ color: '#64748B' }}>
          conviction {conviction.toFixed(0)}%
        </div>
      )}
    </div>
  )
}
