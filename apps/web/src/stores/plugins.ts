import { create } from "zustand"
import { api } from "@/lib/api"

export interface Plugin {
  id: string
  name: string
  version: string
  description: string | null
  author: string
  plugin_type: string
  status: string
  hooks: string[]
  permissions: string[]
  dependencies: string[]
  error: string | null
  loaded_at: string | null
  directory: string
}

interface PluginsState {
  plugins: Plugin[]
  loading: boolean
  fetch: () => Promise<void>
  install: (data: { name: string; version?: string; description?: string; plugin_type?: string }) => Promise<void>
  toggle: (id: string, enable: boolean) => Promise<void>
  remove: (id: string) => Promise<void>
  discover: () => Promise<void>
}

export const usePluginsStore = create<PluginsState>((set, get) => ({
  plugins: [],
  loading: false,
  fetch: async () => {
    set({ loading: true })
    try {
      const data = await api.get("/plugins")
      set({ plugins: data.plugins, loading: false })
    } catch {
      set({ loading: false })
    }
  },
  install: async (data) => {
    const res = await api.post("/plugins/install", data)
    set({ plugins: [...get().plugins, res.plugin] })
  },
  toggle: async (id, enable) => {
    const res = await api.post(`/plugins/${id}/${enable ? "enable" : "disable"}`)
    set({ plugins: get().plugins.map((p) => (p.id === id ? res.plugin : p)) })
  },
  remove: async (id) => {
    await api.delete(`/plugins/${id}`)
    set({ plugins: get().plugins.filter((p) => p.id !== id) })
  },
  discover: async () => {
    const res = await api.post("/plugins/discover-and-load")
    set({ plugins: res.plugins })
  },
}))
