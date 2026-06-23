"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useWorkflowStore } from "@/stores/workflows"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { GitBranch, Plus, Play, Trash2, Loader2, FileText } from "lucide-react"
import Link from "next/link"

export default function WorkflowsPage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const { workflows, loading, fetch, create, remove, execute } = useWorkflowStore()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetch()
  }, [token])

  const handleCreate = async () => {
    if (!name.trim()) return
    const wf = await create({ name: name.trim(), description: description.trim() || undefined })
    setOpen(false)
    setName("")
    setDescription("")
    router.push(`/workflows/${wf.id}`)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active": return "success"
      case "draft": return "secondary"
      case "archived": return "warning"
      default: return "secondary"
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Workflows</h1>
          <p className="text-muted-foreground mt-1">Build and manage automated agent workflows</p>
        </div>
        <Dialog open={open} onOpenChange={setOpen}>
          <Button onClick={() => setOpen(true)}>
            <Plus className="h-4 w-4 mr-1" />
            New Workflow
          </Button>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Workflow</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium text-foreground">Name</label>
                <Input placeholder="My Workflow" value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div>
                <label className="text-sm font-medium text-foreground">Description</label>
                <Textarea placeholder="Optional description..." value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
              <Button onClick={handleCreate} disabled={!name.trim()} className="w-full">Create</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading && workflows.length === 0 ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-6 w-6 text-accent-400 animate-spin" />
        </div>
      ) : workflows.length === 0 ? (
        <Card className="bg-base-900/50">
          <CardContent className="p-8 text-center">
            <GitBranch className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">No workflows yet. Create one to get started.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {workflows.map((wf) => (
            <Card key={wf.id} className="bg-base-950 border-border hover:border-accent-500/30 transition-colors">
              <CardHeader className="flex flex-row items-start justify-between pb-2">
                <div className="flex items-center gap-2 min-w-0">
                  <GitBranch className="h-4 w-4 text-accent-400 shrink-0" />
                  <CardTitle className="text-sm font-medium text-white truncate">{wf.name}</CardTitle>
                </div>
                <Badge variant={getStatusColor(wf.status)}>{wf.status}</Badge>
              </CardHeader>
              <CardContent>
                {wf.description && (
                  <p className="text-xs text-muted-foreground mb-2 line-clamp-2">{wf.description}</p>
                )}
                <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
                  <span>{wf.nodes?.length || 0} nodes</span>
                  <span>·</span>
                  <span>{wf.edges?.length || 0} connections</span>
                </div>
                <div className="flex items-center gap-2">
                  <Link href={`/workflows/${wf.id}`} className="flex-1">
                    <Button variant="outline" size="sm" className="w-full">
                      <FileText className="h-3 w-3 mr-1" /> Edit
                    </Button>
                  </Link>
                  <Button variant="outline" size="sm" onClick={() => execute(wf.id)}>
                    <Play className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => remove(wf.id)}>
                    <Trash2 className="h-3 w-3 text-red-400" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
