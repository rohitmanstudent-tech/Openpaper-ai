"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { api, getToken } from "@/lib/api";
import { BarChart3, DollarSign, Zap, Clock, TrendingUp, ArrowUpRight, ArrowDownRight, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface UsageStats {
  total_cost: number; total_tokens: number;
  total_requests: number; by_provider: Record<string, { cost: number; tokens: number; requests: number }>;
}

interface UsageRecord {
  id: number; provider: string; model: string;
  input_tokens: number; output_tokens: number; total_tokens: number;
  total_cost: number; latency_ms: number; timestamp: string;
}

export default function CostAnalyticsPage() {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [records, setRecords] = useState<UsageRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<"7d" | "30d" | "all">("7d");
  const token = getToken();

  useEffect(() => {
    if (!token) return;
    Promise.all([
      api.get<UsageStats>("/providers/usage/stats", token).catch(() => null),
      api.get<UsageRecord[]>("/providers/usage/records", token).catch(() => []),
    ]).then(([s, r]) => {
      setStats(s);
      setRecords(r as UsageRecord[]);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-5 w-5 animate-spin rounded-full border border-accent-500 border-t-transparent" />
      </div>
    );
  }

  const providerColors: Record<string, string> = {
    openai: "bg-accent-500", claude: "bg-emerald-500",
    gemini: "bg-amber-500", grok: "bg-base-400",
    deepseek: "bg-purple-500", openrouter: "bg-pink-500",
    ollama: "bg-base-500", nvidia: "bg-green-500",
  };

  const metrics = [
    { label: "Total Cost", value: stats ? `$${stats.total_cost.toFixed(2)}` : "$0.00", change: "+12.3%", up: true, icon: DollarSign },
    { label: "Total Tokens", value: stats ? stats.total_tokens.toLocaleString() : "0", change: "+8.1%", up: true, icon: Zap },
    { label: "Total Requests", value: stats ? stats.total_requests.toLocaleString() : "0", change: "+15.2%", up: true, icon: Activity },
    { label: "Avg Latency", value: records.length > 0 ? `${Math.round(records.reduce((a, r) => a + r.latency_ms, 0) / records.length)}ms` : "0ms", change: "-5.3%", up: false, icon: Clock },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-base-100">Cost Analytics</h1>
          <p className="mt-0.5 text-sm text-base-400">Track AI usage and spending across providers</p>
        </div>
        <div className="flex items-center gap-1 rounded-md border border-base-700/50 p-0.5">
          {(["7d", "30d", "all"] as const).map((p) => (
            <button key={p} onClick={() => setPeriod(p)}
              className={cn("rounded px-2.5 py-1 text-xs transition-colors", period === p ? "bg-base-700 text-base-200" : "text-base-500 hover:text-base-300")}>
              {p === "all" ? "All Time" : p}
            </button>
          ))}
        </div>
      </div>

      {/* Metrics */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => (
          <Card key={m.label} className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-base-500">{m.label}</span>
              <m.icon size={14} className="text-base-500" />
            </div>
            <p className="text-xl font-semibold text-base-100">{m.value}</p>
            <div className="mt-1 flex items-center gap-1">
              {m.up ? <ArrowUpRight size={11} className="text-emerald-400" /> : <ArrowDownRight size={11} className="text-red-400" />}
              <span className={cn("text-[11px]", m.up ? "text-emerald-400" : "text-red-400")}>{m.change}</span>
              <span className="text-[11px] text-base-600">vs last period</span>
            </div>
          </Card>
        ))}
      </div>

      {/* By Provider */}
      {stats?.by_provider && (
        <Card className="p-4">
          <h2 className="text-sm font-medium text-base-100 mb-4">Cost by Provider</h2>
          <div className="space-y-3">
            {Object.entries(stats.by_provider).map(([name, data]) => (
              <div key={name} className="flex items-center gap-3">
                <div className={cn("h-2 w-2 rounded-full", providerColors[name] || "bg-base-500")} />
                <span className="w-24 text-xs text-base-300 capitalize">{name}</span>
                <div className="flex-1 h-2 rounded-full bg-base-800 overflow-hidden">
                  <div className={cn("h-full rounded-full", providerColors[name] || "bg-base-500")}
                    style={{ width: `${(data.cost / Math.max(...Object.values(stats.by_provider).map(v => v.cost))) * 100}%` }} />
                </div>
                <span className="w-20 text-right text-xs text-base-400">${data.cost.toFixed(2)}</span>
                <span className="w-24 text-right text-xs text-base-500">{data.tokens.toLocaleString()} tok</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recent Usage */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-medium text-base-100">Recent Usage</h2>
          <span className="text-[11px] text-base-500">{records.length} records</span>
        </div>
        <div className="space-y-1">
          {records.slice(0, 10).map((r) => (
            <div key={r.id} className="flex items-center gap-3 rounded-md px-3 py-2 text-xs transition-colors hover:bg-base-800/40">
              <div className={cn("h-1.5 w-1.5 rounded-full", providerColors[r.provider] || "bg-base-500")} />
              <span className="w-20 text-base-300 capitalize">{r.provider}</span>
              <span className="w-32 text-base-500 truncate">{r.model}</span>
              <span className="flex-1 text-base-500">{r.total_tokens} tokens</span>
              <span className="text-base-400">${r.total_cost.toFixed(4)}</span>
              <span className="text-base-600">{r.latency_ms}ms</span>
              <span className="text-base-600">{new Date(r.timestamp).toLocaleDateString()}</span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
