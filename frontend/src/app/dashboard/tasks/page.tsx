"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { api, getToken } from "@/lib/api";
import { CheckSquare, Plus, Circle, CheckCircle, Clock, AlertCircle, Filter, ArrowUpDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface TaskItem {
  id: number; title: string; description: string | null;
  status: string; priority: string; created_at: string;
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [filter, setFilter] = useState<string>("all");
  const [newTask, setNewTask] = useState({ title: "", description: "", priority: "medium" });
  const token = getToken();

  const fetchTasks = async () => {
    if (!token) return;
    try { const data = await api.get<TaskItem[]>("/tasks", token); setTasks(data); }
    catch {} finally { setLoading(false); }
  };

  useEffect(() => { fetchTasks(); }, []);

  const handleCreate = async () => {
    if (!token || !newTask.title.trim()) return;
    try {
      await api.post("/tasks", newTask, token);
      setShowCreate(false);
      setNewTask({ title: "", description: "", priority: "medium" });
      fetchTasks();
    } catch {}
  };

  const handleStatusUpdate = async (task: TaskItem, newStatus: string) => {
    if (!token) return;
    try { await api.put(`/tasks/${task.id}`, { status: newStatus }, token); fetchTasks(); }
    catch {}
  };

  const filtered = filter === "all" ? tasks : tasks.filter(t => t.status === filter);

  const counts = {
    all: tasks.length,
    pending: tasks.filter(t => t.status === "pending").length,
    in_progress: tasks.filter(t => t.status === "in_progress").length,
    completed: tasks.filter(t => t.status === "completed").length,
  };

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return <CheckCircle size={16} className="text-emerald-400" />;
      case "in_progress": return <Clock size={16} className="text-accent-400" />;
      case "failed": return <AlertCircle size={16} className="text-red-400" />;
      default: return <Circle size={16} className="text-base-500" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="h-5 w-5 animate-spin rounded-full border border-accent-500 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-base-100">Tasks</h1>
          <p className="mt-0.5 text-sm text-base-400">Manage your team's tasks and track progress</p>
        </div>
        <Button onClick={() => setShowCreate(true)}><Plus size={15} className="mr-1.5" />New Task</Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-1 rounded-md border border-base-700/50 p-0.5 w-fit">
        {(["all", "pending", "in_progress", "completed"] as const).map((f) => (
          <button key={f} onClick={() => setFilter(f)}
            className={cn("rounded px-3 py-1 text-xs transition-colors flex items-center gap-1.5",
              filter === f ? "bg-base-700 text-base-200" : "text-base-500 hover:text-base-300")}>
            {f === "all" ? "All" : f.replace("_", " ")}
            <span className="text-[10px] text-base-600">({counts[f]})</span>
          </button>
        ))}
      </div>

      {/* List */}
      {filtered.length === 0 ? (
        <Card className="flex flex-col items-center justify-center py-16">
          <CheckSquare size={40} className="mb-3 text-base-600" />
          <p className="text-sm font-medium text-base-400">No tasks found</p>
          <p className="text-xs text-base-500">Create your first task to get started</p>
        </Card>
      ) : (
        <div className="space-y-1">
          {filtered.map((task) => (
            <div key={task.id} className="flex items-center gap-4 rounded-md px-3 py-2.5 transition-colors hover:bg-base-800/40">
              <button onClick={() => handleStatusUpdate(task, task.status === "completed" ? "pending" : "completed")}
                className="shrink-0">
                {statusIcon(task.status)}
              </button>
              <div className="flex-1 min-w-0">
                <p className={cn("text-sm", task.status === "completed" ? "text-base-500 line-through" : "text-base-200")}>
                  {task.title}
                </p>
                {task.description && (
                  <p className="text-xs text-base-500 mt-0.5">{task.description}</p>
                )}
              </div>
              <Badge variant={task.priority as any} className="shrink-0">{task.priority}</Badge>
              <Badge variant={task.status as any} className="shrink-0">{task.status.replace("_", " ")}</Badge>
              <span className="text-[11px] text-base-600 shrink-0">
                {new Date(task.created_at).toLocaleDateString()}
              </span>
            </div>
          ))}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Create New Task">
        <div className="space-y-4">
          <Input label="Title" value={newTask.title} onChange={(e) => setNewTask({ ...newTask, title: e.target.value })} placeholder="Task title" />
          <Input label="Description" value={newTask.description} onChange={(e) => setNewTask({ ...newTask, description: e.target.value })} placeholder="Optional description" />
          <div className="space-y-1">
            <label className="block text-xs font-medium text-base-400">Priority</label>
            <select value={newTask.priority} onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
              className="w-full rounded-md border border-base-700/50 bg-base-900 px-3 py-1.5 text-sm text-base-100 outline-none focus:border-accent-500/50">
              <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button onClick={handleCreate}>Create Task</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
