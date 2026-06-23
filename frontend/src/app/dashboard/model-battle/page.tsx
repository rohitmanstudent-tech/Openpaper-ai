"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, getToken } from "@/lib/api";
import { Swords, Send, Clock, Zap, CheckCircle2, XCircle, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";

interface BattleResult {
  model: string; provider: string | null;
  content: string | null; error: string | null;
  latency_ms: number; usage?: Record<string, any>;
}

const MODELS = [
  { id: "gpt-4o", label: "GPT-4o", provider: "OpenAI" },
  { id: "gpt-4o-mini", label: "GPT-4o Mini", provider: "OpenAI" },
  { id: "claude-3-5-sonnet", label: "Claude 3.5 Sonnet", provider: "Anthropic" },
  { id: "gemini-1.5-pro", label: "Gemini 1.5 Pro", provider: "Google" },
  { id: "grok-2", label: "Grok 2", provider: "xAI" },
  { id: "deepseek-chat", label: "DeepSeek Chat", provider: "DeepSeek" },
  { id: "llama3.1", label: "Llama 3.1", provider: "Ollama" },
];

export default function ModelBattlePage() {
  const [selectedModels, setSelectedModels] = useState<string[]>(["gpt-4o-mini", "llama3.1"]);
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<BattleResult[]>([]);
  const token = getToken();

  const toggleModel = (id: string) => {
    setSelectedModels((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id]
    );
  };

  const handleBattle = async () => {
    if (!token || selectedModels.length < 2 || !prompt.trim()) return;
    setLoading(true);
    setResults([]);
    try {
      const data = await api.post<BattleResult[]>("/compare", {
        prompt: prompt.trim(),
        models: selectedModels,
        temperature: 0.3,
        max_tokens: 512,
      }, token);
      setResults(data);
    } catch {}
    finally { setLoading(false); }
  };

  const bestResult = results.length > 0
    ? results.filter(r => !r.error).sort((a, b) => a.latency_ms - b.latency_ms)[0]
    : null;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-semibold text-base-100">Model Battle</h1>
        <p className="mt-0.5 text-sm text-base-400">Compare model outputs side by side</p>
      </div>

      {/* Model selector */}
      <Card className="p-4">
        <h2 className="text-sm font-medium text-base-100 mb-3">Select Models (min 2)</h2>
        <div className="flex flex-wrap gap-2">
          {MODELS.map((m) => (
            <button key={m.id} onClick={() => toggleModel(m.id)}
              className={cn(
                "flex items-center gap-2 rounded-md border px-3 py-2 text-xs transition-colors",
                selectedModels.includes(m.id)
                  ? "border-accent-500/50 bg-accent-500/10 text-accent-400"
                  : "border-base-700/50 text-base-500 hover:border-base-600 hover:text-base-300"
              )}>
              <Swords size={12} />
              <span>{m.label}</span>
              <span className="text-base-600">({m.provider})</span>
            </button>
          ))}
        </div>
      </Card>

      {/* Prompt input */}
      <div className="flex gap-3">
        <div className="flex-1">
          <Input
            value={prompt} onChange={(e) => setPrompt(e.target.value)}
            placeholder="Enter a prompt to compare across models..."
            onKeyDown={(e) => e.key === "Enter" && handleBattle()}
          />
        </div>
        <Button onClick={handleBattle} loading={loading} disabled={selectedModels.length < 2 || !prompt.trim()}>
          <Send size={14} className="mr-1.5" />
          Battle
        </Button>
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <BarChart3 size={14} className="text-accent-400" />
            <h2 className="text-sm font-medium text-base-100">Results</h2>
            {bestResult && (
              <span className="text-xs text-emerald-400">
                Fastest: {bestResult.provider}/{bestResult.model} ({bestResult.latency_ms}ms)
              </span>
            )}
          </div>
          <div className={cn("grid gap-4", results.length === 2 ? "md:grid-cols-2" : results.length === 3 ? "md:grid-cols-3" : "md:grid-cols-2 lg:grid-cols-4")}>
            {results.map((r, i) => (
              <Card key={i} className={cn("p-4", r.error ? "border-red-500/20" : "border-base-700/50")}>
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-sm font-medium text-base-100">{r.model}</p>
                    <p className="text-[11px] text-base-500">{r.provider || "unknown"}</p>
                  </div>
                  {r.error ? (
                    <XCircle size={16} className="text-red-400 shrink-0" />
                  ) : (
                    <CheckCircle2 size={16} className="text-emerald-400 shrink-0" />
                  )}
                </div>

                {r.error ? (
                  <p className="text-xs text-red-400">{r.error}</p>
                ) : (
                  <>
                    <p className="text-xs text-base-300 leading-relaxed line-clamp-6 whitespace-pre-wrap">
                      {r.content}
                    </p>
                    <div className="mt-3 pt-3 border-t border-base-700/30 flex items-center gap-3 text-[11px] text-base-500">
                      <span className="flex items-center gap-1">
                        <Clock size={10} />{r.latency_ms}ms
                      </span>
                      {r.usage && (
                        <span className="flex items-center gap-1">
                          <Zap size={10} />{r.usage.total_tokens || "?"} tokens
                        </span>
                      )}
                    </div>
                  </>
                )}
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
