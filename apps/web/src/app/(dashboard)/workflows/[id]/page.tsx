"use client"

import { useEffect, useState, useCallback } from "react"
import { useParams, useRouter } from "next/navigation"
import {
  type Node,
  type Edge,
  type Connection,
  type NodeChange,
  type EdgeChange,
  addEdge,
  applyNodeChanges,
  applyEdgeChanges,
} from "@xyflow/react"
import { useAuthStore } from "@/stores/auth"
import { useWorkflowStore, type WorkflowNode, type WorkflowEdge } from "@/stores/workflows"
import { FlowCanvas } from "@/components/workflows/canvas"
import { NodePanel } from "@/components/workflows/node-panel"
import { Loader2 } from "lucide-react"

let nodeCounter = 0

export default function WorkflowEditorPage() {
  const { id } = useParams<{ id: string }>()
  const { token } = useAuthStore()
  const router = useRouter()
  const { get: fetchWorkflow, save, execute, current } = useWorkflowStore()
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [saving, setSaving] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!token) { router.push("/login"); return }
    ;(async () => {
      try {
        const wf = await fetchWorkflow(Number(id))
        if (wf.nodes?.length) {
          setNodes(wf.nodes as Node[])
        }
        if (wf.edges?.length) {
          setEdges(wf.edges as Edge[])
        }
      } catch {
        router.push("/workflows")
      } finally {
        setLoading(false)
      }
    })()
  }, [token, id])

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setNodes((nds) => applyNodeChanges(changes, nds))
  }, [])

  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    setEdges((eds) => applyEdgeChanges(changes, eds))
  }, [])

  const onConnect = useCallback((connection: Connection) => {
    setEdges((eds) => addEdge(connection, eds))
  }, [])

  const onAddNodeFromPanel = useCallback((node: WorkflowNode) => {
    setNodes((nds) => [...nds, node as Node])
  }, [])

  const onAddNode = useCallback((type: string, position: { x: number; y: number }) => {
    nodeCounter++
    const id = `node_${Date.now()}_${nodeCounter}`
    const newNode: Node = {
      id,
      type,
      position,
      data: {
        label: type.charAt(0).toUpperCase() + type.slice(1).replace("_", " "),
        description: getNodeDescription(type),
        ...getDefaultData(type),
      },
    }
    setNodes((nds) => [...nds, newNode])
  }, [])

  const handleSave = useCallback(async () => {
    setSaving(true)
    try {
      await save(Number(id), {
        nodes: nodes as unknown as WorkflowNode[],
        edges: edges as unknown as WorkflowEdge[],
      })
    } finally {
      setSaving(false)
    }
  }, [id, nodes, edges, save])

  const handleExecute = useCallback(async () => {
    setExecuting(true)
    try {
      await execute(Number(id))
    } finally {
      setExecuting(false)
    }
  }, [id, execute])

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-6 w-6 text-accent-400 animate-spin" />
      </div>
    )
  }

  return (
    <div className="flex h-[calc(100vh-4rem)] -m-6 lg:-m-8">
      <NodePanel onAddNode={onAddNodeFromPanel} />
      <FlowCanvas
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onSave={handleSave}
        onExecute={handleExecute}
        onAddNode={onAddNode}
        saving={saving}
        executing={executing}
        workflowName={current?.name}
      />
    </div>
  )
}

function getDefaultData(type: string): Record<string, unknown> {
  switch (type) {
    case "trigger":
      return { input: {} }
    case "agent":
      return { agent_type: "ceo", provider: "ollama", model: "llama3.1", input: "" }
    case "knowledge_search":
      return { query: "", limit: 5 }
    case "condition":
      return { field: "", operator: "exists", value: "" }
    case "delay":
      return { seconds: 1 }
    case "http_request":
      return { url: "", method: "GET", headers: {}, body: null }
    case "email_sender":
      return { to: "", subject: "", body: "" }
    case "memory_store":
      return { content: "", memory_type: "semantic", agent_id: "workflow" }
    default:
      return {}
  }
}

function getNodeDescription(type: string): string {
  const descriptions: Record<string, string> = {
    trigger: "Starts workflow execution",
    agent: "CEO, Sales, Research, or Buyer Finder agent",
    knowledge_search: "Search documents semantically",
    condition: "Branch based on field value comparison",
    delay: "Wait before executing next node",
    http_request: "Call external HTTP API",
    email_sender: "Send an email notification",
    memory_store: "Store result in agent memory",
  }
  return descriptions[type] || ""
}
