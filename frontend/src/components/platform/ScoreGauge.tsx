interface ScoreGaugeProps {
  score: number   // 0-100
  size?: number   // px, default 80
  label?: string
}

function scoreColor(score: number): string {
  if (score >= 65) return '#10B981'
  if (score >= 45) return '#22C55E'
  if (score >= 30) return '#3B82F6'
  if (score >= 15) return '#F59E0B'
  return '#EF4444'
}

export function ScoreGauge({ score, size = 80, label }: ScoreGaugeProps) {
  const r = (size / 2) * 0.8
  const circumference = 2 * Math.PI * r
  const filled = (score / 100) * circumference
  const color = scoreColor(score)
  const cx = size / 2
  const cy = size / 2

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#1E2332" strokeWidth={6} />
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={color}
          strokeWidth={6}
          strokeDasharray={`${filled} ${circumference}`}
          strokeLinecap="round"
        />
        <text
          x={cx} y={cy}
          textAnchor="middle"
          dominantBaseline="central"
          style={{ transform: 'rotate(90deg)', transformOrigin: `${cx}px ${cy}px`, fill: color, fontSize: size * 0.22, fontWeight: 700, fontFamily: 'monospace' }}
        >
          {Math.round(score)}
        </text>
      </svg>
      {label && <span className="text-xs" style={{ color: '#64748B' }}>{label}</span>}
    </div>
  )
}
