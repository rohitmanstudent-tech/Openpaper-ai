"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import {
  ReactFlow, Background, Controls, MiniMap, BackgroundVariant,
  type Node, type Edge, useNodesState, useEdgesState, ReactFlowProvider,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { useAuthStore } from "@/stores/auth"
import { useAgentGraphStore } from "@/stores/agent-graph"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Brain, Activity, Radio, MessageSquare, GitBranch } from "lucide-react"
import Link from "next/link"

const AGENT_COLORS: Record<string, string> = {
  ceo: "bg-accent-500/10 border-accent-500/30 text-accent-400",
  research: "bg-cyan-500/10 border-cyan-500/30 text-cyan-400",
  buyer_finder: "bg-amber-500/10 border-amber-500/30 text-amber-400",
  sales: "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
}

const STATUS_COLORS: Record<string, string> = {
  idle: "bg-emerald-500",
  working: "bg-amber-500",
  error: "bg-red-500",
  paused: "bg-muted-foreground",
}

export default function AgentGraphPage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const { agents, edges, events, memoryCount, loading, fetchGraph, fetchEvents, fetchMemoryLinks } = useAgentGraphStore()
  const [graphNodes, setGraphNodes, onNodesChange] = useNodesState<Node>([])
  const [graphEdges, setGraphEdges, onEdgesChange] = useEdgesState<Edge>([])

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetchGraph()
    fetchEvents()
    fetchMemoryLinks()
  }, [token])

  useEffect(() => {
    if (agents.length === 0) return
    const flowNodes: Node[] = agents.map((a, i) => ({
      id: a.id,
      type: "default",
      position: { x: 250, y: i * 160 + 50 },
      data: {
        label: (
          <div className={`px-4 py-3 rounded-xl border-2 min-w-[180px] ${AGENT_COLORS[a.agent_type || ""] || "border-border bg-base-900"}`}>
            <div className="flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${STATUS_COLORS[a.status || ""] || "bg-muted-foreground"}`} />
              <span className="text-sm font-medium">{a.label}</span>
            </div>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant="secondary" className="text-[10px]">{a.agent_type}</Badge>
              <span className="text-[10px] text-muted-foreground capitalize">{a.status}</span>
            </div>
          </div>
        ),
      },
      style: { background: "transparent", border: "none", padding: 0 },
    }))
    setGraphNodes(flowNodes)
  }, [agents])

  useEffect(() => {
    if (edges.length === 0) return
    const flowEdges: Edge[] = edges.map((e, i) => ({
      id: `e_${i}`,
      source: e.source.startsWith("agent_") ? `agent_${e.source.replace("agent_", "")}` : e.source,
      target: e.target.startsWith("agent_") ? `agent_${e.target.replace("agent_", "")}` : e.target,
      animated: true,
      label: e.event_type?.replace("_", " ") || "",
      style: { stroke: "#6366f1", strokeWidth: 2 },
      labelStyle: { fill: "#9ca3af", fontSize: 10 },
    }))
    setGraphEdges(flowEdges)
  }, [edges])

  const recentEvents = events.slice(0, 10)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Agent Graph</h1>
          <p className="text-muted-foreground mt-1">Real-time agent network visualization</p>
        </div>
        <div className="flex items-center gap-2">
          <Link href="/agent-graph/live">
            <Badge variant="default" className="flex items-center gap-1 cursor-pointer">
              <Radio className="h-3 w-3" /> Live View
            </Badge>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Agents</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-white">{agents.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Connections</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-white">{edges.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Events</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-white">{events.length}</p></CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Memories</CardTitle></CardHeader>
          <CardContent><p className="text-2xl font-bold text-white">{memoryCount}</p></CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 h-[500px] rounded-xl border border-border overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full"><Loader2 className="h-6 w-6 text-accent-400 animate-spin" /></div>
          ) : (
            <ReactFlowProvider>
              <ReactFlow
                nodes={graphNodes}
                edges={graphEdges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                fitView
                className="bg-base-900/50"
              >
                <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1f2937" />
                <Controls className="bg-base-950 border border-border" />
                <MiniMap nodeStrokeColor="#6366f1" nodeColor="#1e293b" maskColor="rgba(0,0,0,0.7)" />
              </ReactFlow>
            </ReactFlowProvider>
          )}
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><Activity className="h-4 w-4" /> Recent Events</CardTitle></CardHeader>
            <CardContent className="max-h-[300px] overflow-y-auto space-y-2">
              {recentEvents.length === 0 ? (
                <p className="text-xs text-muted-foreground">No events yet</p>
              ) : recentEvents.map((ev, i) => (
                <div key={ev.event_id || i} className="text-xs p-2 rounded bg-base-900/50 space-y-0.5">
                  <div className="flex items-center gap-1">
                    <Badge variant="secondary" className="text-[9px]">{ev.event_type}</Badge>
                    {ev.source_agent && <span className="text-muted-foreground">{ev.source_agent} → {ev.target_agent || "—"}</span>}
                  </div>
                  {ev.timestamp && <p className="text-muted-foreground">{new Date(ev.timestamp).toLocaleTimeString()}</p>}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm flex items-center gap-2"><Brain className="h-4 w-4" /> Memory Links</CardTitle></CardHeader>
            <CardContent>
              <p className="text-2xl font-bold text-accent-400">{memoryCount}</p>
              <p className="text-xs text-muted-foreground">total memories stored</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
