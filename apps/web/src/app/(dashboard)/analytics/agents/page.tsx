"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useAnalyticsStore } from "@/stores/analytics"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Brain, MessageSquare, GitBranch, Activity } from "lucide-react"

const AGENT_TYPE_COLORS: Record<string, string> = {
  ceo: "text-accent-400 bg-accent-500/10",
  research: "text-cyan-400 bg-cyan-500/10",
  buyer_finder: "text-amber-400 bg-amber-500/10",
  sales: "text-emerald-400 bg-emerald-500/10",
}

export default function AgentAnalyticsPage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const { agents, loading, fetchAgents } = useAnalyticsStore()

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetchAgents()
  }, [token])

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Agent Analytics</h1>
          <p className="text-muted-foreground mt-1">Agent performance and activity metrics</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12"><Loader2 className="h-6 w-6 text-accent-400 animate-spin" /></div>
      ) : Object.keys(agents).length === 0 ? (
        <Card className="bg-base-900/50"><CardContent className="p-8 text-center"><Brain className="h-8 w-8 text-muted-foreground mx-auto mb-3" /><p className="text-muted-foreground">No agents found.</p></CardContent></Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.values(agents).map((a) => (
            <Card key={a.id} className="bg-base-950 border-border">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="h-4 w-4 text-accent-400" />
                  <CardTitle className="text-sm font-medium text-white">{a.name}</CardTitle>
                  <Badge className={`text-[10px] capitalize ${AGENT_TYPE_COLORS[a.agent_type] || "text-muted-foreground"}`}>{a.agent_type}</Badge>
                </div>
                <Badge variant={a.status === "idle" ? "success" : a.status === "working" ? "default" : "secondary"} className="capitalize">{a.status}</Badge>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div><p className="text-[10px] text-muted-foreground">Tasks Done</p><p className="text-sm font-bold text-white">{a.tasks_completed}</p></div>
                  <div><p className="text-[10px] text-muted-foreground">Failed</p><p className="text-sm font-bold text-red-400">{a.tasks_failed}</p></div>
                  <div><p className="text-[10px] text-muted-foreground">Delegations</p><p className="text-sm font-bold text-amber-400">{a.delegation_count}</p></div>
                  <div><p className="text-[10px] text-muted-foreground">Messages</p><p className="text-sm font-bold text-cyan-400">{a.message_count}</p></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
