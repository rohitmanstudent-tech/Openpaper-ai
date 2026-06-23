import { create } from "zustand"
import { api } from "@/lib/api"
import type { ProviderStatus } from "@repo/shared"

interface ProviderState {
  providers: ProviderStatus[]
  loading: boolean
  fetch: () => Promise<void>
}

export const useProviderStore = create<ProviderState>((set) => ({
  providers: [],
  loading: false,
  fetch: async () => {
    set({ loading: true })
    try {
      const data = await api.get("/providers")
      set({ providers: data.providers, loading: false })
    } catch {
      set({ loading: false })
    }
  },
}))
