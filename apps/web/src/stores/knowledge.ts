import { create } from "zustand"
import { api } from "@/lib/api"

interface KnowledgeBase {
  name: string
  point_count?: number
}

interface KnowledgeState {
  collections: KnowledgeBase[]
  loading: boolean
  error: string | null
  fetch: () => Promise<void>
  create: (name: string) => Promise<void>
  remove: (name: string) => Promise<void>
}

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  collections: [],
  loading: false,
  error: null,

  fetch: async () => {
    set({ loading: true, error: null })
    try {
      const res = await api.get("/documents/collections")
      const cols = (res.collections ?? []).filter(
        (c: string) => c !== "agent_memories" && c !== "agent_events"
      )
      set({ collections: cols.map((n: string) => ({ name: n })), loading: false })
    } catch {
      set({ loading: false, error: "Failed to load knowledge bases" })
    }
  },

  create: async (name) => {
    await api.post(`/documents/collections/create?name=${encodeURIComponent(name)}`)
    set({ collections: [...get().collections, { name }] })
  },

  remove: async (name) => {
    await api.delete(`/documents/collections/${encodeURIComponent(name)}`)
    set({ collections: get().collections.filter((c) => c.name !== name) })
  },
}))
