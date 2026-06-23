"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Share2, Bot, MessageSquare, ArrowRight, Activity, Zap, Clock, Filter } from "lucide-react";
import { cn } from "@/lib/utils";

interface AgentNode {
  id: string; name: string; type: string; status: string;
  messages: number; lastActive: string;
}

interface MessageEdge {
  from: string; to: string; count: number; lastMessage: string;
}

const agents: AgentNode[] = [
  { id: "ceo", name: "CEO Agent", type: "ceo", status: "idle", messages: 142, lastActive: "5m ago" },
  { id: "research", name: "Research Agent", type: "research", status: "working", messages: 389, lastActive: "Now" },
  { id: "sales", name: "Sales Agent", type: "sales", status: "working", messages: 256, lastActive: "1m ago" },
  { id: "buyer", name: "Buyer Finder", type: "buyer_finder", status: "idle", messages: 98, lastActive: "15m ago" },
  { id: "operations", name: "Operations Agent", type: "operations", status: "paused", messages: 67, lastActive: "1h ago" },
];

const edges: MessageEdge[] = [
  { from: "ceo", to: "research", count: 89, lastMessage: "2m ago" },
  { from: "ceo", to: "sales", count: 67, lastMessage: "5m ago" },
  { from: "research", to: "buyer", count: 34, lastMessage: "10m ago" },
  { from: "sales", to: "operations", count: 23, lastMessage: "25m ago" },
  { from: "research", to: "sales", count: 45, lastMessage: "8m ago" },
  { from: "buyer", to: "sales", count: 18, lastMessage: "30m ago" },
];

const recentMessages = [
  { from: "CEO Agent", to: "Research Agent", content: "Analyze Q4 market trends and provide summary", time: "2m ago", type: "command" },
  { from: "Research Agent", to: "Sales Agent", content: "Found 3 new competitor movements in pricing", time: "5m ago", type: "insight" },
  { from: "Buyer Finder", to: "Sales Agent", content: "New lead identified: Acme Corp (score: 92)", time: "12m ago", type: "lead" },
  { from: "Research Agent", to: "CEO Agent", content: "Q4 analysis complete — 12-page report ready", time: "18m ago", type: "result" },
  { from: "Sales Agent", to: "Operations Agent", content: "Need updated pricing sheet for demo tomorrow", time: "25m ago", type: "request" },
];

