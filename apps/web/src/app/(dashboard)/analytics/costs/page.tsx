"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { DollarSign, BarChart3 } from "lucide-react"

const COST_ESTIMATES = {
  openai: { input: 0.0000025, output: 0.00001 },
  anthropic: { input: 0.000003, output: 0.000015 },
  gemini: { input: 0.00000125, output: 0.000005 },
  deepseek: { input: 0.0000005, output: 0.000002 },
  grok: { input: 0.000002, output: 0.00001 },
  openrouter: { input: 0.000002, output: 0.000008 },
  ollama: { input: 0, output: 0 },
  nim: { input: 0.000001, output: 0.000004 },
}

export default function CostAnalyticsPage() {
  const { token } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    if (!token) { router.push("/login"); return }
  }, [token])

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Cost Analytics</h1>
          <p className="text-muted-foreground mt-1">Provider cost estimates and usage projections</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Daily Est.</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-white">—</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Weekly Est.</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-white">—</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Monthly Est.</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-white">—</p></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-xs text-muted-foreground">Avg. Cost/1K Tokens</CardTitle></CardHeader><CardContent><p className="text-2xl font-bold text-white">$0.003</p></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle className="text-sm">Provider Rate Cards</CardTitle></CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {Object.entries(COST_ESTIMATES).map(([name, rates]) => (
              <div key={name} className="p-3 rounded-lg bg-base-900/50 border border-border">
                <p className="text-sm font-medium text-white capitalize mb-2">{name}</p>
                <div className="space-y-1 text-xs text-muted-foreground">
                  <div className="flex justify-between"><span>Input/1K tokens</span><span className="text-white">${(rates.input * 1000).toFixed(5)}</span></div>
                  <div className="flex justify-between"><span>Output/1K tokens</span><span className="text-white">${(rates.output * 1000).toFixed(5)}</span></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
