"use client"

import { useEffect, useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useDocumentStore } from "@/stores/documents"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ChunkViewer } from "@/components/documents/chunk-viewer"
import { FileText, ArrowLeft, Trash2, Loader2 } from "lucide-react"
import Link from "next/link"

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuthStore()
  const router = useRouter()
  const { documents, fetch, remove } = useDocumentStore()
  const doc = documents.find((d) => d.id === id)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    (async () => {
      if (documents.length === 0) await fetch()
      setLoading(false)
    })()
  }, [token, id])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-6 w-6 text-accent-400 animate-spin" />
      </div>
    )
  }

  if (!doc) {
    return (
      <div className="space-y-4">
        <p className="text-muted-foreground">Document not found.</p>
        <Link href="/documents"><Button variant="outline"><ArrowLeft className="h-4 w-4 mr-1" /> Back</Button></Link>
      </div>
    )
  }

  const handleDelete = async () => {
    await remove(doc.id)
    router.push("/documents")
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/documents">
            <Button variant="ghost" size="sm"><ArrowLeft className="h-4 w-4" /></Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-white">{doc.title}</h1>
            <p className="text-muted-foreground mt-1">{doc.filename}</p>
          </div>
        </div>
        <Button variant="destructive" size="sm" onClick={handleDelete}>
          <Trash2 className="h-4 w-4 mr-1" /> Delete
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-xs text-muted-foreground">Type</p>
                <Badge variant="secondary">{doc.file_type}</Badge>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Size</p>
                <p className="text-sm text-white">{formatSize(doc.size_bytes)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Chunks</p>
                <p className="text-sm text-white">{doc.chunk_count}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Created</p>
                <p className="text-sm text-white">{new Date(doc.created_at).toLocaleString()}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Status</p>
                <Badge variant={doc.status === "indexed" ? "success" : "warning"}>{doc.status}</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex flex-row items-center gap-2">
              <FileText className="h-4 w-4 text-accent-400" />
              <CardTitle className="text-lg">Chunks</CardTitle>
            </CardHeader>
            <CardContent>
              <ChunkViewer documentId={id} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
