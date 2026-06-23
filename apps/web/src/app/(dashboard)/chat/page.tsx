"use client"

import { useEffect, useRef, useState } from "react"
import { useChatStore } from "@/stores/chat"
import { useAgentStore } from "@/stores/agents"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Send, MessageSquare, Bot, Plus, PanelLeftClose, PanelLeft, Loader2 } from "lucide-react"

export default function ChatPage() {
  const { chats, activeChat, messages, streaming, loading, fetchChats, createChat, selectChat, sendMessage } = useChatStore()
  const { agents, fetch: fetchAgents } = useAgentStore()
  const [input, setInput] = useState("")
  const [panelOpen, setPanelOpen] = useState(true)
  const [mobileChatOpen, setMobileChatOpen] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchChats()
    fetchAgents()
  }, [])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || streaming) return
    await sendMessage(input)
    setInput("")
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = async () => {
    if (agents.length === 0) return
    await createChat(agents[0].id)
  }

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-4">
      {/* Chat List - Desktop */}
      <div className={`${panelOpen ? "w-72" : "w-0"} transition-all duration-300 overflow-hidden space-y-2 flex-shrink-0 hidden md:block`}>
        <Button variant="outline" className="w-full justify-start" onClick={handleNewChat}>
          <Plus className="h-4 w-4 mr-2" /> New Chat
        </Button>
        <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-10rem)]">
          {chats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => { selectChat(chat); setMobileChatOpen(false) }}
              className={`w-full text-left p-3 rounded-lg text-sm transition-colors ${
                activeChat?.id === chat.id ? "bg-accent-500/10 text-accent-400" : "text-muted-foreground hover:bg-white/5"
              }`}
            >
              <p className="truncate">{chat.title || "Untitled"}</p>
              <p className="text-xs opacity-50 mt-1">{new Date(chat.created_at).toLocaleDateString()}</p>
            </button>
          ))}
        </div>
      </div>

      {/* Mobile Chat List */}
      {mobileChatOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <div className="fixed inset-0 bg-black/50" onClick={() => setMobileChatOpen(false)} />
          <div className="fixed left-0 top-0 bottom-0 w-72 bg-base-950 p-4 space-y-2">
            <Button variant="outline" className="w-full justify-start mb-4" onClick={handleNewChat}>
              <Plus className="h-4 w-4 mr-2" /> New Chat
            </Button>
            {chats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => { selectChat(chat); setMobileChatOpen(false) }}
                className={`w-full text-left p-3 rounded-lg text-sm transition-colors ${
                  activeChat?.id === chat.id ? "bg-accent-500/10 text-accent-400" : "text-muted-foreground hover:bg-white/5"
                }`}
              >
                <p className="truncate">{chat.title || "Untitled"}</p>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <div className="flex items-center gap-2 p-2 border-b border-border">
          <Button variant="ghost" size="sm" onClick={() => setPanelOpen(!panelOpen)} className="hidden md:inline-flex">
            {panelOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
          </Button>
          <Button variant="ghost" size="sm" onClick={() => setMobileChatOpen(true)} className="md:hidden">
            <MessageSquare className="h-4 w-4" />
          </Button>
          {activeChat && (
            <>
              <span className="text-sm font-medium text-white truncate">{activeChat.title || "Untitled"}</span>
              <span className="text-xs text-muted-foreground">Chat #{activeChat.id}</span>
            </>
          )}
        </div>

        {!activeChat ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <MessageSquare className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-white mb-2">Select or create a chat</h2>
              <p className="text-muted-foreground text-sm">Choose a chat from the sidebar or start a new one</p>
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-y-auto space-y-4 p-4">
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] md:max-w-[70%] rounded-xl p-4 ${
                    msg.role === "user" ? "bg-accent-500/20 text-white" : "bg-base-900 text-foreground"
                  }`}>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-muted-foreground capitalize">{msg.role}</span>
                      <span className="text-[10px] text-muted-foreground">{new Date(msg.created_at).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  </div>
                </div>
              ))}
              {streaming && (
                <div className="flex justify-start">
                  <div className="bg-base-900 rounded-xl p-4">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 text-accent-400 animate-spin" />
                      <span className="text-sm text-muted-foreground">Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <div className="flex gap-2 p-4 border-t border-border">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message... (Enter to send, Shift+Enter for new line)"
                disabled={streaming}
                className="min-h-[40px] max-h-[120px]"
                rows={1}
              />
              <Button onClick={handleSend} disabled={streaming || !input.trim()} className="self-end">
                {streaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
          </>
        )}
      </div>

      {/* Agent Context Panel */}
      <div className={`${panelOpen ? "w-80" : "w-0"} transition-all duration-300 overflow-hidden flex-shrink-0 hidden lg:block`}>
        {activeChat && (() => {
          const agent = agents.find((a) => a.id === activeChat.agent_id)
          return (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-sm">
                  <Bot className="h-4 w-4" /> Agent Context
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {agent ? (
                  <>
                    <div>
                      <p className="text-muted-foreground text-xs">Name</p>
                      <p className="text-white font-medium">{agent.name}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">Type</p>
                      <p className="text-white capitalize">{agent.agent_type}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">Model</p>
                      <p className="text-white">{agent.provider}/{agent.model}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground text-xs">Status</p>
                      <Badge variant={agent.status === "idle" ? "success" : "default"}>{agent.status}</Badge>
                    </div>
                    {agent.description && (
                      <div>
                        <p className="text-muted-foreground text-xs">Description</p>
                        <p className="text-white text-xs">{agent.description}</p>
                      </div>
                    )}
                  </>
                ) : (
                  <p className="text-muted-foreground">No agent linked</p>
                )}
              </CardContent>
            </Card>
          )
        })()}
      </div>
    </div>
  )
}
