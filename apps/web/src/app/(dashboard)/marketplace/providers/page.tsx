"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { useMarketplaceStore } from "@/stores/marketplace"
import { useAuthStore } from "@/stores/auth"
import { Radio, Star, Download, Loader2, ArrowLeft, Search, Trash2, RefreshCw } from "lucide-react"

export default function MarketplaceProvidersPage() {
  const router = useRouter()
  const { token } = useAuthStore()
  const { items, installed, loading, installItem, uninstallItem, updateItem, fetchItems, fetchInstalled } = useMarketplaceStore()
  const [search, setSearch] = useState("")

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetchItems({ category: "providers" })
    fetchInstalled()
  }, [])

  const filtered = items.filter((i) => {
    if (!search.trim()) return true
    const q = search.toLowerCase()
    return i.name.toLowerCase().includes(q) || i.description.toLowerCase().includes(q) || i.tags.some((t) => t.includes(q))
  })

  const getStatus = (itemId: string) => installed.find((i) => i.item_id === itemId)?.status || "not_installed"

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.push("/marketplace")}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back
        </Button>
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Radio className="h-8 w-8 text-purple-400" /> Provider Marketplace
          </h1>
          <p className="text-muted-foreground mt-1">AI model providers and inference services</p>
        </div>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input placeholder="Search providers..." className="pl-10" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-accent-400" />
        </div>
      ) : filtered.length === 0 ? (
        <Card className="border-white/10">
          <CardContent className="p-12 text-center">
            <Radio className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No providers found</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((item) => {
            const status = getStatus(item.id)
            return (
              <Card key={item.id} className="border-white/10 flex flex-col">
                <Link href={`/marketplace/${item.id}`} className="flex-1">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-base text-white">{item.name}</CardTitle>
                      <Badge variant="secondary" className="text-xs">v{item.version}</Badge>
                    </div>
                    <CardDescription className="line-clamp-2">{item.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="pb-3">
                    <div className="flex items-center gap-4 text-xs text-muted-foreground mb-3">
                      <span className="flex items-center gap-1"><Star className="h-3 w-3 text-amber-400" /> {item.rating}</span>
                      <span className="flex items-center gap-1"><Download className="h-3 w-3" /> {item.downloads}</span>
                      <span className="capitalize">{item.item_type}</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {item.tags.slice(0, 4).map((tag) => (
                        <Badge key={tag} variant="outline" className="text-xs">{tag}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Link>
                <div className="px-6 pb-4 pt-0 flex gap-2">
                  {status === "installed" ? (
                    <>
                      <Button size="sm" variant="outline" className="flex-1" onClick={() => uninstallItem(item.id)}>
                        <Trash2 className="h-4 w-4 mr-1" /> Uninstall
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => updateItem(item.id)}>
                        <RefreshCw className="h-4 w-4" />
                      </Button>
                    </>
                  ) : (
                    <Button size="sm" className="w-full" onClick={() => installItem(item.id)}>
                      <Download className="h-4 w-4 mr-1" /> Install
                    </Button>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}
