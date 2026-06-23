"use client"

import { useEffect, useState, useCallback } from "react"
import { useAgentStore } from "@/stores/agents"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Select } from "@/components/ui/select"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Bot, Plus, Play, Trash2, SendHorizonal, Loader2 } from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

export default function AgentsPage() {
  const { agents, fetch, create, update, remove, loading } = useAgentStore()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: "", agent_type: "research", model: "llama3.1", provider: "ollama", description: "" })
  const [execAgent, setExecAgent] = useState<number | null>(null)
  const [execInput, setExecInput] = useState("")
  const [execOutput, setExecOutput] = useState("")
  const [execStreaming, setExecStreaming] = useState(false)
  const [delAgent, setDelAgent] = useState<number | null>(null)
  const [delTarget, setDelTarget] = useState("")
  const [delInput, setDelInput] = useState("")

  useEffect(() => { fetch() }, [])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    await create(form as any)
    setForm({ name: "", agent_type: "research", model: "llama3.1", provider: "ollama", description: "" })
    setShowForm(false)
  }

  const handleExecute = useCallback(async (agentId: number) => {
    if (!execInput.trim()) return
    setExecStreaming(true)
    setExecOutput("")
    try {
      const res = await globalThis.fetch(`${API_URL}/agents/${agentId}/execute`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ input: execInput, stream: true }),
      })
      const reader = res.body?.getReader()
      if (!reader) return
      const decoder = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const text = decoder.decode(value)
        const lines = text.split("\n")
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.content) setExecOutput((prev) => prev + data.content)
              if (data.done) { fetch(); setExecStreaming(false) }
            } catch { /* skip */ }
          }
        }
      }
    } catch (e) {
      setExecOutput(`Error: ${e}`)
    }
    setExecStreaming(false)
  }, [execInput])

  const handleDelegate = useCallback(async (agentId: number) => {
    if (!delInput.trim() || !delTarget) return
    try {
      const res = await globalThis.fetch(`${API_URL}/agents/${agentId}/delegate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ target_agent_type: delTarget, input: delInput }),
      })
      const data = await res.json()
      setExecOutput(`Delegated to ${data.delegated_to}: ${data.result}`)
      fetch()
    } catch (e) {
      setExecOutput(`Error: ${e}`)
    }
  }, [delInput, delTarget])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Agent Workspace</h1>
          <p className="text-muted-foreground text-sm mt-1">Manage and interact with AI agents</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="h-4 w-4 mr-2" /> New Agent
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Create Agent</CardTitle></CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Name</Label>
                  <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
                </div>
                <div className="space-y-2">
                  <Label>Type</Label>
                  <Select value={form.agent_type} onChange={(e) => setForm({ ...form, agent_type: e.target.value })}>
                    <option value="research">Research</option>
                    <option value="sales">Sales</option>
                    <option value="ceo">CEO</option>
                    <option value="buyer_finder">Buyer Finder</option>
                    <option value="operations">Operations</option>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Model</Label>
                  <Input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
                </div>
                <div className="space-y-2">
                  <Label>Provider</Label>
                  <Select value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })}>
                    <option value="ollama">Ollama</option>
                    <option value="openai">OpenAI</option>
                    <option value="claude">Claude</option>
                    <option value="openrouter">OpenRouter</option>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Description</Label>
                <Textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
              </div>
              <Button type="submit">Create</Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Execute Dialog */}
      <Dialog open={execAgent !== null} onOpenChange={(v) => { if (!v) { setExecAgent(null); setExecOutput("") } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Execute Agent</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Input</Label>
              <Textarea value={execInput} onChange={(e) => setExecInput(e.target.value)} placeholder="Enter task for agent..." />
            </div>
            <Button onClick={() => execAgent && handleExecute(execAgent)} disabled={execStreaming || !execInput.trim()}>
              {execStreaming ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <SendHorizonal className="h-4 w-4 mr-2" />}
              {execStreaming ? "Running..." : "Execute"}
            </Button>
            {execOutput && (
              <div className="rounded-lg bg-base-900 p-4">
                <p className="text-xs text-muted-foreground mb-2">Output:</p>
                <p className="text-sm text-foreground whitespace-pre-wrap">{execOutput}</p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Delegate Dialog */}
      <Dialog open={delAgent !== null} onOpenChange={(v) => { if (!v) { setDelAgent(null); setExecOutput("") } }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delegate Task</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label>Target Agent Type</Label>
              <Select value={delTarget} onChange={(e) => setDelTarget(e.target.value)}>
                <option value="">Select...</option>
                <option value="research">Research</option>
                <option value="sales">Sales</option>
                <option value="ceo">CEO</option>
                <option value="buyer_finder">Buyer Finder</option>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Input</Label>
              <Textarea value={delInput} onChange={(e) => setDelInput(e.target.value)} placeholder="Task details..." />
            </div>
            <Button onClick={() => delAgent && handleDelegate(delAgent)} disabled={!delTarget || !delInput.trim()}>
              <SendHorizonal className="h-4 w-4 mr-2" /> Delegate
            </Button>
            {execOutput && (
              <div className="rounded-lg bg-base-900 p-4">
                <p className="text-sm text-foreground whitespace-pre-wrap">{execOutput}</p>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}><CardContent className="h-32 animate-pulse bg-base-800/50 rounded-xl" /></Card>
          ))}
        </div>
      ) : agents.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12 text-center">
            <Bot className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">No agents yet. Create your first agent.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent) => (
            <Card key={agent.id} className="group">
              <CardHeader className="flex flex-row items-start justify-between">
                <div>
                  <CardTitle className="text-base">{agent.name}</CardTitle>
                  <p className="text-xs text-muted-foreground mt-1 capitalize">{agent.agent_type}</p>
                </div>
                <Badge variant={agent.status === "idle" ? "success" : agent.status === "working" ? "default" : "warning"}>
                  {agent.status}
                </Badge>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground mb-3 line-clamp-2">{agent.description || "No description"}</p>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-muted-foreground">{agent.provider}/{agent.model}</span>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="flex-1" onClick={() => { setExecAgent(agent.id); setExecInput(""); setExecOutput("") }}>
                    <Play className="h-3 w-3 mr-1" /> Execute
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1" onClick={() => { setDelAgent(agent.id); setDelTarget(""); setDelInput(""); setExecOutput("") }}>
                    <SendHorizonal className="h-3 w-3 mr-1" /> Delegate
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => remove(agent.id)}>
                    <Trash2 className="h-3 w-3 text-red-400" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
