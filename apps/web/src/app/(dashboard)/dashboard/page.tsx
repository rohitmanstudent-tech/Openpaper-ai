"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useAgentStore } from "@/stores/agents"
import { useChatStore } from "@/stores/chat"
import { useTaskStore } from "@/stores/tasks"
import { useDashboardStore } from "@/stores/dashboard"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Bot, MessageSquare, Cpu, CheckSquare, Activity, Wifi, WifiOff } from "lucide-react"

export default function DashboardPage() {
  const { user, token } = useAuthStore()
  const { agents, fetch: fetchAgents } = useAgentStore()
  const { chats, fetchChats } = useChatStore()
  const { tasks, fetch: fetchTasks } = useTaskStore()
  const { systemHealth, providerCount, modelCount, fetchHealth, fetchCounts } = useDashboardStore()
  const router = useRouter()
  const [mounted, setMounted] = useState(false)

  const load = useCallback(() => {
    if (!token) { router.push("/login"); return }
    fetchAgents()
    fetchChats()
    fetchTasks()
    fetchHealth()
    fetchCounts()
  }, [token])

  useEffect(() => { setMounted(true); load() }, [load])

  useEffect(() => {
    if (!mounted) return
    const interval = setInterval(() => {
      fetchHealth()
      fetchAgents()
      fetchTasks()
    }, 15000)
    return () => clearInterval(interval)
  }, [mounted])

  const activeTasks = tasks.filter((t) => t.status !== "completed").length
  const systemOk = systemHealth?.status === "healthy"

  const stats = [
    { label: "Agents", value: agents.length, icon: Bot, color: "text-accent-400" },
    { label: "Chats", value: chats.length, icon: MessageSquare, color: "text-emerald-400" },
    { label: "Active Tasks", value: activeTasks, icon: CheckSquare, color: "text-amber-400" },
    { label: "Models", value: modelCount, icon: Cpu, color: "text-purple-400" },
    { label: "Providers", value: providerCount, icon: Activity, color: "text-cyan-400" },
  ]

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Welcome back, {user?.username || "user"}</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">System</span>
          {systemOk ? (
            <Badge variant="success" className="flex items-center gap-1">
              <Wifi className="h-3 w-3" /> Healthy
            </Badge>
          ) : (
            <Badge variant="destructive" className="flex items-center gap-1">
              <WifiOff className="h-3 w-3" /> Degraded
            </Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{stat.label}</CardTitle>
              <stat.icon className={`h-5 w-5 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-white">{stat.value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Agents</CardTitle>
          </CardHeader>
          <CardContent>
            {agents.length === 0 ? (
              <p className="text-sm text-muted-foreground">No agents yet. Create one to get started.</p>
            ) : (
              <div className="space-y-3">
                {agents.slice(0, 5).map((agent) => (
                  <div key={agent.id} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                    <div>
                      <p className="text-sm font-medium text-white">{agent.name}</p>
                      <p className="text-xs text-muted-foreground">{agent.provider}/{agent.model}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      agent.status === "idle" ? "bg-emerald-500/10 text-emerald-400" :
                      agent.status === "working" ? "bg-accent-500/10 text-accent-400" :
                      "bg-amber-500/10 text-amber-400"
                    }`}>
                      {agent.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Recent Chats</CardTitle>
          </CardHeader>
          <CardContent>
            {chats.length === 0 ? (
              <p className="text-sm text-muted-foreground">No chats yet. Start a conversation.</p>
            ) : (
              <div className="space-y-3">
                {chats.slice(0, 5).map((chat) => (
                  <div key={chat.id} className="p-3 rounded-lg bg-white/5">
                    <p className="text-sm font-medium text-white">{chat.title || "Untitled"}</p>
                    <p className="text-xs text-muted-foreground">{new Date(chat.created_at).toLocaleDateString()}</p>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Active Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            {activeTasks === 0 ? (
              <p className="text-sm text-muted-foreground">No active tasks.</p>
            ) : (
              <div className="space-y-3">
                {tasks.filter((t) => t.status !== "completed").slice(0, 5).map((task) => (
                  <div key={task.id} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                    <div>
                      <p className="text-sm font-medium text-white">{task.title}</p>
                      <p className="text-xs text-muted-foreground capitalize">{task.status} · {task.priority}</p>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      task.status === "in_progress" ? "bg-accent-500/10 text-accent-400" :
                      task.status === "pending" ? "bg-amber-500/10 text-amber-400" :
                      "bg-emerald-500/10 text-emerald-400"
                    }`}>{task.status}</span>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Agent Types</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { type: "ceo", label: "CEO", desc: "Strategic leadership & delegation", count: agents.filter(a => a.agent_type === "ceo").length },
                { type: "sales", label: "Sales", desc: "Lead generation & proposals", count: agents.filter(a => a.agent_type === "sales").length },
                { type: "research", label: "Research", desc: "Market research & analysis", count: agents.filter(a => a.agent_type === "research").length },
                { type: "buyer_finder", label: "Buyer Finder", desc: "Export lead qualification", count: agents.filter(a => a.agent_type === "buyer_finder").length },
              ].map((item) => (
                <div key={item.type} className="flex items-center justify-between p-3 rounded-lg bg-white/5">
                  <div>
                    <p className="text-sm font-medium text-white capitalize">{item.label}</p>
                    <p className="text-xs text-muted-foreground">{item.desc}</p>
                  </div>
                  <span className="text-sm text-muted-foreground">{item.count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {systemHealth && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">System Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {systemHealth.checks && Object.entries(systemHealth.checks).map(([key, val]) => (
                <div key={key} className="flex items-center gap-2 p-3 rounded-lg bg-white/5">
                  {val.status === "healthy" || val.status === "available" ? (
                    <Wifi className="h-4 w-4 text-emerald-400" />
                  ) : (
                    <WifiOff className="h-4 w-4 text-red-400" />
                  )}
                  <div>
                    <p className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                    <p className="text-sm text-white">{val.status}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
