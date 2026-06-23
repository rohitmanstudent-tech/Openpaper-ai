"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useWorkflowStore, type WorkflowRun, type WorkflowLog } from "@/stores/workflows"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { History, Play, XCircle, Loader2, ChevronDown, ChevronUp } from "lucide-react"

export default function WorkflowRunsPage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const { runs, loading, fetchRuns, getRun, cancelRun } = useWorkflowStore()
  const [selectedRun, setSelectedRun] = useState<WorkflowRun | null>(null)
  const [expanded, setExpanded] = useState<Record<number, boolean>>({})

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetchRuns()
  }, [token])

  const handleViewLogs = async (run: WorkflowRun) => {
    const full = await getRun(run.id)
    setSelectedRun(full)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "success"
      case "running": return "default"
      case "failed": return "destructive"
      case "cancelled": return "warning"
      case "pending": return "secondary"
      default: return "secondary"
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Workflow Runs</h1>
          <p className="text-muted-foreground mt-1">History and logs of workflow executions</p>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-6 w-6 text-accent-400 animate-spin" />
        </div>
      ) : runs.length === 0 ? (
        <Card className="bg-base-900/50">
          <CardContent className="p-8 text-center">
            <History className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
            <p className="text-muted-foreground">No workflow runs yet. Execute a workflow to see results.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {runs.map((run) => (
            <Card key={run.id} className="bg-base-950 border-border">
              <CardHeader className="p-4 pb-2 flex flex-row items-center justify-between">
                <div className="flex items-center gap-3">
                  <Badge variant={getStatusColor(run.status)} className="capitalize">{run.status}</Badge>
                  <CardTitle className="text-sm font-medium text-white">
                    Workflow #{run.workflow_id} · Run #{run.id}
                  </CardTitle>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => handleViewLogs(run)}>
                    View Logs
                  </Button>
                  {run.status === "running" && (
                    <Button variant="ghost" size="sm" onClick={() => cancelRun(run.id)}>
                      <XCircle className="h-4 w-4 text-red-400" />
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="p-4 pt-1">
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span>Trigger: {run.trigger}</span>
                  <span>·</span>
                  <span>{run.logs?.length || 0} node(s)</span>
                  <span>·</span>
                  <span>Started: {run.started_at ? new Date(run.started_at).toLocaleString() : "—"}</span>
                  {run.completed_at && (
                    <>
                      <span>·</span>
                      <span>Completed: {new Date(run.completed_at).toLocaleString()}</span>
                    </>
                  )}
                </div>
                {run.error && (
                  <p className="text-xs text-red-400 mt-2">Error: {run.error}</p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={!!selectedRun} onOpenChange={(o) => { if (!o) setSelectedRun(null) }}>
        <DialogContent className="max-w-3xl max-h-[80vh]">
          <DialogHeader>
            <DialogTitle>Run Logs — Workflow #{selectedRun?.workflow_id}</DialogTitle>
          </DialogHeader>
          {selectedRun && (
            <ScrollArea className="h-[60vh]">
              <div className="space-y-3">
                {(selectedRun.logs || []).map((log, i) => (
                  <Card key={i} className="bg-base-900/50">
                    <CardHeader
                      className="p-3 flex flex-row items-center justify-between cursor-pointer"
                      onClick={() => setExpanded((p) => ({ ...p, [i]: !p[i] }))}
                    >
                      <div className="flex items-center gap-2">
                        <Badge variant={log.status === "completed" ? "success" : log.status === "failed" ? "destructive" : "secondary"}>
                          {log.status}
                        </Badge>
                        <CardTitle className="text-xs font-medium text-muted-foreground">
                          {log.node_type} ({log.node_id?.slice(0, 8)})
                        </CardTitle>
                      </div>
                      {expanded[i] ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                    </CardHeader>
                    {expanded[i] && (
                      <CardContent className="p-3 pt-0">
                        <pre className="text-xs text-foreground whitespace-pre-wrap font-mono bg-base-950 p-2 rounded">
                          {JSON.stringify(log.result || log.error || log, null, 2)}
                        </pre>
                      </CardContent>
                    )}
                  </Card>
                ))}
              </div>
            </ScrollArea>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
