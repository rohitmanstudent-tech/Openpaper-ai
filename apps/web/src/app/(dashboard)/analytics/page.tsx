"use client"

import { useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useAnalyticsStore } from "@/stores/analytics"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Cpu, DollarSign, Activity, Database, FileText, GitBranch, Brain, Wifi, WifiOff } from "lucide-react"
import Link from "next/link"

export default function AnalyticsPage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const { providers, agents, workflows, memory, documents, system, loading, fetchAll } = useAnalyticsStore()

  const load = useCallback(() => {
    if (!token) { router.push("/login"); return }
    fetchAll()
  }, [token])

  useEffect(() => { load() }, [load])
  useEffect(() => {
    const interval = setInterval(() => fetchAll(), 15000)
    return () => clearInterval(interval)
  }, [])

  const totalRuns = workflows.reduce((s, w) => s + w.total_runs, 0)
  const successRuns = workflows.reduce((s, w) => s + w.successful_runs, 0)
  const agentCount = Object.keys(agents).length

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Analytics</h1>
          <p className="text-muted-foreground mt-1">Platform-wide metrics and insights</p>
        </div>
        {system && (
          <Badge variant={system.status === "healthy" ? "success" : "destructive"} className="flex items-center gap-1">
            {system.status === "healthy" ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
            {system.status}
          </Badge>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12"><Loader2 className="h-6 w-6 text-accent-400 animate-spin" /></div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <Link href="/analytics/providers"><Card className="hover:border-accent-500/30 transition-colors cursor-pointer h-full">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-xs text-muted-foreground">Providers</CardTitle>
                <Cpu className="h-4 w-4 text-accent-400" />
              </CardHeader>
              <CardContent><p className="text-2xl font-bold text-white">{Object.keys(providers).length}</p></CardContent>
            </Card></Link>
            <Link href="/analytics/agents"><Card className="hover:border-accent-500/30 transition-colors cursor-pointer h-full">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-xs text-muted-foreground">Agents</CardTitle>
                <Brain className="h-4 w-4 text-cyan-400" />
              </CardHeader>
              <CardContent><p className="text-2xl font-bold text-white">{agentCount}</p></CardContent>
            </Card></Link>
            <Link href="/analytics/workflows"><Card className="hover:border-accent-500/30 transition-colors cursor-pointer h-full">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-xs text-muted-foreground">Workflows</CardTitle>
                <GitBranch className="h-4 w-4 text-amber-400" />
              </CardHeader>
              <CardContent><p className="text-2xl font-bold text-white">{workflows.length}</p></CardContent>
            </Card></Link>
            <Link href="/analytics/costs"><Card className="hover:border-accent-500/30 transition-colors cursor-pointer h-full">
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-xs text-muted-foreground">Total Runs</CardTitle>
                <Activity className="h-4 w-4 text-emerald-400" />
              </CardHeader>
              <CardContent><p className="text-2xl font-bold text-white">{totalRuns}</p></CardContent>
            </Card></Link>
            <Card>
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-xs text-muted-foreground">Memory</CardTitle>
                <Database className="h-4 w-4 text-purple-400" />
              </CardHeader>
              <CardContent><p className="text-2xl font-bold text-white">{memory?.total ?? 0}</p></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-xs text-muted-foreground">Documents</CardTitle>
                <FileText className="h-4 w-4 text-rose-400" />
              </CardHeader>
              <CardContent><p className="text-2xl font-bold text-white">{documents?.total_documents ?? 0}</p></CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader><CardTitle className="text-sm">Provider Status</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(providers).map(([name, p]) => (
                    <div key={name} className="flex items-center justify-between p-2 rounded bg-base-900/50">
                      <span className="text-sm capitalize">{name}</span>
                      <Badge variant={p.status === "available" ? "success" : "secondary"} className="text-[10px]">{p.status}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-sm">Workflow Performance</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm"><span className="text-muted-foreground">Total Runs</span><span className="text-white font-medium">{totalRuns}</span></div>
                  <div className="flex justify-between text-sm"><span className="text-muted-foreground">Successful</span><span className="text-emerald-400 font-medium">{successRuns}</span></div>
                  <div className="flex justify-between text-sm"><span className="text-muted-foreground">Failed</span><span className="text-red-400 font-medium">{totalRuns - successRuns}</span></div>
                  <div className="flex justify-between text-sm"><span className="text-muted-foreground">Success Rate</span><span className="text-white font-medium">{totalRuns > 0 ? `${((successRuns / totalRuns) * 100).toFixed(1)}%` : "—"}</span></div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-sm">Memory Breakdown</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-2 rounded bg-base-900/50"><p className="text-xs text-muted-foreground">Short-term</p><p className="text-lg font-bold text-white">{memory?.short_term ?? 0}</p></div>
                  <div className="p-2 rounded bg-base-900/50"><p className="text-xs text-muted-foreground">Long-term</p><p className="text-lg font-bold text-white">{memory?.long_term ?? 0}</p></div>
                  <div className="p-2 rounded bg-base-900/50"><p className="text-xs text-muted-foreground">Shared</p><p className="text-lg font-bold text-white">{memory?.shared ?? 0}</p></div>
                  <div className="p-2 rounded bg-base-900/50"><p className="text-xs text-muted-foreground">Agent Personal</p><p className="text-lg font-bold text-white">{memory?.agent_personal ?? 0}</p></div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle className="text-sm">Documents & Chunks</CardTitle></CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm"><span className="text-muted-foreground">Documents</span><span className="text-white font-medium">{documents?.total_documents ?? 0}</span></div>
                  <div className="flex justify-between text-sm"><span className="text-muted-foreground">Chunks</span><span className="text-white font-medium">{documents?.total_chunks ?? 0}</span></div>
                  <div className="flex justify-between text-sm"><span className="text-muted-foreground">Searches</span><span className="text-white font-medium">{documents?.searches_performed ?? 0}</span></div>
                </div>
              </CardContent>
            </Card>
          </div>

          {system && (
            <Card>
              <CardHeader><CardTitle className="text-sm">System Health</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                  {Object.entries(system.checks || {}).map(([key, val]) => (
                    <div key={key} className="flex items-center gap-2 p-2 rounded bg-base-900/50">
                      {(val as { status: string }).status === "healthy" || (val as { status: string }).status === "available" ? (
                        <Wifi className="h-4 w-4 text-emerald-400" />
                      ) : (
                        <WifiOff className="h-4 w-4 text-red-400" />
                      )}
                      <div>
                        <p className="text-[10px] text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                        <p className="text-xs text-white">{(val as { status: string }).status}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