export default function AgentGraphPage() {
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [view, setView] = useState<"graph" | "messages">("graph");

  const getAgentColor = (type: string) => {
    switch (type) {
      case "ceo": return "border-accent-400/50 bg-accent-400/10";
      case "research": return "border-emerald-400/50 bg-emerald-400/10";
      case "sales": return "border-blue-400/50 bg-blue-400/10";
      case "buyer_finder": return "border-amber-400/50 bg-amber-400/10";
      case "operations": return "border-purple-400/50 bg-purple-400/10";
      default: return "border-base-600/50 bg-base-800/50";
    }
  };

  const getAgentAccent = (type: string) => {
    switch (type) {
      case "ceo": return "text-accent-400"; case "research": return "text-emerald-400";
      case "sales": return "text-blue-400"; case "buyer_finder": return "text-amber-400";
      case "operations": return "text-purple-400"; default: return "text-base-400";
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-base-100">Agent Communication Graph</h1>
          <p className="mt-0.5 text-sm text-base-400">Visualize inter-agent message flows in real-time</p>
        </div>
        <div className="flex items-center gap-1 rounded-md border border-base-700/50 p-0.5">
          <button onClick={() => setView("graph")} className={cn("rounded px-2.5 py-1 text-xs transition-colors", view === "graph" ? "bg-base-700 text-base-200" : "text-base-500 hover:text-base-300")}>
            Graph
          </button>
          <button onClick={() => setView("messages")} className={cn("rounded px-2.5 py-1 text-xs transition-colors", view === "messages" ? "bg-base-700 text-base-200" : "text-base-500 hover:text-base-300")}>
            Messages
          </button>
        </div>
      </div>

      {view === "graph" ? (
        <>
          {/* Agent nodes */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
            {agents.map((agent) => (
              <button key={agent.id} onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
                className={cn(
                  "rounded-lg border p-3 text-left transition-all",
                  selectedAgent === agent.id ? "border-accent-400/60 bg-accent-400/5" : "border-base-700/50 bg-base-900/60 card-hover",
                  getAgentColor(agent.type)
                )}>
                <div className="flex items-center gap-2 mb-2">
                  <Bot size={15} className={getAgentAccent(agent.type)} />
                  <p className="text-sm font-medium text-base-100">{agent.name}</p>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-base-500">
                  <span className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    agent.status === "working" ? "bg-emerald-400" :
                    agent.status === "paused" ? "bg-amber-400" : "bg-base-500"
                  )} />
                  <span className="capitalize">{agent.status}</span>
                  <span className="text-base-600">·</span>
                  <span>{agent.messages} msgs</span>
                </div>
                <p className="mt-1 text-[11px] text-base-600">Active {agent.lastActive}</p>
              </button>
            ))}
          </div>

          {/* Edge summary */}
          <Card className="p-4">
            <div className="flex items-center gap-2 mb-3">
              <Share2 size={14} className="text-accent-400" />
              <h2 className="text-sm font-medium text-base-100">Message Flow</h2>
            </div>
            <div className="space-y-2">
              {edges.map((edge, i) => {
                const from = agents.find(a => a.id === edge.from);
                const to = agents.find(a => a.id === edge.to);
                if (!from || !to) return null;
                return (
                  <div key={i} className="flex items-center gap-3 rounded-md bg-base-800/30 px-3 py-2 text-xs">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className={`h-1.5 w-1.5 rounded-full ${getAgentColor(from.type).includes("accent") ? "bg-accent-400" : getAgentColor(from.type).includes("emerald") ? "bg-emerald-400" : "bg-blue-400"}`} />
                      <span className="text-base-300">{from.name}</span>
                    </div>
                    <ArrowRight size={11} className="text-base-600 shrink-0" />
                    <div className="flex items-center gap-1.5 min-w-0">
                      <span className={`h-1.5 w-1.5 rounded-full ${getAgentColor(to.type).includes("accent") ? "bg-accent-400" : getAgentColor(to.type).includes("emerald") ? "bg-emerald-400" : "bg-blue-400"}`} />
                      <span className="text-base-300">{to.name}</span>
                    </div>
                    <span className="ml-auto text-base-500">{edge.count} messages</span>
                    <span className="text-base-600">{edge.lastMessage}</span>
                  </div>
                );
              })}
            </div>
          </Card>
        </>
      ) : (
        <Card className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium text-base-100">Recent Inter-Agent Messages</h2>
            <span className="flex items-center gap-1 text-[11px] text-base-500">
              <Activity size={11} /> Live
            </span>
          </div>
          <div className="space-y-0.5">
            {recentMessages.map((msg, i) => (
              <div key={i} className="flex items-start gap-3 rounded-md px-3 py-2.5 transition-colors hover:bg-base-800/40">
                <MessageSquare size={13} className="mt-0.5 text-base-500 shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-base-300">{msg.from}</span>
                    <ArrowRight size={10} className="text-base-600" />
                    <span className="text-xs font-medium text-base-300">{msg.to}</span>
                    <Badge variant={msg.type === "command" ? "working" : msg.type === "insight" ? "active" : msg.type === "lead" ? "completed" : "idle"} className="text-[10px]">
                      {msg.type}
                    </Badge>
                  </div>
                  <p className="mt-0.5 text-xs text-base-500">{msg.content}</p>
                  <p className="mt-0.5 text-[11px] text-base-600">{msg.time}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
