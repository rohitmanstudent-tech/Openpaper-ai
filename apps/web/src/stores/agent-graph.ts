import { create } from "zustand"
import { api } from "@/lib/api"

export interface GraphNode {
  id: string
  type: string
  label: string
  agent_type?: string
  status?: string
}

export interface GraphEdge {
  source: string
  target: string
  event_type?: string
  correlation_id?: string
}

export interface GraphEvent {
  event_id: string
  event_type: string
  source_agent?: string
  target_agent?: string
  correlation_id?: string
  timestamp?: string
  data?: Record<string, unknown>
}

interface Delegation {
  event_id: string
  event_type: string
  source_agent: string
  target_agent: string
  timestamp: string
}

interface MemoryLink {
  id: string
  agent_id?: string
  memory_type?: string
  content?: string
  importance_score?: number
}

interface AgentGraphState {
  agents: GraphNode[]
  edges: GraphEdge[]
  events: GraphEvent[]
  delegations: Delegation[]
  memories: MemoryLink[]
  memoryCount: number
  loading: boolean
  error: string | null
  fetchGraph: () => Promise<void>
  fetchEvents: (limit?: number) => Promise<void>
  fetchDelegations: () => Promise<void>
  fetchMemoryLinks: () => Promise<void>
}

export const useAgentGraphStore = create<AgentGraphState>((set) => ({
  agents: [],
  edges: [],
  events: [],
  delegations: [],
  memories: [],
  memoryCount: 0,
  loading: false,
  error: null,

  fetchGraph: async () => {
    set({ loading: true, error: null })
    try {
      const res = await api.get("/agent-graph")
      set({
        agents: res.nodes ?? [],
        edges: res.edges ?? [],
        events: res.events ?? [],
        memoryCount: res.memory_count ?? 0,
        loading: false,
      })
    } catch {
      set({ loading: false, error: "Failed to load agent graph" })
    }
  },

  fetchEvents: async (limit) => {
    try {
      const res = await api.get(`/agent-graph/events${limit ? `?limit=${limit}` : ""}`)
      set({ events: res.events ?? [] })
    } catch {
      // ignore
    }
  },

  fetchDelegations: async () => {
    try {
      const res = await api.get("/agent-graph/delegations")
      set({ delegations: res.delegations ?? [] })
    } catch {
      // ignore
    }
  },

  fetchMemoryLinks: async () => {
    try {
      const res = await api.get("/agent-graph/memory-links")
      set({ memories: res.memories ?? [], memoryCount: res.total ?? 0 })
    } catch {
      // ignore
    }
  },
}))
