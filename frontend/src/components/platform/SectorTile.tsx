import type { Sector } from '../../api/client'

interface SectorTileProps {
  sector: Sector
  onClick?: () => void
}

const SIGNAL_COLORS: Record<string, string> = {
  EARLY_ROTATION: '#10B981',
  LEADING:        '#22C55E',
  MOMENTUM:       '#3B82F6',
  EMERGING:       '#8B5CF6',
  LAGGING:        '#F59E0B',
  DECLINING:      '#EF4444',
}

export function SectorTile({ sector, onClick }: SectorTileProps) {
  const color = SIGNAL_COLORS[sector.rotation_signal] ?? '#64748B'
  const score = sector.combined_score ?? 0

  return (
    <div
      className="p-3 rounded border cursor-pointer hover:brightness-110 transition-all"
      style={{ backgroundColor: '#141720', borderColor: color + '40', borderLeftColor: color, borderLeftWidth: 3 }}
      onClick={onClick}
    >
      <div className="font-bold text-sm truncate" style={{ color: '#E2E8F0' }}>{sector.sector}</div>
      <div className="text-xs mt-1" style={{ color }}>{sector.rotation_signal}</div>
      <div className="text-lg font-bold mt-1" style={{ color }}>{score.toFixed(1)}</div>
      <div className="text-xs mt-1" style={{ color: '#64748B' }}>
        FII {(sector.FII_flow_score ?? 0).toFixed(1)}
      </div>
    </div>
  )
}
