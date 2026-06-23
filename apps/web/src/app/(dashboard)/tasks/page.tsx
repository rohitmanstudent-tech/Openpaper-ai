"use client"

import { useEffect, useState, useCallback } from "react"
import { useTaskStore, type Task } from "@/stores/tasks"
import { useAgentStore } from "@/stores/agents"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Plus, CheckCircle, Circle, Clock, AlertCircle, Trash2, Play, Pencil, X } from "lucide-react"

const STATUS_ICONS: Record<string, typeof Circle> = {
  pending: Circle,
  in_progress: Clock,
  completed: CheckCircle,
  failed: AlertCircle,
  cancelled: Circle,
}

const STATUS_COLORS: Record<string, string> = {
  pending: "text-muted-foreground",
  in_progress: "text-accent-400",
  completed: "text-emerald-400",
  failed: "text-red-400",
  cancelled: "text-muted-foreground",
}

const PRIORITY_COLORS: Record<string, string> = {
  low: "text-muted-foreground",
  medium: "text-accent-400",
  high: "text-amber-400",
  critical: "text-red-400",
}

export default function TasksPage() {
  const { tasks, loading, fetch, create, update, remove } = useTaskStore()
  const { agents, fetch: fetchAgents } = useAgentStore()
  const [showCreate, setShowCreate] = useState(false)
  const [createForm, setCreateForm] = useState({ title: "", description: "", priority: "medium", assigned_agent: "" })
  const [editTask, setEditTask] = useState<Task | null>(null)
  const [editForm, setEditForm] = useState({ title: "", description: "", status: "", priority: "", assigned_agent: "" })
  const [mounted, setMounted] = useState(false)

  useEffect(() => { setMounted(true); fetch(); fetchAgents() }, [])

  useEffect(() => {
    if (!mounted) return
    const interval = setInterval(() => fetch(), 10000)
    return () => clearInterval(interval)
  }, [mounted])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    await create({
      title: createForm.title,
      description: createForm.description || undefined,
      priority: createForm.priority,
      assigned_agent: createForm.assigned_agent ? parseInt(createForm.assigned_agent) : undefined,
    })
    setCreateForm({ title: "", description: "", priority: "medium", assigned_agent: "" })
    setShowCreate(false)
  }

  const handleEdit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editTask) return
    await update(editTask.id, {
      title: editForm.title,
      description: editForm.description || null,
      status: editForm.status as Task["status"],
      priority: editForm.priority as Task["priority"],
      assigned_agent: editForm.assigned_agent ? parseInt(editForm.assigned_agent) : null,
    })
    setEditTask(null)
  }

  const openEdit = (task: Task) => {
    setEditTask(task)
    setEditForm({
      title: task.title,
      description: task.description || "",
      status: task.status,
      priority: task.priority,
      assigned_agent: task.assigned_agent?.toString() || "",
    })
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Tasks</h1>
          <p className="text-muted-foreground text-sm mt-1">Manage and track agent tasks</p>
        </div>
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogTrigger>
            <Button><Plus className="h-4 w-4 mr-2" /> New Task</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Task</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="space-y-2">
                <Label>Title</Label>
                <Input value={createForm.title} onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })} required />
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea value={createForm.description} onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })} />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Priority</Label>
                  <Select value={createForm.priority} onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value })}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Assign Agent</Label>
                  <Select value={createForm.assigned_agent} onChange={(e) => setCreateForm({ ...createForm, assigned_agent: e.target.value })}>
                    <option value="">Unassigned</option>
                    {agents.map((a) => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </Select>
                </div>
              </div>
              <Button type="submit">Create</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex gap-2">
        {["all", "pending", "in_progress", "completed", "failed"].map((s) => (
          <Button key={s} variant="ghost" size="sm" className="capitalize">{s.replace("_", " ")}</Button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}><CardContent className="h-16 animate-pulse bg-base-800/50 rounded-xl" /></Card>
          ))}
        </div>
      ) : tasks.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <CheckCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No tasks yet. Create one to get started.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {tasks.map((task) => {
            const StatusIcon = STATUS_ICONS[task.status] || Circle
            const agent = agents.find((a) => a.id === task.assigned_agent)
            return (
              <Card key={task.id} className="group">
                <CardContent className="flex items-center gap-4 py-4">
                  <div className="shrink-0">
                    <StatusIcon className={`h-5 w-5 ${STATUS_COLORS[task.status]}`} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className={`text-sm font-medium truncate ${task.status === "completed" ? "line-through text-muted-foreground" : "text-white"}`}>
                        {task.title}
                      </p>
                      <Badge variant={task.priority === "critical" ? "destructive" : task.priority === "high" ? "warning" : task.priority === "medium" ? "default" : "secondary"} className="text-[10px]">
                        {task.priority}
                      </Badge>
                      <Badge variant={task.status === "completed" ? "success" : task.status === "failed" ? "destructive" : task.status === "in_progress" ? "default" : "secondary"} className="text-[10px]">
                        {task.status.replace("_", " ")}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      {task.description && (
                        <p className="text-xs text-muted-foreground truncate">{task.description}</p>
                      )}
                      {agent && (
                        <span className="text-xs text-accent-400">{agent.name}</span>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {new Date(task.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-1 shrink-0">
                    {task.status === "pending" && task.assigned_agent && (
                      <Button variant="ghost" size="sm" onClick={() => update(task.id, { status: "in_progress" })}>
                        <Play className="h-3 w-3" />
                      </Button>
                    )}
                    {task.status === "in_progress" && (
                      <Button variant="ghost" size="sm" onClick={() => update(task.id, { status: "completed" })}>
                        <CheckCircle className="h-3 w-3" />
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" onClick={() => openEdit(task)}>
                      <Pencil className="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => remove(task.id)}>
                      <Trash2 className="h-3 w-3 text-red-400" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog open={editTask !== null} onOpenChange={(v) => { if (!v) setEditTask(null) }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Task</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleEdit} className="space-y-4">
            <div className="space-y-2">
              <Label>Title</Label>
              <Input value={editForm.title} onChange={(e) => setEditForm({ ...editForm, title: e.target.value })} required />
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea value={editForm.description} onChange={(e) => setEditForm({ ...editForm, description: e.target.value })} />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Status</Label>
                <Select value={editForm.status} onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}>
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                  <option value="cancelled">Cancelled</option>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Priority</Label>
                <Select value={editForm.priority} onChange={(e) => setEditForm({ ...editForm, priority: e.target.value })}>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Assign Agent</Label>
                <Select value={editForm.assigned_agent} onChange={(e) => setEditForm({ ...editForm, assigned_agent: e.target.value })}>
                  <option value="">Unassigned</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>{a.name}</option>
                  ))}
                </Select>
              </div>
            </div>
            <Button type="submit">Save</Button>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
