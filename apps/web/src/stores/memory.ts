import { create } from "zustand"
import { api } from "@/lib/api"

export interface MemoryEntry {
  id: string
  content: string
  memory_type?: string
  agent_id?: string
  score?: number
  created_at?: string
  payload?: Record<string, unknown>
}

interface MemoryState {
  memories: MemoryEntry[]
  loading: boolean
  error: string | null
  recall: (query: string, agentId?: string) => Promise<void>
  search: (query: string, filters?: Record<string, string>) => Promise<void>
  remove: (id: string) => Promise<void>
}

export const useMemoryStore = create<MemoryState>((set) => ({
  memories: [],
  loading: false,
  error: null,

  recall: async (query, agentId) => {
    set({ loading: true, error: null })
    try {
      const res = await api.post("/memory/recall", { query, agent_id: agentId, limit: 50 })
      set({ memories: res.results ?? [], loading: false })
    } catch {
      set({ loading: false, error: "Failed to recall memories" })
    }
  },

  search: async (query, filters) => {
    set({ loading: true, error: null })
    try {
      const res = await api.post("/memory/search", { query, limit: 50, ...filters })
      set({ memories: res.results ?? [], loading: false })
    } catch {
      set({ loading: false, error: "Failed to search memories" })
    }
  },

  remove: async (id) => {
    await api.delete(`/memory/points/${id}`)
    set((s) => ({ memories: s.memories.filter((m) => m.id !== id) }))
  },
}))
