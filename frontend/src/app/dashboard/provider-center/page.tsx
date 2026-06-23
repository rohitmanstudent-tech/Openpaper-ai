"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, getToken } from "@/lib/api";
import { Radio, CheckCircle2, XCircle, AlertTriangle, Cpu, RefreshCw, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

interface Provider {
  name: string; status: string; default_model: string;
  model_count: number; capabilities: string[]; local: boolean;
}

const providerIcons: Record<string, string> = {
  openai: "OpenAI", claude: "Claude", gemini: "Gemini", grok: "Grok",
  deepseek: "DeepSeek", openrouter: "OpenRouter", ollama: "Ollama", nvidia: "NVIDIA",
};

export default function ProviderCenterPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [loading, setLoading] = useState(true);
  const token = getToken();

  const fetchProviders = async () => {
    if (!token) return;
    try {
      const data = await api.get<Provider[]>("/providers", token);
      setProviders(data);
    } catch {}
    finally { setLoading(false); }
  };

  useEffect(() => { fetchProviders(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-5 w-5 animate-spin rounded-full border border-accent-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-base-100">Provider Center</h1>
          <p className="mt-0.5 text-sm text-base-400">Manage AI provider connections and routing</p>
        </div>
        <button onClick={fetchProviders} className="flex items-center gap-1.5 rounded-md border border-base-700/50 px-3 py-1.5 text-xs text-base-400 transition-colors hover:border-base-600 hover:text-base-200">
          <RefreshCw size={12} />
          Refresh
        </button>
      </div>

      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {providers.map((p) => (
          <Card key={p.name} className="p-4 card-hover">
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-base-800">
                  <Radio size={16} className="text-accent-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-base-100">{providerIcons[p.name] || p.name}</p>
                  <p className="text-[11px] text-base-500">{p.name}</p>
                </div>
              </div>
              {p.status === "available" ? (
                <CheckCircle2 size={16} className="text-emerald-400" />
              ) : p.status === "error" ? (
                <XCircle size={16} className="text-red-400" />
              ) : (
                <AlertTriangle size={16} className="text-amber-400" />
              )}
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="text-base-500">Model</span>
                <span className="text-base-300">{p.default_model}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-base-500">Models</span>
                <span className="text-base-300">{p.model_count}</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-base-500">Type</span>
                <Badge variant={p.local ? "idle" : "active"}>{p.local ? "Local" : "Cloud"}</Badge>
              </div>
            </div>

            {p.capabilities && p.capabilities.length > 0 && (
              <div className="mt-3 pt-3 border-t border-base-700/30 flex flex-wrap gap-1">
                {p.capabilities.map((cap) => (
                  <span key={cap} className="rounded bg-base-800 px-1.5 py-0.5 text-[10px] text-base-500">{cap}</span>
                ))}
              </div>
            )}
          </Card>
        ))}
      </div>

      {/* Routing config summary */}
      <Card className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <Activity size={14} className="text-accent-400" />
          <h2 className="text-sm font-medium text-base-100">Fallback Chain</h2>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-base-500">
          {providers.filter(p => p.status === "available").map((p, i) => (
            <span key={p.name} className="flex items-center gap-1">
              <span className="rounded bg-base-800 px-2 py-0.5 text-base-300">{p.name}</span>
              {i < providers.filter(p2 => p2.status === "available").length - 1 && (
                <span className="text-base-600">→</span>
              )}
            </span>
          ))}
          {providers.filter(p => p.status === "available").length === 0 && (
            <span className="text-base-600">No providers available</span>
          )}
        </div>
      </Card>
    </div>
  );
}
