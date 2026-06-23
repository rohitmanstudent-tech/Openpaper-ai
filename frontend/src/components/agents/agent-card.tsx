"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Bot, MessageSquare, Play, Cpu } from "lucide-react";
import { cn } from "@/lib/utils";

interface Agent {
  id: number; name: string; agent_type: string; description: string | null;
  status: string; model: string; provider: string; temperature: number;
}

const statusColors: Record<string, string> = {
  idle: "bg-base-700",
  working: "bg-emerald-400",
  paused: "bg-amber-400",
  error: "bg-red-400",
};

interface AgentCardProps {
  agent: Agent;
  onChat?: (agent: Agent) => void;
}

const typeIcons: Record<string, string> = {
  ceo: "👑", sales: "💼", research: "🔬", buyer_finder: "🎯", operations: "⚙️",
};

export function AgentCard({ agent, onChat }: AgentCardProps) {
  return (
    <Card className="p-4 card-hover group">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-base-800 text-base">
            {typeIcons[agent.agent_type] || "🤖"}
          </div>
          <div>
            <p className="text-sm font-medium text-base-100">{agent.name}</p>
            <p className="text-xs text-base-500 capitalize">{agent.agent_type.replace("_", " ")}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={cn("h-1.5 w-1.5 rounded-full", statusColors[agent.status] || "bg-base-600")} />
          <span className="text-[11px] text-base-500 capitalize">{agent.status}</span>
        </div>
      </div>

      {agent.description && (
        <p className="mt-3 text-xs text-base-400 line-clamp-2">{agent.description}</p>
      )}

      <div className="mt-3 flex items-center gap-2">
        <Cpu size={11} className="text-base-500" />
        <span className="text-[11px] text-base-500">{agent.provider}/{agent.model}</span>
      </div>

      <div className="mt-3 flex items-center gap-2 pt-3 border-t border-base-700/30">
        {onChat && (
          <button
            onClick={() => onChat(agent)}
            className="flex items-center gap-1.5 rounded-md bg-base-800 px-2.5 py-1.5 text-[11px] font-medium text-base-300 transition-colors hover:bg-base-700 hover:text-base-100"
          >
            <MessageSquare size={12} />
            Chat
          </button>
        )}
        <button className="flex items-center gap-1.5 rounded-md bg-base-800 px-2.5 py-1.5 text-[11px] font-medium text-base-300 transition-colors hover:bg-base-700 hover:text-base-100">
          <Play size={12} />
          Run
        </button>
      </div>
    </Card>
  );
}
