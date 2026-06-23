"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Modal } from "@/components/ui/modal";
import { AgentCard } from "@/components/agents/agent-card";
import { api, getToken } from "@/lib/api";
import { Plus, Bot, Search, Grid3X3, List, SlidersHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

interface Agent {
  id: number; name: string; agent_type: string; description: string | null;
  status: string; model: string; provider: string; system_prompt: string | null;
  temperature: number; is_active: boolean;
}

const AGENT_TYPES = ["ceo", "sales", "research", "buyer_finder", "operations"];
const PROVIDERS = ["ollama", "openai", "claude", "gemini", "grok", "deepseek", "openrouter", "nvidia"];

export default function AgentsPage() {
  const router = useRouter();
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [search, setSearch] = useState("");
  const [view, setView] = useState<"grid" | "list">("grid");
  const [newAgent, setNewAgent] = useState({
    name: "", agent_type: "research", description: "",
    model: "llama3.1", provider: "ollama", temperature: 0.7,
  });
  const token = getToken();

  const fetchAgents = async () => {
    if (!token) return;
    try { const data = await api.get<Agent[]>("/agents", token); setAgents(data); }
    catch {}
    finally { setLoading(false); }
  };

  useEffect(() => { fetchAgents(); }, []);

  const handleCreate = async () => {
    if (!token || !newAgent.name.trim()) return;
    try {
      await api.post("/agents", newAgent, token);
      setShowCreate(false);
      setNewAgent({ name: "", agent_type: "research", description: "", model: "llama3.1", provider: "ollama", temperature: 0.7 });
      fetchAgents();
    } catch {}
  };

  const handleChat = (agent: Agent) => router.push(`/dashboard/chat?agentId=${agent.id}`);

  const filtered = agents.filter(a =>
    a.name.toLowerCase().includes(search.toLowerCase()) ||
    a.agent_type.includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-5 w-5 animate-spin rounded-full border border-accent-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-base-100">Agents</h1>
          <p className="mt-0.5 text-sm text-base-400">Manage your AI agent workforce</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus size={15} className="mr-1.5" />
          New Agent
        </Button>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-base-500" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search agents..."
            className="w-full rounded-md border border-base-700/50 bg-base-900 py-1.5 pl-8 pr-3 text-sm text-base-100 placeholder-base-500 outline-none transition-colors focus:border-accent-500/50"
          />
        </div>
        <div className="flex items-center gap-1 rounded-md border border-base-700/50 p-0.5">
          <button onClick={() => setView("grid")} className={cn("rounded p-1.5 transition-colors", view === "grid" ? "bg-base-700 text-base-200" : "text-base-500 hover:text-base-300")}>
            <Grid3X3 size={14} />
          </button>
          <button onClick={() => setView("list")} className={cn("rounded p-1.5 transition-colors", view === "list" ? "bg-base-700 text-base-200" : "text-base-500 hover:text-base-300")}>
            <List size={14} />
          </button>
        </div>
      </div>

      {/* Content */}
      {filtered.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-16">
          <Bot size={40} className="mb-3 text-base-600" />
          <p className="text-sm font-medium text-base-400">No agents found</p>
          <p className="mt-1 text-xs text-base-500">Create your first agent to get started</p>
          <Button className="mt-4" onClick={() => setShowCreate(true)}>
            <Plus size={15} className="mr-1.5" />
            Create Agent
          </Button>
        </Card>
      ) : view === "grid" ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {filtered.map((agent) => (
            <AgentCard key={agent.id} agent={agent} onChat={handleChat} />
          ))}
        </div>
      ) : (
        <div className="space-y-0.5">
          {filtered.map((agent) => (
            <div key={agent.id} className="flex items-center gap-4 rounded-md px-3 py-2.5 transition-colors hover:bg-base-800/40">
              <Bot size={16} className="text-base-400" />
              <p className="flex-1 text-sm text-base-200">{agent.name}</p>
              <span className="text-xs text-base-500 capitalize">{agent.agent_type.replace("_", " ")}</span>
              <span className="text-xs text-base-500">{agent.provider}/{agent.model}</span>
              <span className={cn(
                "text-xs capitalize",
                agent.status === "working" ? "text-emerald-400" :
                agent.status === "error" ? "text-red-400" : "text-base-500"
              )}>{agent.status}</span>
              <button onClick={() => handleChat(agent)} className="rounded bg-base-800 px-2 py-1 text-[11px] text-base-400 hover:text-base-200 transition-colors">
                Chat
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Create Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create New Agent">
        <div className="space-y-4">
          <Input label="Agent Name" value={newAgent.name} onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })} placeholder="My Research Agent" />
          <div className="space-y-1">
            <label className="block text-xs font-medium text-base-400">Type</label>
            <select value={newAgent.agent_type} onChange={(e) => setNewAgent({ ...newAgent, agent_type: e.target.value })}
              className="w-full rounded-md border border-base-700/50 bg-base-900 px-3 py-1.5 text-sm text-base-100 outline-none focus:border-accent-500/50">
              {AGENT_TYPES.map((type) => (
                <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1).replace("_", " ")}</option>
              ))}
            </select>
          </div>
          <Input label="Description" value={newAgent.description} onChange={(e) => setNewAgent({ ...newAgent, description: e.target.value })} placeholder="What does this agent do?" />
          <Input label="Model" value={newAgent.model} onChange={(e) => setNewAgent({ ...newAgent, model: e.target.value })} placeholder="llama3.1" />
          <div className="space-y-1">
            <label className="block text-xs font-medium text-base-400">Provider</label>
            <select value={newAgent.provider} onChange={(e) => setNewAgent({ ...newAgent, provider: e.target.value })}
              className="w-full rounded-md border border-base-700/50 bg-base-900 px-3 py-1.5 text-sm text-base-100 outline-none focus:border-accent-500/50">
              {PROVIDERS.map((p) => (
                <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <label className="block text-xs font-medium text-base-400">Temperature ({newAgent.temperature})</label>
            <input type="range" min="0" max="2" step="0.1" value={newAgent.temperature}
              onChange={(e) => setNewAgent({ ...newAgent, temperature: parseFloat(e.target.value) })}
              className="w-full accent-accent-500" />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate}>Create Agent</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
