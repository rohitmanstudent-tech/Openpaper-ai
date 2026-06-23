import { create } from "zustand"
import { api } from "@/lib/api"

interface ProviderMetric {
  name: string
  status: string
  models_count: number
}

interface AgentStat {
  id: number
  name: string
  agent_type: string
  status: string
  tasks_completed: number
  tasks_failed: number
  delegation_count: number
  message_count: number
  total_events: number
}

interface WorkflowStat {
  id: number
  name: string
  status: string
  total_runs: number
  successful_runs: number
  failed_runs: number
  avg_duration: number
}

interface MemoryAnalytics {
  total: number
  long_term: number
  short_term: number
  shared: number
  agent_personal: number
  recent: Record<string, unknown>[]
}

interface DocumentAnalytics {
  total_documents: number
  total_chunks: number
  searches_performed: number
  top_documents: { id: string; title: string; chunk_count: number }[]
}

interface SystemCheck {
  status: string
  message?: string
  error?: string
}

interface AnalyticsState {
  providers: Record<string, ProviderMetric>
  agents: Record<string, AgentStat>
  workflows: WorkflowStat[]
  memory: MemoryAnalytics | null
  documents: DocumentAnalytics | null
  system: { status: string; uptime_seconds: number; checks: Record<string, SystemCheck> } | null
  costs: Record<string, unknown> | null
  loading: boolean
  error: string | null
  fetchProviders: () => Promise<void>
  fetchAgents: () => Promise<void>
  fetchWorkflows: () => Promise<void>
  fetchMemory: () => Promise<void>
  fetchDocuments: () => Promise<void>
  fetchSystem: () => Promise<void>
  fetchCosts: () => Promise<void>
  fetchAll: () => Promise<void>
}

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
  providers: {},
  agents: {},
  workflows: [],
  memory: null,
  documents: null,
  system: null,
  costs: null,
  loading: false,
  error: null,

  fetchProviders: async () => {
    try {
      const res = await api.get("/analytics/providers")
      set({ providers: res.providers ?? {} })
    } catch {
      // ignore
    }
  },

  fetchAgents: async () => {
    try {
      const res = await api.get("/analytics/agents")
      set({ agents: res.agents ?? {} })
    } catch {
      // ignore
    }
  },

  fetchWorkflows: async () => {
    try {
      const res = await api.get("/analytics/workflows")
      set({ workflows: res.workflows ?? [] })
    } catch {
      // ignore
    }
  },

  fetchMemory: async () => {
    try {
      const res = await api.get("/analytics/memory")
      set({ memory: res })
    } catch {
      // ignore
    }
  },

  fetchDocuments: async () => {
    try {
      const res = await api.get("/analytics/documents")
      set({ documents: res })
    } catch {
      // ignore
    }
  },

  fetchSystem: async () => {
    try {
      const res = await api.get("/analytics/system")
      set({ system: res })
    } catch {
      // ignore
    }
  },

  fetchCosts: async () => {
    try {
      const res = await api.get("/analytics/costs")
      set({ costs: res })
    } catch {
      // ignore
    }
  },

  fetchAll: async () => {
    set({ loading: true, error: null })
    try {
      const [p, a, w, m, d, s] = await Promise.all([
        api.get("/analytics/providers"),
        api.get("/analytics/agents"),
        api.get("/analytics/workflows"),
        api.get("/analytics/memory"),
        api.get("/analytics/documents"),
        api.get("/analytics/system"),
      ])
      set({
        providers: p.providers ?? {},
        agents: a.agents ?? {},
        workflows: w.workflows ?? [],
        memory: m,
        documents: d,
        system: s,
        loading: false,
      })
    } catch {
      set({ loading: false, error: "Failed to load analytics" })
    }
  },
}))
