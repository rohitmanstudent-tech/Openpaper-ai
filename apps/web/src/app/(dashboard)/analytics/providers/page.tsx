"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { useAnalyticsStore } from "@/stores/analytics"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Cpu } from "lucide-react"

const PROVIDER_COLORS: Record<string, string> = {
  openai: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  anthropic: "bg-purple-500/10 text-purple-400 border-purple-500/20",
  gemini: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  deepseek: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  grok: "bg-rose-500/10 text-rose-400 border-rose-500/20",
  openrouter: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  ollama: "bg-accent-500/10 text-accent-400 border-accent-500/20",
  nim: "bg-violet-500/10 text-violet-400 border-violet-500/20",
}

export default function ProviderAnalyticsPage() {
  const { token } = useAuthStore()
  const router = useRouter()
  const { providers, loading, fetchProviders } = useAnalyticsStore()

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetchProviders()
  }, [token])

  const available = Object.values(providers).filter((p) => p.status === "available").length

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Provider Analytics</h1>
          <p className="text-muted-foreground mt-1">AI provider health and model availability</p>
        </div>
        <Badge variant={available > 0 ? "success" : "destructive"}>{available} available</Badge>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-12"><Loader2 className="h-6 w-6 text-accent-400 animate-spin" /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(providers).map(([name, p]) => (
            <Card key={name} className={`${PROVIDER_COLORS[name] || "bg-base-900 border-border"} h-full`}>
              <CardHeader className="pb-2 flex flex-row items-center justify-between">
                <CardTitle className="text-sm font-medium capitalize">{name}</CardTitle>
                <Cpu className="h-4 w-4" />
              </CardHeader>
              <CardContent>
                <Badge variant={p.status === "available" ? "success" : "secondary"} className="mb-2">{p.status}</Badge>
                <p className="text-xs text-muted-foreground">{p.models_count} models</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
