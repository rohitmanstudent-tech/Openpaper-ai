"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useDocumentStore, type Document } from "@/stores/documents"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { DropZone } from "@/components/documents/dropzone"
import { SemanticSearch } from "@/components/documents/semantic-search"
import { FileText, Trash2, Search, Upload, File, Loader2 } from "lucide-react"
import Link from "next/link"

export default function DocumentsPage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const { documents, loading, fetch, upload, remove } = useDocumentStore()
  const [uploading, setUploading] = useState(false)
  const [showSearch, setShowSearch] = useState(false)

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetch()
  }, [token])

  const handleUpload = async (file: File) => {
    setUploading(true)
    try {
      await upload(file)
      await fetch()
    } finally {
      setUploading(false)
    }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Documents</h1>
          <p className="text-muted-foreground mt-1">Upload, manage, and search your documents</p>
        </div>
        <Button variant="outline" onClick={() => setShowSearch(!showSearch)}>
          <Search className="h-4 w-4 mr-1" />
          Semantic Search
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Upload Document</CardTitle>
        </CardHeader>
        <CardContent>
          <DropZone onUpload={handleUpload} />
        </CardContent>
      </Card>

      {showSearch && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Semantic Search</CardTitle>
          </CardHeader>
          <CardContent>
            <SemanticSearch />
          </CardContent>
        </Card>
      )}

      <div>
        <h2 className="text-lg font-semibold text-white mb-4">
          {loading ? "Loading..." : `${documents.length} Document${documents.length !== 1 ? "s" : ""}`}
        </h2>

        {loading && documents.length === 0 ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-6 w-6 text-accent-400 animate-spin" />
          </div>
        ) : documents.length === 0 ? (
          <Card className="bg-base-900/50">
            <CardContent className="p-8 text-center">
              <File className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">No documents yet. Upload one above.</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {documents.map((doc) => (
              <Link key={doc.id} href={`/documents/${doc.id}`}>
                <Card className="bg-base-950 border-border hover:border-accent-500/30 transition-colors h-full">
                  <CardHeader className="flex flex-row items-start justify-between pb-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <FileText className="h-4 w-4 text-accent-400 shrink-0" />
                      <CardTitle className="text-sm font-medium text-white truncate">{doc.title}</CardTitle>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => { e.preventDefault(); remove(doc.id) }}
                    >
                      <Trash2 className="h-4 w-4 text-red-400" />
                    </Button>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant="secondary">{doc.file_type}</Badge>
                      <span>{formatSize(doc.size_bytes)}</span>
                      <span>{doc.chunk_count} chunks</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
