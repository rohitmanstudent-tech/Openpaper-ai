import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface MarketplaceItem {
  id: string
  name: string
  item_type: string
  version: string
  description: string
  author: string
  tags: string[]
  downloads: number
  rating: number
  install_status: string
  permissions: string[]
  dependencies: string[]
  config_schema: Record<string, unknown>
  readme: string
  updated_at: string
}

interface InstalledItem {
  id: number
  item_id: string
  name: string
  item_type: string
  version: string
  status: string
  author: string
  description: string | null
  permissions: string[]
  dependencies: string[]
  installed_at: string
  updated_at: string
}

interface MarketplaceState {
  items: MarketplaceItem[]
  installed: InstalledItem[]
  categories: string[]
  total: number
  loading: boolean
  error: string | null
  activeCategory: string | null
  searchQuery: string

  fetchItems: (params?: {
    category?: string
    search?: string
    featured?: boolean
    trending?: boolean
    recentlyAdded?: boolean
  }) => Promise<void>
  fetchInstalled: () => Promise<void>
  installItem: (itemId: string) => Promise<void>
  uninstallItem: (itemId: string) => Promise<void>
  updateItem: (itemId: string) => Promise<void>
  syncWithHub: () => Promise<Record<string, unknown> | null>
  getSyncStatus: () => Promise<Record<string, unknown> | null>
  setActiveCategory: (category: string | null) => void
  setSearchQuery: (query: string) => void
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const useMarketplaceStore = create<MarketplaceState>()(
  persist(
    (set, get) => ({
      items: [],
      installed: [],
      categories: [],
      total: 0,
      loading: false,
      error: null,
      activeCategory: null,
      searchQuery: '',

      fetchItems: async (params) => {
        set({ loading: true, error: null })
        try {
          const query = new URLSearchParams()
          if (params?.category) query.set('category', params.category)
          if (params?.search) query.set('search', params.search)
          if (params?.featured) query.set('featured', 'true')
          if (params?.trending) query.set('trending', 'true')
          if (params?.recentlyAdded) query.set('recently_added', 'true')

          const res = await fetch(`${API_BASE}/api/v1/marketplace?${query.toString()}`, {
            credentials: 'include',
          })
          if (!res.ok) throw new Error('Failed to fetch marketplace items')
          const data = await res.json()
          set({
            items: data.items,
            total: data.total,
            categories: data.categories,
            loading: false,
          })
        } catch (e) {
          set({ error: (e as Error).message, loading: false })
        }
      },

      fetchInstalled: async () => {
        try {
          const res = await fetch(`${API_BASE}/api/v1/marketplace/installed/list`, {
            credentials: 'include',
          })
          if (!res.ok) throw new Error('Failed to fetch installed items')
          const data = await res.json()
          set({ installed: data })
        } catch {
          // silently fail
        }
      },

      installItem: async (itemId) => {
        set({ loading: true, error: null })
        try {
          const res = await fetch(`${API_BASE}/api/v1/marketplace/install`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ item_id: itemId }),
          })
          if (!res.ok) {
            const err = await res.json()
            throw new Error(err.detail || 'Install failed')
          }
          await get().fetchInstalled()
          await get().fetchItems()
        } catch (e) {
          set({ error: (e as Error).message, loading: false })
        }
      },

      uninstallItem: async (itemId) => {
        set({ loading: true, error: null })
        try {
          const res = await fetch(`${API_BASE}/api/v1/marketplace/${itemId}/uninstall`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
          })
          if (!res.ok) {
            const err = await res.json()
            throw new Error(err.detail || 'Uninstall failed')
          }
          await get().fetchInstalled()
          await get().fetchItems()
        } catch (e) {
          set({ error: (e as Error).message, loading: false })
        }
      },

      updateItem: async (itemId) => {
        set({ loading: true, error: null })
        try {
          const res = await fetch(`${API_BASE}/api/v1/marketplace/${itemId}/update`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
          })
          if (!res.ok) {
            const err = await res.json()
            throw new Error(err.detail || 'Update failed')
          }
          await get().fetchInstalled()
          await get().fetchItems()
        } catch (e) {
          set({ error: (e as Error).message, loading: false })
        }
      },

      syncWithHub: async () => {
        try {
          const res = await fetch(`${API_BASE}/api/v1/hub/sync`, {
            method: 'POST',
            credentials: 'include',
          })
          if (!res.ok) throw new Error('Sync failed')
          const data = await res.json()
          await get().fetchItems()
          await get().fetchInstalled()
          return data
        } catch (e) {
          set({ error: (e as Error).message })
          return null
        }
      },

      getSyncStatus: async () => {
        try {
          const res = await fetch(`${API_BASE}/api/v1/hub/sync/status`, {
            credentials: 'include',
          })
          if (!res.ok) throw new Error('Failed to fetch sync status')
          return await res.json()
        } catch {
          return null
        }
      },

      setActiveCategory: (category) => set({ activeCategory: category }),
      setSearchQuery: (query) => set({ searchQuery: query }),
    }),
    {
      name: 'opencode-marketplace-store',
      partialize: (state) => ({
        installed: state.installed,
        activeCategory: state.activeCategory,
      }),
    }
  )
)
