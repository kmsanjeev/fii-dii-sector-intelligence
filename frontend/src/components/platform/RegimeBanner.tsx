interface RegimeBannerProps {
  regime: string
  smartMoney: number
  fiiConviction: number
}

const REGIME_COLORS: Record<string, string> = {
  STRONG_ACCUMULATION: '#10B981',
  ACCUMULATION:        '#22C55E',
  NEUTRAL:             '#F59E0B',
  DISTRIBUTION:        '#F97316',
  STRONG_DISTRIBUTION: '#EF4444',
}

export function RegimeBanner({ regime, smartMoney, fiiConviction }: RegimeBannerProps) {
  const color = REGIME_COLORS[regime] ?? '#64748B'
  const smSign = smartMoney >= 0 ? '+' : ''

  return (
    <div
      className="w-full border-b"
      style={{
        backgroundColor: `${color}18`,
        borderColor: `${color}40`,
        color,
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        gap: 'clamp(8px, 3vw, 24px)',
        padding: 'clamp(4px, 1.5vw, 8px) clamp(10px, 3vw, 16px)',
        fontSize: 'clamp(11px, 2.5vw, 14px)',
      }}
    >
      <span style={{ fontWeight: 700, letterSpacing: '0.12em', whiteSpace: 'nowrap' }}>{regime}</span>
      <span style={{ whiteSpace: 'nowrap' }}>Smart Money: {smSign}{smartMoney.toFixed(1)}</span>
      <span style={{ whiteSpace: 'nowrap' }}>FII Conv: {fiiConviction.toFixed(0)}%</span>
    </div>
  )
}
