"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useMemoryStore, type MemoryEntry } from "@/stores/memory"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Search, Brain, Trash2, Loader2 } from "lucide-react"

export default function MemoryPage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const { memories, loading, recall, search, remove } = useMemoryStore()
  const [query, setQuery] = useState("")
  const [mode, setMode] = useState<"recall" | "search">("recall")

  useEffect(() => {
    if (!token) { router.push("/login"); return }
  }, [token])

  const handleSearch = async () => {
    if (!query.trim()) return
    if (mode === "recall") {
      await recall(query)
    } else {
      await search(query)
    }
  }

  const getMemoryTypeColor = (type?: string) => {
    switch (type) {
      case "episodic": return "success"
      case "semantic": return "warning"
      case "procedural": return "default"
      default: return "secondary"
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Memory Explorer</h1>
          <p className="text-muted-foreground mt-1">Browse and search agent memories</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Semantic Memory Search</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <div className="flex rounded-lg border border-border overflow-hidden">
              <button
                onClick={() => setMode("recall")}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  mode === "recall" ? "bg-accent-500/10 text-accent-400" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Recall
              </button>
              <button
                onClick={() => setMode("search")}
                className={`px-3 py-1.5 text-xs font-medium transition-colors ${
                  mode === "search" ? "bg-accent-500/10 text-accent-400" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                Search
              </button>
            </div>
          </div>
          <div className="flex gap-2">
            <Input
              placeholder={mode === "recall" ? "Recall memories semantically..." : "Search memories by query..."}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="flex-1"
            />
            <Button onClick={handleSearch} disabled={loading || !query.trim()}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
            </Button>
          </div>
        </CardContent>
      </Card>

      <div>
        <h2 className="text-lg font-semibold text-white mb-4">
          {memories.length} Result{memories.length !== 1 ? "s" : ""}
        </h2>

        {loading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-6 w-6 text-accent-400 animate-spin" />
          </div>
        ) : memories.length === 0 ? (
          <Card className="bg-base-900/50">
            <CardContent className="p-8 text-center">
              <Brain className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">Search memories to see results.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-3">
            {memories.map((mem) => (
              <Card key={mem.id} className="bg-base-950 border-border">
                <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="h-4 w-4 text-accent-400" />
                    <div className="flex items-center gap-2">
                      <CardTitle className="text-sm font-medium text-white">
                        {mem.id?.slice(0, 8)}...
                      </CardTitle>
                      {mem.memory_type && (
                        <Badge variant={getMemoryTypeColor(mem.memory_type)}>{mem.memory_type}</Badge>
                      )}
                      {mem.score !== undefined && (
                        <Badge variant={mem.score > 0.7 ? "success" : "warning"}>
                          {(mem.score * 100).toFixed(0)}%
                        </Badge>
                      )}
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => remove(mem.id)}>
                    <Trash2 className="h-3 w-3 text-red-400" />
                  </Button>
                </CardHeader>
                <CardContent className="p-4 pt-1">
                  <p className="text-sm text-foreground whitespace-pre-wrap line-clamp-4">{mem.content}</p>
                  {mem.agent_id && (
                    <p className="text-xs text-muted-foreground mt-1">Agent: {mem.agent_id}</p>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
