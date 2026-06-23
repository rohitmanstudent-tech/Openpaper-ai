"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Message } from "@/components/chat/message";
import { ChatInput } from "@/components/chat/chat-input";
import { api, getToken } from "@/lib/api";
import { cn } from "@/lib/utils";
import {
  MessageSquare, Bot, Plus, ChevronLeft, PanelRightOpen,
  History, Sparkles, Hash, Clock, ArrowUpRight
} from "lucide-react";

interface Agent { id: number; name: string; agent_type: string; }
interface ChatItem { id: number; title: string | null; agent_id: number; updated_at: string; }
interface MessageData { id: number; chat_id: number; role: string; content: string; created_at: string; }

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function ChatPage() {
  const searchParams = useSearchParams();
  const agentIdParam = searchParams.get("agentId");
  const [agents, setAgents] = useState<Agent[]>([]);
  const [chats, setChats] = useState<ChatItem[]>([]);
  const [activeChat, setActiveChat] = useState<number | null>(null);
  const [messages, setMessages] = useState<MessageData[]>([]);
  const [streamingContent, setStreamingContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [showPanel, setShowPanel] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const token = getToken();

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  useEffect(() => { scrollToBottom(); }, [messages, streamingContent]);

  useEffect(() => {
    if (!token) return;
    Promise.all([
      api.get<Agent[]>("/agents", token).catch(() => []),
      api.get<ChatItem[]>("/chat", token).catch(() => []),
    ]).then(([agentsData, chatsData]) => {
      setAgents(agentsData as Agent[]);
      setChats(chatsData as ChatItem[]);
      if (agentIdParam && (agentsData as Agent[]).length > 0) {
        const agent = (agentsData as Agent[]).find((a) => a.id === Number(agentIdParam));
        if (agent) handleNewChat(agent);
      }
    }).finally(() => setLoading(false));
  }, []);

  const handleNewChat = async (agent: Agent) => {
    if (!token) return;
    try {
      const chat = await api.post<ChatItem>("/chat", { agent_id: agent.id, title: `Chat with ${agent.name}` }, token);
      setChats((prev) => [chat, ...prev]);
      setActiveChat(chat.id);
      setMessages([]);
      setShowSidebar(false);
    } catch {}
  };

  const loadChat = async (chatId: number) => {
    if (!token) return;
    try {
      const data = await api.get<{ id: number; messages: MessageData[] }>(`/chat/${chatId}`, token);
      setActiveChat(chatId);
      setMessages(data.messages);
      setShowSidebar(false);
    } catch {}
  };

  const handleSend = useCallback(async (content: string) => {
    if (!token || !activeChat) return;
    setSending(true);
    setStreamingContent("");
    const userMsg: MessageData = {
      id: Date.now(), chat_id: activeChat, role: "user",
      content, created_at: new Date().toISOString()
    };
    setMessages((prev) => [...prev, userMsg]);
    try {
      const response = await fetch(`${API_URL}/chat/${activeChat}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ content, stream: true }),
      });
      if (!response.ok) throw new Error("Failed");
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const text = decoder.decode(value);
          const lines = text.split("\n");
          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));
                if (data.event === "chunk") {
                  fullContent += data.data.content;
                  setStreamingContent(fullContent);
                } else if (data.event === "done") {
                  const agentMsg: MessageData = {
                    id: data.data.id, chat_id: activeChat, role: "agent",
                    content: data.data.content, created_at: data.data.created_at
                  };
                  setMessages((prev) => [...prev, agentMsg]);
                  setStreamingContent("");
                }
              } catch { continue; }
            }
          }
        }
      }
    } catch {}
    finally { setSending(false); }
  }, [token, activeChat]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-5 w-5 animate-spin rounded-full border border-accent-500 border-t-transparent" />
      </div>
    );
  }

  const activeAgent = activeChat ? agents.find(a => chats.find(c => c.id === activeChat)?.agent_id === a.id) : null;

  return (
    <div className="flex h-[calc(100vh-3rem)] -mx-6 -mt-6 gap-0 overflow-hidden">
      {/* Chat sidebar */}
      <div className={cn(
        "w-64 shrink-0 border-r border-base-700/50 bg-base-900/50 flex flex-col transition-all duration-200",
        !showSidebar && "hidden"
      )}>
        <div className="flex items-center justify-between px-3 py-2.5 border-b border-base-700/30">
          <h2 className="text-xs font-medium text-base-100">Conversations</h2>
          <button onClick={() => setShowSidebar(false)} className="rounded p-1 text-base-500 hover:text-base-300">
            <ChevronLeft size={14} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <p className="px-2 pb-1 pt-2 text-[11px] font-medium uppercase tracking-wider text-base-500">Agents</p>
          {agents.map((agent) => (
            <button key={agent.id} onClick={() => handleNewChat(agent)}
              className="flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-base-400 transition-colors hover:bg-base-800 hover:text-base-200">
              <Bot size={15} className="text-base-500" />
              <span>{agent.name}</span>
            </button>
          ))}
          <p className="px-2 pb-1 pt-3 text-[11px] font-medium uppercase tracking-wider text-base-500">Recent</p>
          {chats.slice(0, 8).map((chat) => (
            <button key={chat.id} onClick={() => loadChat(chat.id)}
              className={cn(
                "flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-sm transition-colors",
                activeChat === chat.id
                  ? "bg-accent-500/10 text-accent-400"
                  : "text-base-500 hover:bg-base-800 hover:text-base-300"
              )}>
              <MessageSquare size={14} />
              <span className="truncate">{chat.title || `Chat #${chat.id}`}</span>
            </button>
          ))}
        </div>
        <div className="p-2 border-t border-base-700/30">
          <button onClick={() => setShowSidebar(!showSidebar)} className="flex w-full items-center gap-2.5 rounded-md px-2.5 py-2 text-sm text-base-500 transition-colors hover:bg-base-800 hover:text-base-300">
            <Plus size={14} />
            <span>New Chat</span>
          </button>
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col min-w-0">
        {activeChat ? (
          <>
            {/* Chat header */}
            <div className="flex items-center gap-3 border-b border-base-700/30 px-4 py-2.5">
              {!showSidebar && (
                <button onClick={() => setShowSidebar(true)} className="rounded p-1 text-base-500 hover:text-base-300">
                  <PanelRightOpen size={14} />
                </button>
              )}
              <Bot size={15} className="text-accent-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-base-100 truncate">
                  {chats.find(c => c.id === activeChat)?.title || "Chat"}
                </p>
                {activeAgent && (
                  <p className="text-[11px] text-base-500">{activeAgent.name} · {activeAgent.agent_type}</p>
                )}
              </div>
              <button onClick={() => setShowPanel(!showPanel)} className={cn(
                "rounded p-1.5 transition-colors",
                showPanel ? "bg-base-700 text-base-300" : "text-base-500 hover:text-base-300"
              )}>
                <PanelRightOpen size={14} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
              {messages.length === 0 && !streamingContent ? (
                <div className="flex h-full flex-col items-center justify-center text-center">
                  <MessageSquare size={48} className="mb-3 text-base-700" />
                  <p className="text-sm font-medium text-base-500">Start a conversation</p>
                  <p className="text-xs text-base-600">Send a message to begin chatting with {activeAgent?.name || "your agent"}</p>
                </div>
              ) : (
                <>
                  {messages.map((msg) => (
                    <Message key={msg.id} role={msg.role as "user" | "agent"} content={msg.content}
                      timestamp={new Date(msg.created_at).toLocaleTimeString()} />
                  ))}
                  {streamingContent && <Message role="agent" content={streamingContent} isStreaming />}
                </>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="px-4 py-3 border-t border-base-700/30">
              <ChatInput onSend={handleSend} loading={sending} />
            </div>
          </>
        ) : (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <MessageSquare size={56} className="mb-4 text-base-700" />
            <h2 className="text-lg font-medium text-base-300">Select a conversation</h2>
            <p className="mt-1 text-sm text-base-500">Choose an agent from the sidebar to begin</p>
          </div>
        )}
      </div>

      {/* Right panel - Agent context & activity */}
      {showPanel && activeChat && (
        <div className="w-72 shrink-0 border-l border-base-700/50 bg-base-900/50 overflow-y-auto">
          <div className="px-3 py-2.5 border-b border-base-700/30">
            <h2 className="text-xs font-medium text-base-100">Context</h2>
          </div>
          <div className="p-3 space-y-4">
            {activeAgent && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-base-400">Active Agent</p>
                <div className="flex items-center gap-2.5 rounded-md bg-base-800/50 px-3 py-2">
                  <Bot size={15} className="text-accent-400" />
                  <div>
                    <p className="text-sm text-base-200">{activeAgent.name}</p>
                    <p className="text-[11px] text-base-500 capitalize">{activeAgent.agent_type}</p>
                  </div>
                </div>
              </div>
            )}
            <div className="space-y-2">
              <p className="text-xs font-medium text-base-400">Suggested</p>
              <div className="space-y-1">
                {["Summarize this conversation", "Generate a report", "Find related memories", "Continue research"].map((s) => (
                  <button key={s} className="flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-xs text-base-500 transition-colors hover:bg-base-800 hover:text-base-300">
                    <Sparkles size={11} />
                    {s}
                  </button>
                ))}
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-xs font-medium text-base-400">Recent Activity</p>
              <div className="space-y-1.5">
                {[
                  { text: "Memory search: Q4 data", time: "2m ago" },
                  { text: "Provider: OpenAI GPT-4o", time: "8m ago" },
                  { text: "Token usage: 1,847", time: "15m ago" },
                ].map((a, i) => (
                  <div key={i} className="flex items-start gap-2">
                    <Clock size={11} className="mt-0.5 text-base-600" />
                    <div>
                      <p className="text-xs text-base-500">{a.text}</p>
                      <p className="text-[11px] text-base-600">{a.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
