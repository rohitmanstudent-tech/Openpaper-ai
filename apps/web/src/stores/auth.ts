import { create } from "zustand"
import { api } from "@/lib/api"
import type { User, AuthResponse } from "@repo/shared"

interface AuthState {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; username: string; password: string; full_name: string }) => Promise<void>
  logout: () => void
  loadUser: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("token") : null,
  loading: false,

  login: async (email, password) => {
    set({ loading: true })
    try {
      const data: AuthResponse = await api.post("/auth/login", { email, password })
      api.setToken(data.access_token)
      localStorage.setItem("token", data.access_token)
      set({ user: data.user, token: data.access_token, loading: false })
    } catch {
      set({ loading: false })
      throw new Error("Login failed")
    }
  },

  register: async (data) => {
    set({ loading: true })
    try {
      const res: AuthResponse = await api.post("/auth/register", data)
      api.setToken(res.access_token)
      localStorage.setItem("token", res.access_token)
      set({ user: res.user, token: res.access_token, loading: false })
    } catch {
      set({ loading: false })
      throw new Error("Registration failed")
    }
  },

  logout: () => {
    api.setToken(null)
    localStorage.removeItem("token")
    set({ user: null, token: null })
  },

  loadUser: async () => {
    const token = get().token
    if (!token) return
    try {
      api.setToken(token)
      const user = await api.get("/auth/me")
      set({ user })
    } catch {
      set({ user: null, token: null })
      localStorage.removeItem("token")
    }
  },
}))
