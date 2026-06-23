"use client"

import { useEffect, useState, useRef } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Radio, Activity, Wifi, WifiOff, Loader2, MessageSquare, GitBranch, CheckCircle, XCircle } from "lucide-react"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

interface LiveEvent {
  event_id: string
  event_type: string
  source_agent?: string
  target_agent?: string
  correlation_id?: string
  timestamp?: string
  data?: Record<string, unknown>
}

export default function LiveAgentGraphPage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const [events, setEvents] = useState<LiveEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [statusCounts, setStatusCounts] = useState<Record<string, number>>({})
  const eventsRef = useRef<LiveEvent[]>([])
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined)

  const getEventIcon = (type: string) => {
    switch (type) {
      case "message_sent":
      case "message_received": return <MessageSquare className="h-3 w-3 text-accent-400" />
      case "task_completed": return <CheckCircle className="h-3 w-3 text-emerald-400" />
      case "task_failed": return <XCircle className="h-3 w-3 text-red-400" />
      case "task_assigned": return <GitBranch className="h-3 w-3 text-amber-400" />
      default: return <Activity className="h-3 w-3 text-muted-foreground" />
    }
  }

  useEffect(() => {
    if (!token) { router.push("/login"); return }

    const fetchEvents = async () => {
      try {
        const res = await fetch(`${API_BASE}/agent-graph/events?limit=50`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        const data = await res.json()
        if (data.events) {
          const newEvents = data.events as LiveEvent[]
          eventsRef.current = newEvents
          setEvents(newEvents)
          setConnected(true)

          const counts: Record<string, number> = {}
          for (const ev of newEvents) {
            counts[ev.event_type] = (counts[ev.event_type] || 0) + 1
          }
          setStatusCounts(counts)
        }
      } catch {
        setConnected(false)
      }
    }

    fetchEvents()
    intervalRef.current = setInterval(fetchEvents, 3000)

    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [token])

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold text-white">Live Agent Graph</h1>
            <p className="text-muted-foreground mt-1">Real-time event stream</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Status</span>
          {connected ? (
            <Badge variant="success" className="flex items-center gap-1"><Wifi className="h-3 w-3" /> Live</Badge>
          ) : (
            <Badge variant="destructive" className="flex items-center gap-1"><WifiOff className="h-3 w-3" /> Disconnected</Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {Object.entries(statusCounts).slice(0, 12).map(([type, count]) => (
          <Card key={type}>
            <CardHeader className="pb-1"><CardTitle className="text-[10px] text-muted-foreground uppercase truncate">{type.replace(/_/g, " ")}</CardTitle></CardHeader>
            <CardContent><p className="text-lg font-bold text-white">{count}</p></CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Radio className="h-4 w-4 text-accent-400" />
            Event Stream
            {connected && <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            {events.length === 0 ? (
              <div className="flex items-center justify-center p-8"><Loader2 className="h-5 w-5 text-accent-400 animate-spin" /></div>
            ) : (
              <div className="space-y-1">
                {events.map((ev, i) => (
                  <div key={ev.event_id || i} className="flex items-center gap-3 p-2 rounded hover:bg-base-900/50 text-xs transition-colors">
                    <span className="text-muted-foreground w-16 shrink-0 font-mono">
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : "—"}
                    </span>
                    {getEventIcon(ev.event_type)}
                    <Badge variant="secondary" className="text-[9px] shrink-0">{ev.event_type}</Badge>
                    {ev.source_agent && (
                      <span className="text-foreground font-medium">{ev.source_agent}</span>
                    )}
                    {ev.target_agent && (
                      <>
                        <span className="text-muted-foreground">→</span>
                        <span className="text-foreground font-medium">{ev.target_agent}</span>
                      </>
                    )}
                    {ev.correlation_id && (
                      <span className="text-muted-foreground font-mono text-[9px] ml-auto">
                        {ev.correlation_id.slice(0, 8)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
