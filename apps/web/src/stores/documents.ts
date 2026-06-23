import { create } from "zustand"
import { api } from "@/lib/api"

export interface Document {
  id: string
  filename: string
  title: string
  file_type: string
  size_bytes: number
  chunk_count: number
  created_at: string
  status: string
}

export interface Chunk {
  id: string
  document_id: string
  content: string
  chunk_index: number
  score?: number
}

interface DocumentsState {
  documents: Document[]
  loading: boolean
  error: string | null
  fetch: () => Promise<void>
  upload: (file: File, title?: string) => Promise<Document>
  remove: (id: string) => Promise<void>
}

export const useDocumentStore = create<DocumentsState>((set, get) => ({
  documents: [],
  loading: false,
  error: null,

  fetch: async () => {
    set({ loading: true, error: null })
    try {
      const res = await api.get("/documents")
      set({ documents: res.documents ?? [], loading: false })
    } catch {
      set({ loading: false, error: "Failed to load documents" })
    }
  },

  upload: async (file, title) => {
    const fd = new FormData()
    fd.append("file", file)
    if (title) fd.append("title", title)
    const res = await api.upload("/documents/upload", fd)
    const doc: Document = {
      id: res.document_id,
      filename: res.filename,
      title: title || file.name,
      file_type: file.name.split(".").pop() || "",
      size_bytes: file.size,
      chunk_count: res.chunk_count,
      created_at: new Date().toISOString(),
      status: res.status,
    }
    set({ documents: [doc, ...get().documents] })
    return doc
  },

  remove: async (id) => {
    await api.delete(`/documents/${id}`)
    set({ documents: get().documents.filter((d) => d.id !== id) })
  },
}))
