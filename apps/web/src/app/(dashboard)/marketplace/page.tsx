"use client"

import { useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { useMarketplaceStore } from "@/stores/marketplace"
import { useAuthStore } from "@/stores/auth"
import { Store, Star, Download, Search, Loader2, ArrowRight, Bot, GitBranch, Wrench, Radio, RefreshCw, Globe } from "lucide-react"

const CATEGORY_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string }> = {
  agents: { label: "Agents", icon: Bot, color: "text-accent-400" },
  workflows: { label: "Workflows", icon: GitBranch, color: "text-emerald-400" },
  tools: { label: "Tools", icon: Wrench, color: "text-amber-400" },
  providers: { label: "Providers", icon: Radio, color: "text-purple-400" },
}

export default function MarketplacePage() {
  const router = useRouter()
  const { token } = useAuthStore()
  const { items, loading, searchQuery, setSearchQuery, fetchItems, fetchInstalled, syncWithHub, getSyncStatus } = useMarketplaceStore()

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetchItems({ featured: true })
    fetchInstalled()
  }, [])

  const featured = items.filter((i) => i.rating >= 4.5).slice(0, 6)

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
            <Store className="h-8 w-8 text-accent-400" /> Marketplace
          </h1>
          <p className="text-muted-foreground mt-1">Discover and install agents, workflows, tools, and providers</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={async () => { await syncWithHub(); await fetchItems({ featured: true }) }}>
            <RefreshCw className="h-4 w-4 mr-1" /> Sync with Hub
          </Button>
          <Button variant="ghost" size="sm" onClick={async () => {
            const status: any = await getSyncStatus()
            const syncs = status?.recent_syncs as any[] | undefined
            if (syncs && syncs.length > 0) {
              const last = syncs[0]
              alert(`Last sync: ${last.packages_synced} packages (${last.packages_added} new, ${last.packages_updated} updated)`)
            } else {
              alert('No sync history yet')
            }
          }}>
            <Globe className="h-4 w-4 mr-1" /> Hub Status
          </Button>
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search marketplace..."
          className="pl-10"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && searchQuery.trim()) {
              router.push(`/marketplace?search=${encodeURIComponent(searchQuery.trim())}`)
            }
          }}
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-accent-400" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(CATEGORY_CONFIG).map(([key, config]) => (
              <Link key={key} href={`/marketplace/${key}`}>
                <Card className="hover:bg-white/5 transition-colors cursor-pointer border-white/10">
                  <CardContent className="p-6 flex flex-col items-center text-center gap-3">
                    <config.icon className={`h-10 w-10 ${config.color}`} />
                    <div>
                      <p className="font-semibold text-white">{config.label}</p>
                      <p className="text-sm text-muted-foreground">
                        {items.filter((i) => i.item_type === key.slice(0, -1)).length} available
                      </p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                <Star className="h-5 w-5 text-amber-400" /> Featured
              </h2>
              <Link href="/marketplace?featured=true">
                <Button variant="outline" size="sm">
                  View All <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {featured.map((item) => {
                const catConfig = CATEGORY_CONFIG[`${item.item_type}s`]
                const CatIcon = catConfig?.icon || Store
                return (
                  <Link key={item.id} href={`/marketplace/${item.id}`}>
                    <Card className="hover:bg-white/5 transition-colors cursor-pointer border-white/10 h-full">
                      <CardHeader className="pb-3">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-2">
                            <CatIcon className={`h-5 w-5 ${catConfig?.color || "text-muted-foreground"}`} />
                            <CardTitle className="text-base text-white">{item.name}</CardTitle>
                          </div>
                          <Badge variant="secondary" className="text-xs">
                            v{item.version}
                          </Badge>
                        </div>
                        <CardDescription className="line-clamp-2">{item.description}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center gap-1"><Star className="h-3 w-3 text-amber-400" /> {item.rating}</span>
                          <span className="flex items-center gap-1"><Download className="h-3 w-3" /> {item.downloads}</span>
                          <span className="capitalize">{item.item_type}</span>
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                )
              })}
            </div>
          </div>

          <div className="flex items-center justify-center gap-4 pt-4">
            <Link href="/marketplace/agents"><Button variant="outline">Browse Agents</Button></Link>
            <Link href="/marketplace/workflows"><Button variant="outline">Browse Workflows</Button></Link>
            <Link href="/marketplace/tools"><Button variant="outline">Browse Tools</Button></Link>
            <Link href="/marketplace/providers"><Button variant="outline">Browse Providers</Button></Link>
          </div>
        </>
      )}
    </div>
  )
}
