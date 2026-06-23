"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { useRouter, useParams } from "next/navigation"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useMarketplaceStore } from "@/stores/marketplace"
import { useAuthStore } from "@/stores/auth"
import { ArrowLeft, Star, Download, Loader2, Bot, GitBranch, Wrench, Radio, Store, Check, Trash2, RefreshCw, Shield, Package, BookOpen } from "lucide-react"

const TYPE_ICONS: Record<string, { icon: React.ElementType; color: string }> = {
  agent: { icon: Bot, color: "text-accent-400" },
  workflow: { icon: GitBranch, color: "text-emerald-400" },
  tool: { icon: Wrench, color: "text-amber-400" },
  provider: { icon: Radio, color: "text-purple-400" },
}

export default function MarketplaceDetailPage() {
  const router = useRouter()
  const params = useParams()
  const { token } = useAuthStore()
  const { items, installed, loading, installItem, uninstallItem, updateItem, fetchItems, fetchInstalled } = useMarketplaceStore()
  const [actionLoading, setActionLoading] = useState(false)

  const itemId = params.id as string

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    fetchItems()
    fetchInstalled()
  }, [])

  const item = items.find((i) => i.id === itemId)
  const installInfo = installed.find((i) => i.item_id === itemId)
  const typeConfig = TYPE_ICONS[item?.item_type || ""] || { icon: Store, color: "text-muted-foreground" }
  const TypeIcon = typeConfig.icon

  const handleInstall = async () => {
    setActionLoading(true)
    await installItem(itemId)
    setActionLoading(false)
  }

  const handleUninstall = async () => {
    setActionLoading(true)
    await uninstallItem(itemId)
    setActionLoading(false)
  }

  const handleUpdate = async () => {
    setActionLoading(true)
    await updateItem(itemId)
    setActionLoading(false)
  }

  if (loading && !item) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-accent-400" />
      </div>
    )
  }

  if (!item) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/marketplace")}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back
        </Button>
        <Card className="border-white/10">
          <CardContent className="p-12 text-center">
            <Store className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Item not found</p>
            <Button variant="outline" className="mt-4" onClick={() => router.push("/marketplace")}>
              Browse Marketplace
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  const status = installInfo?.status || "not_installed"

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back
        </Button>
      </div>

      <Card className="border-white/10">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <TypeIcon className={`h-10 w-10 ${typeConfig.color}`} />
              <div>
                <CardTitle className="text-2xl text-white">{item.name}</CardTitle>
                <CardDescription className="text-base">{item.description}</CardDescription>
              </div>
            </div>
            <Badge variant="secondary" className="text-sm px-3 py-1">
              v{item.version}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center gap-6 text-sm">
            <span className="flex items-center gap-1 text-muted-foreground">
              <Star className="h-4 w-4 text-amber-400" /> {item.rating} / 5
            </span>
            <span className="flex items-center gap-1 text-muted-foreground">
              <Download className="h-4 w-4" /> {item.downloads.toLocaleString()} downloads
            </span>
            <span className="text-muted-foreground">by {item.author}</span>
            <Badge variant="outline" className="capitalize">{item.item_type}</Badge>
          </div>

          <div className="flex flex-wrap gap-2">
            {item.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">{tag}</Badge>
            ))}
          </div>

          <div className="flex gap-3">
            {status === "installed" ? (
              <>
                <Button variant="default" onClick={handleUpdate} disabled={actionLoading}>
                  <RefreshCw className={`h-4 w-4 mr-1 ${actionLoading ? "animate-spin" : ""}`} /> Update
                </Button>
                <Button variant="destructive" onClick={handleUninstall} disabled={actionLoading}>
                  <Trash2 className="h-4 w-4 mr-1" /> Uninstall
                </Button>
                <Badge variant="success" className="text-sm py-1 px-3">
                  <Check className="h-4 w-4 mr-1" /> Installed
                </Badge>
              </>
            ) : (
              <Button variant="default" size="lg" onClick={handleInstall} disabled={actionLoading}>
                <Download className={`h-4 w-4 mr-1 ${actionLoading ? "animate-spin" : ""}`} /> Install
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-white/10">
          <CardHeader>
            <CardTitle className="text-sm text-white flex items-center gap-2">
              <Shield className="h-4 w-4 text-accent-400" /> Permissions
            </CardTitle>
          </CardHeader>
          <CardContent>
            {item.permissions.length > 0 ? (
              <ul className="space-y-1">
                {item.permissions.map((p) => (
                  <li key={p} className="text-sm text-muted-foreground">- {p}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No special permissions required</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-white/10">
          <CardHeader>
            <CardTitle className="text-sm text-white flex items-center gap-2">
              <Package className="h-4 w-4 text-emerald-400" /> Dependencies
            </CardTitle>
          </CardHeader>
          <CardContent>
            {item.dependencies.length > 0 ? (
              <ul className="space-y-1">
                {item.dependencies.map((dep) => (
                  <li key={dep} className="text-sm">
                    <Link href={`/marketplace/${dep}`} className="text-accent-400 hover:underline">
                      {dep}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No dependencies</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-white/10">
          <CardHeader>
            <CardTitle className="text-sm text-white flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-amber-400" /> Info
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm text-muted-foreground">
            <p>Type: <span className="capitalize">{item.item_type}</span></p>
            <p>Version: {item.version}</p>
            <p>Author: {item.author}</p>
            {installInfo && <p>Installed: {new Date(installInfo.installed_at).toLocaleDateString()}</p>}
          </CardContent>
        </Card>
      </div>

      {item.readme && (
        <Card className="border-white/10">
          <CardHeader>
            <CardTitle className="text-lg text-white">README</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-invert max-w-none text-sm text-muted-foreground whitespace-pre-wrap">
              {item.readme}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
