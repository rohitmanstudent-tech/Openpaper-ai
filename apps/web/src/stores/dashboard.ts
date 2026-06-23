import { create } from "zustand"
import { api } from "@/lib/api"

interface SystemHealth {
  status: string
  uptime_seconds?: number
  version?: string
  environment?: string
  checks?: Record<string, { status: string }>
}

interface DashboardState {
  systemHealth: SystemHealth | null
  providerCount: number
  modelCount: number
  healthLoading: boolean
  fetchHealth: () => Promise<void>
  fetchCounts: () => Promise<void>
}

export const useDashboardStore = create<DashboardState>((set) => ({
  systemHealth: null,
  providerCount: 0,
  modelCount: 0,
  healthLoading: false,
  fetchHealth: async () => {
    set({ healthLoading: true })
    try {
      const health = await api.get("/health/deep")
      set({ systemHealth: health, healthLoading: false })
    } catch {
      set({ healthLoading: false })
    }
  },
  fetchCounts: async () => {
    try {
      const [providers, models] = await Promise.all([
        api.get("/providers"),
        api.get("/models"),
      ])
      set({
        providerCount: providers.providers?.length || 0,
        modelCount: Object.values(models as Record<string, string[]>).flat().length || 0,
      })
    } catch {
      // silently fail
    }
  },
}))
