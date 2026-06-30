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
      className="w-full px-4 py-2 text-sm flex items-center gap-6 border-b"
      style={{ backgroundColor: `${color}18`, borderColor: `${color}40`, color }}
    >
      <span className="font-bold tracking-widest">{regime}</span>
      <span>Smart Money: {smSign}{smartMoney.toFixed(1)}</span>
      <span>FII Conviction: {fiiConviction.toFixed(0)}%</span>
    </div>
  )
}
