"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useAnalyticsStore } from "@/stores/analytics"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, GitBranch, CheckCircle, XCircle, Clock } from "lucide-react"

export default function WorkflowAnalyticsPage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const { workflows, loading, fetchWorkflows } = useAnalyticsStore()

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetchWorkflows()
  }, [token])

  const totalRuns = workflows.reduce((s, w) => s + w.total_runs, 0)
  const successRuns = workflows.reduce((s, w) => s + w.successful_runs, 0)
  const failedRuns = workflows.reduce((s, w) => s + w.failed_runs, 0)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Workflow Analytics</h1>
          <p className="text-muted-foreground mt-1">Workflow execution performance</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Total Runs</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-white">{totalRuns}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Successful</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-emerald-400">{successRuns}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Failed</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-red-400">{failedRuns}</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Success Rate</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-white">{totalRuns > 0 ? `${((successRuns / totalRuns) * 100).toFixed(1)}%` : "—"}</p></CardContent></Card>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12"><Loader2 className="h-6 w-6 text-accent-400 animate-spin" /></div>
      ) : workflows.length === 0 ? (
        <Card className="bg-base-900/50"><CardContent className="p-8 text-center"><GitBranch className="h-8 w-8 text-muted-foreground mx-auto mb-3" /><p className="text-muted-foreground">No workflow data yet.</p></CardContent></Card>
      ) : (
        <div className="space-y-3">
          {workflows.map((w) => (
            <Card key={w.id} className="bg-base-950 border-border">
              <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between">
                <div className="flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-accent-400" />
                  <CardTitle className="text-sm font-medium text-white">{w.name}</CardTitle>
                  <Badge variant={w.status === "active" ? "success" : "secondary"}>{w.status}</Badge>
                </div>
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div><span className="text-muted-foreground">Runs:</span> <span className="text-white font-medium">{w.total_runs}</span></div>
                  <div><span className="text-muted-foreground">Success:</span> <span className="text-emerald-400 font-medium">{w.successful_runs}</span></div>
                  <div><span className="text-muted-foreground">Failed:</span> <span className="text-red-400 font-medium">{w.failed_runs}</span></div>
                  <div><span className="text-muted-foreground">Avg:</span> <span className="text-white font-medium">{w.avg_duration}s</span></div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
