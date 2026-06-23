"use client"

import { useState, useEffect } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { FileText, Search, ChevronDown, ChevronUp } from "lucide-react"
import type { Chunk } from "@/stores/documents"

interface ChunkViewerProps {
  documentId: string
}

export function ChunkViewer({ documentId }: ChunkViewerProps) {
  const [chunks, setChunks] = useState<Chunk[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})

  useEffect(() => {
    (async () => {
      try {
        const res = await api.get(`/documents/${documentId}/chunks?limit=100`)
        setChunks(res.chunks ?? [])
      } catch {
        // ignore
      } finally {
        setLoading(false)
      }
    })()
  }, [documentId])

  if (loading) {
    return <div className="text-sm text-muted-foreground p-4">Loading chunks...</div>
  }

  if (chunks.length === 0) {
    return <div className="text-sm text-muted-foreground p-4">No chunks found.</div>
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
        <FileText className="h-4 w-4" />
        {chunks.length} Chunks
      </h3>
      <ScrollArea className="h-[500px]">
        <div className="space-y-3">
          {chunks.map((chunk) => (
            <Card key={chunk.id} className="bg-base-900/50">
              <CardHeader
                className="p-3 flex flex-row items-center justify-between cursor-pointer"
                onClick={() => setExpanded((prev) => ({ ...prev, [chunk.chunk_index]: !prev[chunk.chunk_index] }))}
              >
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">#{chunk.chunk_index}</Badge>
                  <CardTitle className="text-xs font-medium text-muted-foreground">
                    {chunk.content.slice(0, 60)}...
                  </CardTitle>
                </div>
                {expanded[chunk.chunk_index] ? (
                  <ChevronUp className="h-3 w-3 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-3 w-3 text-muted-foreground" />
                )}
              </CardHeader>
              {expanded[chunk.chunk_index] && (
                <CardContent className="p-3 pt-0">
                  <p className="text-sm text-foreground whitespace-pre-wrap">{chunk.content}</p>
                </CardContent>
              )}
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
