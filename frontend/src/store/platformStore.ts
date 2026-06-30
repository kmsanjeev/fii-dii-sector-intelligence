import { create } from 'zustand'
import type { MarketRegime } from '../api/client'

interface PlatformStore {
  regime: MarketRegime | null
  setRegime: (r: MarketRegime) => void
  selectedSector: string | null
  setSelectedSector: (s: string | null) => void
  selectedSymbol: string | null
  setSelectedSymbol: (s: string | null) => void
}

export const usePlatformStore = create<PlatformStore>(set => ({
  regime: null,
  setRegime: (r) => set({ regime: r }),
  selectedSector: null,
  setSelectedSector: (s) => set({ selectedSector: s }),
  selectedSymbol: null,
  setSelectedSymbol: (s) => set({ selectedSymbol: s }),
}))
