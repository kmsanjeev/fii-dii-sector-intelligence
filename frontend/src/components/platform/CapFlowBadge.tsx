interface CapFlowBadgeProps {
  label: string
}

const BADGE_STYLES: Record<string, { bg: string; text: string }> = {
  STRONG_CANDIDATE: { bg: '#10B98120', text: '#10B981' },
  EMERGING:         { bg: '#22C55E20', text: '#22C55E' },
  WATCHLIST:        { bg: '#3B82F620', text: '#3B82F6' },
  NEUTRAL:          { bg: '#F59E0B20', text: '#F59E0B' },
  AVOID:            { bg: '#EF444420', text: '#EF4444' },
}

export function CapFlowBadge({ label }: CapFlowBadgeProps) {
  const style = BADGE_STYLES[label] ?? { bg: '#1E233240', text: '#64748B' }
  return (
    <span
      className="inline-block px-2 py-0.5 rounded text-xs font-bold tracking-wide"
      style={{ backgroundColor: style.bg, color: style.text }}
    >
      {label}
    </span>
  )
}
