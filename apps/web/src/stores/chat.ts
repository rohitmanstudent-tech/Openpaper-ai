import { create } from "zustand"
import { api } from "@/lib/api"
import type { Chat, ChatMessage } from "@repo/shared"

interface ChatState {
  chats: Chat[]
  activeChat: Chat | null
  messages: ChatMessage[]
  streaming: boolean
  loading: boolean
  fetchChats: () => Promise<void>
  createChat: (agentId: number) => Promise<void>
  selectChat: (chat: Chat | null) => Promise<void>
  sendMessage: (content: string, stream?: boolean) => Promise<void>
}

export const useChatStore = create<ChatState>((set, get) => ({
  chats: [],
  activeChat: null,
  messages: [],
  streaming: false,
  loading: false,

  fetchChats: async () => {
    const chats = await api.get("/chat/chats")
    set({ chats })
  },

  createChat: async (agentId) => {
    const chat = await api.post("/chat/chats", { agent_id: agentId })
    set({ chats: [chat, ...get().chats], activeChat: chat, messages: [] })
  },

  selectChat: async (chat) => {
    if (!chat) return set({ activeChat: null, messages: [] })
    const data = await api.get(`/chat/chats/${chat.id}`)
    set({ activeChat: data, messages: data.messages || [] })
  },

  sendMessage: async (content, stream = true) => {
    const chat = get().activeChat
    if (!chat) return

    set({ streaming: true })
    const userMsg = { id: Date.now(), chat_id: chat.id, role: "user" as const, content, created_at: new Date().toISOString() }
    set({ messages: [...get().messages, userMsg] })

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/chat/chats/${chat.id}/completions`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
          body: JSON.stringify({ content, stream }),
        }
      )

      if (stream) {
        const reader = res.body?.getReader()
        if (!reader) return
        const decoder = new TextDecoder()
        let fullContent = ""

        set({ messages: [...get().messages, { id: Date.now() + 1, chat_id: chat.id, role: "agent" as const, content: "", created_at: new Date().toISOString() }] })

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          const text = decoder.decode(value)
          const lines = text.split("\n")
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.content) {
                  fullContent += data.content
                  const msgs = get().messages
                  const last = msgs[msgs.length - 1]
                  if (last.role === "agent") {
                    last.content = fullContent
                    set({ messages: [...msgs.slice(0, -1), { ...last }] })
                  }
                }
              } catch { /* skip */ }
            }
          }
        }
      } else {
        const data = await res.json()
        set({ messages: [...get().messages, data] })
      }
    } catch (e) {
      console.error("Chat error:", e)
    }

    set({ streaming: false })
  },
}))
