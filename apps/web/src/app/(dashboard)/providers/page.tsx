"use client"

import { useEffect } from "react"
import { useProviderStore } from "@/stores/providers"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Cpu, CheckCircle, XCircle, Clock } from "lucide-react"

const PROVIDER_ICONS: Record<string, string> = {
  ollama: "Ollama",
  openai: "OpenAI",
  claude: "Claude",
  openrouter: "OpenRouter",
}

export default function ProvidersPage() {
  const { providers, loading, fetch } = useProviderStore()

  useEffect(() => { fetch() }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Providers</h1>
        <p className="text-muted-foreground text-sm mt-1">Configure and monitor AI model providers</p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}><CardContent className="h-24 animate-pulse bg-base-800/50 rounded-xl" /></Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {providers.map((p) => (
            <Card key={p.name}>
              <CardHeader className="flex flex-row items-center gap-3">
                <div className="h-10 w-10 rounded-lg bg-white/5 flex items-center justify-center">
                  <Cpu className="h-5 w-5 text-accent-400" />
                </div>
                <div>
                  <CardTitle className="text-base capitalize">{p.name}</CardTitle>
                  <p className="text-xs text-muted-foreground">{p.model_count} models</p>
                </div>
                <div className="ml-auto">
                  {p.status === "available" ? (
                    <CheckCircle className="h-5 w-5 text-emerald-400" />
                  ) : p.status === "error" ? (
                    <XCircle className="h-5 w-5 text-red-400" />
                  ) : (
                    <Clock className="h-5 w-5 text-amber-400" />
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Default model</span>
                  <span className="text-white font-mono text-xs">{p.default_model}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
