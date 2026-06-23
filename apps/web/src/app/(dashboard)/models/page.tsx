"use client"

import { useEffect, useState } from "react"
import { useModelsStore } from "@/stores/models"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Cpu, Search, CheckCircle, XCircle, BarChart3 } from "lucide-react"

export default function ModelsPage() {
  const { modelsByProvider, providers, loading, fetch } = useModelsStore()
  const [search, setSearch] = useState("")

  useEffect(() => { fetch() }, [])

  const allModels = Object.entries(modelsByProvider).flatMap(([provider, models]) =>
    models.map((model) => ({ provider, model }))
  )
  const filtered = search
    ? allModels.filter((m) => m.model.toLowerCase().includes(search.toLowerCase()) || m.provider.toLowerCase().includes(search.toLowerCase()))
    : allModels

  const providerStatusMap = Object.fromEntries(
    providers.map((p) => [p.name, p.status])
  )

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Models</h1>
        <p className="text-muted-foreground text-sm mt-1">Browse available models across all providers</p>
      </div>

      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Models</CardTitle>
            <BarChart3 className="h-5 w-5 text-accent-400" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-white">{allModels.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Providers</CardTitle>
            <Cpu className="h-5 w-5 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-white">{providers.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Available Providers</CardTitle>
            <CheckCircle className="h-5 w-5 text-emerald-400" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-white">{providers.filter((p) => p.status === "available").length}</p>
          </CardContent>
        </Card>
      </div>

      {/* Provider Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {providers.map((p) => (
          <Card key={p.name}>
            <CardHeader className="flex flex-row items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-white/5 flex items-center justify-center">
                <Cpu className="h-5 w-5 text-accent-400" />
              </div>
              <div className="flex-1">
                <CardTitle className="text-base capitalize">{p.name}</CardTitle>
                <p className="text-xs text-muted-foreground">{p.model_count} models</p>
              </div>
              {p.status === "available" ? (
                <CheckCircle className="h-5 w-5 text-emerald-400" />
              ) : (
                <XCircle className="h-5 w-5 text-red-400" />
              )}
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Default</span>
                <span className="text-white font-mono text-xs">{p.default_model}</span>
              </div>
              {modelsByProvider[p.name] && (
                <div className="mt-3 flex flex-wrap gap-1">
                  {modelsByProvider[p.name].slice(0, 6).map((m) => (
                    <Badge key={m} variant="secondary" className="text-xs">{m}</Badge>
                  ))}
                  {modelsByProvider[p.name].length > 6 && (
                    <Badge variant="outline" className="text-xs">+{modelsByProvider[p.name].length - 6}</Badge>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Full Model List */}
      <Card>
        <CardHeader>
          <CardTitle>All Models</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative mb-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              className="pl-10"
              placeholder="Search models..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          {loading ? (
            <div className="space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-10 animate-pulse bg-base-800/50 rounded-lg" />
              ))}
            </div>
          ) : (
            <div className="max-h-96 overflow-y-auto space-y-1">
              {filtered.map((m, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded-lg hover:bg-white/5">
                  <div className="flex items-center gap-3">
                    <Badge variant="secondary" className="w-20 justify-center">{m.provider}</Badge>
                    <span className="text-sm text-foreground font-mono">{m.model}</span>
                  </div>
                  <span className={`text-xs ${providerStatusMap[m.provider] === "available" ? "text-emerald-400" : "text-red-400"}`}>
                    {providerStatusMap[m.provider] === "available" ? "Available" : "Unavailable"}
                  </span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
