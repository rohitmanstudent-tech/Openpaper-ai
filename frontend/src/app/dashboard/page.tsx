"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, getToken } from "@/lib/api";
import {
  Bot,
  MessageSquare,
  Activity,
  ArrowUpRight,
  Clock,
  Zap,
  Users,
  Database,
} from "lucide-react";

interface Agent { id: number; name: string; agent_type: string; status: string; model: string; provider: string; }
interface ChatItem { id: number; title: string | null; updated_at: string; agent_id: number; }

const activityFeed = [
  { id: 1, type: "agent", message: "Research Agent completed market analysis", time: "2m ago", agent: "Researcher" },
  { id: 2, type: "chat", message: "New conversation started with Sales Agent", time: "5m ago", agent: "Sales" },
  { id: 3, type: "task", message: "Q4 report generation task completed", time: "12m ago", agent: "Operations" },
  { id: 4, type: "agent", message: "Buyer Finder identified 3 new leads", time: "18m ago", agent: "Buyer Finder" },
  { id: 5, type: "memory", message: "New knowledge entry: competitor pricing", time: "25m ago", agent: "System" },
  { id: 6, type: "workflow", message: "Onboarding workflow triggered", time: "32m ago", agent: "CEO" },
];

export default function DashboardPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [chats, setChats] = useState<ChatItem[]>([]);
  const [loading, setLoading] = useState(true);
  const token = getToken();

  useEffect(() => {
    if (!token) return;
    Promise.all([
      api.get<Agent[]>("/agents", token).catch(() => []),
      api.get<ChatItem[]>("/chat", token).catch(() => []),
    ]).then(([a, c]) => {
      setAgents(a as Agent[]);
      setChats(c as ChatItem[]);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-5 w-5 animate-spin rounded-full border border-accent-500 border-t-transparent" />
      </div>
    );
  }

  const stats = [
    { label: "Active Agents", value: agents.filter(a => a.status === "working").length, total: agents.length, icon: Bot },
    { label: "Active Chats", value: chats.length, icon: MessageSquare },
    { label: "Tasks Today", value: "12", icon: Activity },
    { label: "API Calls", value: "1,847", icon: Zap },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-base-100">Dashboard</h1>
          <p className="mt-0.5 text-sm text-base-400">Overview of your AI workspace</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-base-500">
          <Clock size={12} />
          <span>Last updated just now</span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((s) => (
          <Card key={s.label} className="flex items-center gap-3 p-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-base-800">
              <s.icon size={16} className="text-base-300" />
            </div>
            <div>
              <p className="text-lg font-semibold text-base-100">
                {s.value}
                {"total" in s && <span className="text-sm font-normal text-base-500">/{s.total}</span>}
              </p>
              <p className="text-xs text-base-500">{s.label}</p>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Activity Feed */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-base-100">Activity Feed</h2>
            <Link href="/dashboard/tasks" className="text-xs text-accent-400 hover:text-accent-300 transition-colors">
              View all
            </Link>
          </div>
          <div className="space-y-0.5">
            {activityFeed.map((item) => (
              <div key={item.id} className="flex items-start gap-3 rounded-md px-3 py-2.5 transition-colors hover:bg-base-800/40">
                <div className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-base-800">
                  <div className={cn(
                    "h-1.5 w-1.5 rounded-full",
                    item.type === "agent" ? "bg-accent-400" :
                    item.type === "chat" ? "bg-emerald-400" :
                    item.type === "task" ? "bg-amber-400" : "bg-base-400"
                  )} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-base-200 truncate">{item.message}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[11px] text-base-500">{item.agent}</span>
                    <span className="text-[11px] text-base-600">·</span>
                    <span className="text-[11px] text-base-500">{item.time}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Related Work Panel */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium text-base-100">Related Work</h2>
          </div>
          <Card className="p-4 space-y-3">
            <div className="flex items-center gap-3 pb-3 border-b border-base-700/30">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-base-800">
                <Bot size={15} className="text-base-300" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-base-200 truncate">Marketing Strategy</p>
                <p className="text-[11px] text-base-500">Research Agent · 2h ago</p>
              </div>
              <ArrowUpRight size={14} className="text-base-500 shrink-0" />
            </div>
            <div className="flex items-center gap-3 pb-3 border-b border-base-700/30">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-base-800">
                <Users size={15} className="text-base-300" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-base-200 truncate">Lead Scoring Model</p>
                <p className="text-[11px] text-base-500">Sales Agent · 4h ago</p>
              </div>
              <ArrowUpRight size={14} className="text-base-500 shrink-0" />
            </div>
            <div className="flex items-center gap-3 pb-3 border-b border-base-700/30">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-base-800">
                <Database size={15} className="text-base-300" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-base-200 truncate">Competitor Analysis</p>
                <p className="text-[11px] text-base-500">Knowledge Base · 6h ago</p>
              </div>
              <ArrowUpRight size={14} className="text-base-500 shrink-0" />
            </div>
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-base-800">
                <Zap size={15} className="text-base-300" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-base-200 truncate">Workflow: Q4 Review</p>
                <p className="text-[11px] text-base-500">CEO Agent · 8h ago</p>
              </div>
              <ArrowUpRight size={14} className="text-base-500 shrink-0" />
            </div>
          </Card>

          {/* Quick actions */}
          <h2 className="text-sm font-medium text-base-100 pt-2">Quick Actions</h2>
          <div className="grid grid-cols-2 gap-2">
            <Link href="/dashboard/agents" className="rounded-md border border-base-700/50 px-3 py-2.5 text-center text-xs text-base-400 transition-colors hover:border-base-600 hover:text-base-200">
              New Agent
            </Link>
            <Link href="/dashboard/chat" className="rounded-md border border-base-700/50 px-3 py-2.5 text-center text-xs text-base-400 transition-colors hover:border-base-600 hover:text-base-200">
              New Chat
            </Link>
            <Link href="/dashboard/workflows" className="rounded-md border border-base-700/50 px-3 py-2.5 text-center text-xs text-base-400 transition-colors hover:border-base-600 hover:text-base-200">
              New Workflow
            </Link>
            <Link href="/dashboard/memory" className="rounded-md border border-base-700/50 px-3 py-2.5 text-center text-xs text-base-400 transition-colors hover:border-base-600 hover:text-base-200">
              Add Memory
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function cn(...classes: (string | false | undefined | null)[]) {
  return classes.filter(Boolean).join(" ");
}
