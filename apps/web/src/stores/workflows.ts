import { create } from "zustand"
import { api } from "@/lib/api"

export interface WorkflowNode {
  id: string
  type: string
  position: { x: number; y: number }
  data: Record<string, unknown>
}

export interface WorkflowEdge {
  id: string
  source: string
  target: string
  sourceHandle?: string
  targetHandle?: string
  label?: string
}

export interface Workflow {
  id: number
  name: string
  description: string | null
  status: string
  nodes: WorkflowNode[]
  edges: WorkflowEdge[]
  owner_id: number
  created_at: string
  updated_at: string
}

export interface WorkflowRun {
  id: number
  workflow_id: number
  status: string
  trigger: string
  input_data: Record<string, unknown>
  output_data: Record<string, unknown> | null
  logs: WorkflowLog[]
  error: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
}

export interface WorkflowLog {
  node_id: string
  node_type: string
  status: string
  timestamp: string
  result?: unknown
  error?: string
}

interface WorkflowState {
  workflows: Workflow[]
  runs: WorkflowRun[]
  current: Workflow | null
  loading: boolean
  error: string | null
  fetch: () => Promise<void>
  get: (id: number) => Promise<Workflow>
  create: (data: { name: string; description?: string }) => Promise<Workflow>
  save: (id: number, data: Partial<Workflow>) => Promise<Workflow>
  remove: (id: number) => Promise<void>
  execute: (id: number, input?: Record<string, unknown>) => Promise<WorkflowRun>
  fetchRuns: (workflowId?: number) => Promise<void>
  getRun: (runId: number) => Promise<WorkflowRun>
  cancelRun: (runId: number) => Promise<WorkflowRun>
  setCurrent: (wf: Workflow | null) => void
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  workflows: [],
  runs: [],
  current: null,
  loading: false,
  error: null,

  fetch: async () => {
    set({ loading: true, error: null })
    try {
      const workflows = await api.get("/workflows")
      set({ workflows, loading: false })
    } catch {
      set({ loading: false, error: "Failed to load workflows" })
    }
  },

  get: async (id) => {
    const wf = await api.get(`/workflows/${id}`)
    set({ current: wf })
    return wf
  },

  create: async (data) => {
    const wf = await api.post("/workflows", data)
    set({ workflows: [wf, ...get().workflows] })
    return wf
  },

  save: async (id, data) => {
    const updated = await api.put(`/workflows/${id}`, data)
    set({ current: updated, workflows: get().workflows.map((w) => (w.id === id ? updated : w)) })
    return updated
  },

  remove: async (id) => {
    await api.delete(`/workflows/${id}`)
    set({ workflows: get().workflows.filter((w) => w.id !== id) })
  },

  execute: async (id, input = {}) => {
    return api.post(`/workflows/${id}/execute`, { input_data: input })
  },

  fetchRuns: async (workflowId) => {
    set({ loading: true })
    try {
      const path = workflowId ? `/workflows/${workflowId}/runs` : "/workflows/runs"
      const runs = await api.get(path)
      set({ runs, loading: false })
    } catch {
      set({ loading: false, error: "Failed to load runs" })
    }
  },

  getRun: async (runId) => {
    return api.get(`/workflows/runs/${runId}`)
  },

  cancelRun: async (runId) => {
    return api.post(`/workflows/runs/${runId}/cancel`)
  },

  setCurrent: (wf) => set({ current: wf }),
}))
