import { create } from "zustand"
import { api } from "@/lib/api"
import type { Agent } from "@repo/shared"

interface AgentState {
  agents: Agent[]
  loading: boolean
  selected: Agent | null
  fetch: () => Promise<void>
  create: (data: Partial<Agent>) => Promise<void>
  update: (id: number, data: Partial<Agent>) => Promise<void>
  remove: (id: number) => Promise<void>
  select: (agent: Agent | null) => void
}

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: [],
  loading: false,
  selected: null,

  fetch: async () => {
    set({ loading: true })
    try {
      const agents = await api.get("/agents")
      set({ agents, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  create: async (data) => {
    const agent = await api.post("/agents", data)
    set({ agents: [agent, ...get().agents] })
  },

  update: async (id, data) => {
    const updated = await api.put(`/agents/${id}`, data)
    set({ agents: get().agents.map((a) => (a.id === id ? updated : a)) })
  },

  remove: async (id) => {
    await api.delete(`/agents/${id}`)
    set({ agents: get().agents.filter((a) => a.id !== id) })
  },

  select: (agent) => set({ selected: agent }),
}))
