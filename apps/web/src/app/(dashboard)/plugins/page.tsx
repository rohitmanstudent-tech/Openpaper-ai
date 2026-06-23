"use client"

import { useEffect, useState } from "react"
import { usePluginsStore, type Plugin } from "@/stores/plugins"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Select } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Puzzle, Plus, MoreVertical, Play, Pause, Trash2, RefreshCw, Search } from "lucide-react"

export default function PluginsPage() {
  const { plugins, loading, fetch, install, toggle, remove, discover } = usePluginsStore()
  const [search, setSearch] = useState("")
  const [showInstall, setShowInstall] = useState(false)
  const [installForm, setInstallForm] = useState({ name: "", description: "", plugin_type: "tool" })

  useEffect(() => { fetch() }, [])

  const filtered = search
    ? plugins.filter((p) => p.name.toLowerCase().includes(search.toLowerCase()) || p.description?.toLowerCase().includes(search.toLowerCase()))
    : plugins

  const handleInstall = async (e: React.FormEvent) => {
    e.preventDefault()
    await install(installForm)
    setInstallForm({ name: "", description: "", plugin_type: "tool" })
    setShowInstall(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Plugins</h1>
          <p className="text-muted-foreground text-sm mt-1">Extend functionality with plugins</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={discover}>
            <RefreshCw className="h-4 w-4 mr-2" /> Discover
          </Button>
          <Dialog open={showInstall} onOpenChange={setShowInstall}>
            <DialogTrigger>
              <Button><Plus className="h-4 w-4 mr-2" /> Install Plugin</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Install Plugin</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleInstall} className="space-y-4">
                <div className="space-y-2">
                  <Label>Name</Label>
                  <Input value={installForm.name} onChange={(e) => setInstallForm({ ...installForm, name: e.target.value })} required />
                </div>
                <div className="space-y-2">
                  <Label>Type</Label>
                  <Select value={installForm.plugin_type} onChange={(e) => setInstallForm({ ...installForm, plugin_type: e.target.value })}>
                    <option value="tool">Tool</option>
                    <option value="agent">Agent</option>
                    <option value="provider">Provider</option>
                    <option value="hook">Hook</option>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Description</Label>
                  <Textarea value={installForm.description} onChange={(e) => setInstallForm({ ...installForm, description: e.target.value })} />
                </div>
                <Button type="submit">Install</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input className="pl-10" placeholder="Search plugins..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}><CardContent className="h-32 animate-pulse bg-base-800/50 rounded-xl" /></Card>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Puzzle className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No plugins found.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((plugin) => (
            <PluginCard key={plugin.id} plugin={plugin} onToggle={toggle} onRemove={remove} />
          ))}
        </div>
      )}
    </div>
  )
}

function PluginCard({ plugin, onToggle, onRemove }: { plugin: Plugin; onToggle: (id: string, enable: boolean) => Promise<void>; onRemove: (id: string) => Promise<void> }) {
  return (
    <Card className="group">
      <CardHeader className="flex flex-row items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-white/5 flex items-center justify-center">
            <Puzzle className="h-5 w-5 text-accent-400" />
          </div>
          <div>
            <CardTitle className="text-base">{plugin.name}</CardTitle>
            <p className="text-xs text-muted-foreground">v{plugin.version} · {plugin.plugin_type}</p>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger>
            <MoreVertical className="h-4 w-4" />
          </DropdownMenuTrigger>
          <DropdownMenuContent>
            <DropdownMenuItem onClick={() => onToggle(plugin.id, plugin.status !== "active")}>
              {plugin.status === "active" ? <Pause className="h-4 w-4 mr-2" /> : <Play className="h-4 w-4 mr-2" />}
              {plugin.status === "active" ? "Disable" : "Enable"}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onRemove(plugin.id)} className="text-red-400">
              <Trash2 className="h-4 w-4 mr-2" /> Remove
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent>
        <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{plugin.description || "No description"}</p>
        <div className="flex items-center justify-between">
          <Badge variant={plugin.status === "active" ? "success" : "secondary"}>
            {plugin.status}
          </Badge>
          <span className="text-xs text-muted-foreground">{plugin.author}</span>
        </div>
        {plugin.hooks && plugin.hooks.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {plugin.hooks.map((hook) => (
              <Badge key={hook} variant="outline" className="text-[10px]">{hook}</Badge>
            ))}
          </div>
        )}
        {plugin.error && (
          <p className="text-xs text-red-400 mt-2">{plugin.error}</p>
        )}
      </CardContent>
    </Card>
  )
}
