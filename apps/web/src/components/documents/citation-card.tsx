"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { FileText, Quote } from "lucide-react"

interface CitationCardProps {
  content: string
  documentTitle?: string
  chunkIndex?: number
  score?: number
}

export function CitationCard({ content, documentTitle, chunkIndex, score }: CitationCardProps) {
  return (
    <Card className="bg-base-900/50 border-l-2 border-l-accent-500">
      <CardContent className="p-3">
        <div className="flex items-start gap-2">
          <Quote className="h-4 w-4 text-accent-400 mt-0.5 shrink-0" />
          <div className="space-y-1">
            <p className="text-sm text-foreground italic whitespace-pre-wrap">{content}</p>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {documentTitle && (
                <span className="flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  {documentTitle}
                </span>
              )}
              {chunkIndex !== undefined && <Badge variant="secondary">Chunk #{chunkIndex}</Badge>}
              {score !== undefined && (
                <Badge variant={score > 0.7 ? "success" : "warning"}>
                  {(score * 100).toFixed(0)}% match
                </Badge>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
