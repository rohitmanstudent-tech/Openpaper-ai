import { create } from "zustand"
import { api } from "@/lib/api"

export interface Task {
  id: number
  title: string
  description: string | null
  status: "pending" | "in_progress" | "completed" | "failed" | "cancelled"
  priority: "low" | "medium" | "high" | "critical"
  assigned_to: number | null
  assigned_agent: number | null
  created_by: number
  parent_task_id: number | null
  due_date: string | null
  completed_at: string | null
  result: string | null
  created_at: string
  updated_at: string
}

type TaskFormData = {
  title: string
  description?: string
  priority?: string
  assigned_agent?: number
  due_date?: string
}

interface TaskState {
  tasks: Task[]
  loading: boolean
  fetch: () => Promise<void>
  create: (data: TaskFormData) => Promise<void>
  update: (id: number, data: Partial<Task>) => Promise<void>
  remove: (id: number) => Promise<void>
}

export const useTaskStore = create<TaskState>((set, get) => ({
  tasks: [],
  loading: false,

  fetch: async () => {
    set({ loading: true })
    try {
      const tasks = await api.get("/tasks")
      set({ tasks, loading: false })
    } catch {
      set({ loading: false })
    }
  },

  create: async (data) => {
    const task = await api.post("/tasks", data)
    set({ tasks: [task, ...get().tasks] })
  },

  update: async (id, data) => {
    const updated = await api.put(`/tasks/${id}`, data)
    set({ tasks: get().tasks.map((t) => (t.id === id ? updated : t)) })
  },

  remove: async (id) => {
    await api.delete(`/tasks/${id}`)
    set({ tasks: get().tasks.filter((t) => t.id !== id) })
  },
}))
