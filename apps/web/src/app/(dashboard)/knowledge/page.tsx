"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useKnowledgeStore } from "@/stores/knowledge"
import { useDocumentStore } from "@/stores/documents"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { DropZone } from "@/components/documents/dropzone"
import { Plus, Database, Trash2, BookOpen } from "lucide-react"

export default function KnowledgePage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const { collections, loading, fetch: fetchKBs, create, remove } = useKnowledgeStore()
  const { upload } = useDocumentStore()
  const [newName, setNewName] = useState("")
  const [showCreate, setShowCreate] = useState(false)

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetchKBs()
  }, [token])

  const handleCreate = async () => {
    if (!newName.trim()) return
    await create(newName.trim())
    setNewName("")
    setShowCreate(false)
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Knowledge Base</h1>
          <p className="text-muted-foreground mt-1">Manage document collections and semantic search indexes</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="h-4 w-4 mr-1" />
          New Collection
        </Button>
      </div>

      {showCreate && (
        <Card className="bg-base-900/50">
          <CardContent className="p-4 flex gap-2">
            <Input
              placeholder="Collection name..."
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              className="flex-1"
            />
            <Button onClick={handleCreate} disabled={!newName.trim()}>Create</Button>
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {collections.map((kb) => (
          <Card key={kb.name} className="bg-base-950 border-border hover:border-accent-500/30 transition-colors">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div className="flex items-center gap-2">
                <Database className="h-4 w-4 text-accent-400" />
                <CardTitle className="text-sm font-medium text-white">{kb.name}</CardTitle>
              </div>
              <Button variant="ghost" size="sm" onClick={() => remove(kb.name)}>
                <Trash2 className="h-4 w-4 text-red-400" />
              </Button>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {kb.point_count ?? "—"} points
              </p>
            </CardContent>
          </Card>
        ))}

        {!loading && collections.length === 0 && (
          <Card className="bg-base-900/50 col-span-full">
            <CardContent className="p-8 text-center">
              <BookOpen className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">No collections yet. Create one to get started.</p>
            </CardContent>
          </Card>
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Upload Document</CardTitle>
        </CardHeader>
        <CardContent>
          <DropZone onUpload={async (file) => { await upload(file); fetchKBs() }} />
        </CardContent>
      </Card>
    </div>
  )
}
