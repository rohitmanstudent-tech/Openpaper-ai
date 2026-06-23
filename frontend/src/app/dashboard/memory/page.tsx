"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { api, getToken } from "@/lib/api";
import { Brain, Plus, Search, Trash2, Hash, Clock, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface MemoryItem {
  id: number; content: string; memory_type: string;
  scope: string; tags: string | null; created_at: string;
}

export default function MemoryPage() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [newContent, setNewContent] = useState("");
  const [searchMode, setSearchMode] = useState(false);
  const token = getToken();

  const fetchMemories = async () => {
    if (!token) return;
    try { const data = await api.get<MemoryItem[]>("/memory", token); setMemories(data); }
    catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetchMemories(); }, []);

  const handleCreate = async () => {
    if (!token || !newContent.trim()) return;
    try {
      await api.post("/memory", { content: newContent, memory_type: "long_term", scope: "private" }, token);
      setNewContent(""); fetchMemories();
    } catch {}
  };

  const handleSearch = async () => {
    if (!token || !query.trim()) return;
    setSearchMode(true); setLoading(true);
    try { const data = await api.post<MemoryItem[]>("/memory/search", { query }, token); setMemories(data); }
    catch {} finally { setLoading(false); }
  };

  const handleClear = () => { setQuery(""); setSearchMode(false); fetchMemories(); };

  const handleDelete = async (id: number) => {
    if (!token) return;
    try { await api.delete(`/memory/${id}`, token); setMemories((prev) => prev.filter((m) => m.id !== id)); }
    catch {}
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-xl font-semibold text-base-100">Memory Engine</h1>
        <p className="mt-0.5 text-sm text-base-400">Store and search your team's collective knowledge</p>
      </div>

      {/* Search */}
      <div className="flex gap-3">
        <div className="flex-1 max-w-sm">
          <div className="relative">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-base-500" />
            <input value={query} onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              placeholder="Search memories..." className="w-full rounded-md border border-base-700/50 bg-base-900 py-1.5 pl-8 pr-3 text-sm text-base-100 placeholder-base-500 outline-none focus:border-accent-500/50" />
          </div>
        </div>
        <Button variant="secondary" onClick={handleSearch}><Search size={13} className="mr-1" />Search</Button>
        {searchMode && <Button variant="ghost" onClick={handleClear}>Clear</Button>}
      </div>

      {/* Add new */}
      <Card className="p-4">
        <div className="flex gap-3">
          <div className="flex-1">
            <Input value={newContent} onChange={(e) => setNewContent(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              placeholder="Enter a fact, insight, or piece of knowledge..." />
          </div>
          <Button onClick={handleCreate}><Plus size={14} className="mr-1" />Save</Button>
        </div>
      </Card>

      {/* List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-5 w-5 animate-spin rounded-full border border-accent-500 border-t-transparent" />
        </div>
      ) : memories.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-16">
          <Brain size={40} className="mb-3 text-base-600" />
          <p className="text-sm font-medium text-base-400">{searchMode ? "No matching memories" : "No memories yet"}</p>
          <p className="text-xs text-base-500">{searchMode ? "Try a different search term" : "Store your first memory above"}</p>
        </Card>
      ) : (
        <div className="space-y-2">
          {memories.map((memory) => (
            <Card key={memory.id} className="flex items-start justify-between gap-4 p-4">
              <div className="flex-1 min-w-0">
                <p className="text-sm text-base-200 leading-relaxed">{memory.content}</p>
                <div className="mt-2 flex items-center gap-2">
                  <Badge variant={memory.memory_type as any}>{memory.memory_type}</Badge>
                  <Badge variant={memory.scope as any}>{memory.scope}</Badge>
                  {memory.tags && (
                    <span className="flex items-center gap-1 text-[11px] text-base-500">
                      <Hash size={10} />{memory.tags}
                    </span>
                  )}
                  <span className="text-[11px] text-base-600 ml-auto">
                    <Clock size={10} className="inline mr-1" />
                    {new Date(memory.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <button onClick={() => handleDelete(memory.id)}
                className="rounded p-1.5 text-base-500 transition-colors hover:bg-base-700 hover:text-red-400 shrink-0">
                <Trash2 size={14} />
              </button>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
