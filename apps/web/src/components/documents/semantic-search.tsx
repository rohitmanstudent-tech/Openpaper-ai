"use client"

import { useState } from "react"
import { api } from "@/lib/api"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Search, Loader2, FileText } from "lucide-react"
import type { Chunk } from "@/stores/documents"

interface SemanticSearchProps {
  collection?: string
  onSelectChunk?: (chunk: Chunk) => void
}

export function SemanticSearch({ collection = "knowledge_base", onSelectChunk }: SemanticSearchProps) {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<{ chunk: Chunk; score: number }[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)

  const handleSearch = async () => {
    if (!query.trim()) return
    setLoading(true)
    setSearched(true)
    try {
      const res = await api.post("/documents/search", {
        query: query.trim(),
        collection,
        limit: 10,
        score_threshold: 0.3,
      })
      setResults(
        (res.results ?? []).map((r: { chunk: Chunk }) => ({
          chunk: r.chunk,
          score: r.chunk.score ?? 0,
        }))
      )
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Input
          placeholder="Search documents semantically..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="flex-1"
        />
        <Button onClick={handleSearch} disabled={loading || !query.trim()}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          Search
        </Button>
      </div>

      {loading && <p className="text-sm text-muted-foreground">Searching...</p>}

      {!loading && searched && results.length === 0 && (
        <p className="text-sm text-muted-foreground">No results found.</p>
      )}

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((r, i) => (
            <Card
              key={`${r.chunk.id}-${i}`}
              className="bg-base-900/50 cursor-pointer hover:bg-base-900 transition-colors"
              onClick={() => onSelectChunk?.(r.chunk)}
            >
              <CardHeader className="p-3 pb-1 flex flex-row items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-accent-400" />
                  <CardTitle className="text-xs font-medium text-muted-foreground">
                    {r.chunk.document_id?.slice(0, 8)}...
                  </CardTitle>
                </div>
                <Badge variant={r.score > 0.7 ? "success" : r.score > 0.5 ? "warning" : "secondary"}>
                  {(r.score * 100).toFixed(0)}%
                </Badge>
              </CardHeader>
              <CardContent className="p-3 pt-1">
                <p className="text-sm text-foreground line-clamp-3">{r.chunk.content}</p>
                <p className="text-xs text-muted-foreground mt-1">Chunk #{r.chunk.chunk_index}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
