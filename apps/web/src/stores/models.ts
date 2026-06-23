import { create } from "zustand"
import { api } from "@/lib/api"

export interface ModelInfo {
  name: string
  default_model: string
  status: string
  model_count: number
}

interface ModelsState {
  modelsByProvider: Record<string, string[]>
  providers: ModelInfo[]
  loading: boolean
  fetch: () => Promise<void>
}

export const useModelsStore = create<ModelsState>((set) => ({
  modelsByProvider: {},
  providers: [],
  loading: false,
  fetch: async () => {
    set({ loading: true })
    try {
      const [modelsData, providersData] = await Promise.all([
        api.get("/models"),
        api.get("/providers"),
      ])
      set({ modelsByProvider: modelsData, providers: providersData.providers, loading: false })
    } catch {
      set({ loading: false })
    }
  },
}))
