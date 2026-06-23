"use client"

import { useCallback, useRef, useState } from "react"
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  type EdgeChange,
  useReactFlow,
  ReactFlowProvider,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import { NODE_TYPES } from "./nodes"
import { Button } from "@/components/ui/button"
import { Save, Play, Trash2 } from "lucide-react"

interface FlowCanvasProps {
  nodes: Node[]
  edges: Edge[]
  onNodesChange: (changes: NodeChange[]) => void
  onEdgesChange: (changes: EdgeChange[]) => void
  onConnect: (connection: Connection) => void
  onSave: () => void
  onExecute: () => void
  onAddNode: (type: string, position: { x: number; y: number }) => void
  saving?: boolean
  executing?: boolean
  workflowName?: string
}

function FlowCanvasInner({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onConnect,
  onSave,
  onExecute,
  onAddNode,
  saving,
  executing,
  workflowName,
}: FlowCanvasProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const { screenToFlowPosition } = useReactFlow()
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = "move"
  }, [])

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault()
      const type = event.dataTransfer.getData("application/reactflow")
      if (!type || !reactFlowWrapper.current) return
      const position = screenToFlowPosition({ x: event.clientX, y: event.clientY })
      onAddNode(type, position)
    },
    [screenToFlowPosition, onAddNode]
  )

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  const onPaneClick = useCallback(() => {
    setSelectedNode(null)
  }, [])

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-base-950">
        <h2 className="text-sm font-medium text-foreground">{workflowName || "Untitled Workflow"}</h2>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onSave} disabled={saving}>
            <Save className="h-4 w-4 mr-1" />
            {saving ? "Saving..." : "Save"}
          </Button>
          <Button size="sm" onClick={onExecute} disabled={executing}>
            <Play className="h-4 w-4 mr-1" />
            {executing ? "Running..." : "Execute"}
          </Button>
        </div>
      </div>

      <div className="flex-1" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          nodeTypes={NODE_TYPES}
          fitView
          deleteKeyCode={["Backspace", "Delete"]}
          className="bg-base-900/50"
          defaultEdgeOptions={{
            animated: true,
            style: { stroke: "#4b5563", strokeWidth: 2 },
            labelStyle: { fill: "#9ca3af", fontSize: 11 },
          }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#1f2937" />
          <Controls className="bg-base-950 border border-border rounded-lg [&_button]:text-muted-foreground [&_button]:hover:text-foreground [&_button]:hover:bg-base-800" />
          <MiniMap
            nodeStrokeColor="#6366f1"
            nodeColor="#1e293b"
            maskColor="rgba(0,0,0,0.7)"
            className="border border-border rounded-lg"
          />
        </ReactFlow>
      </div>
    </div>
  )
}

export function FlowCanvas(props: FlowCanvasProps) {
  return (
    <ReactFlowProvider>
      <FlowCanvasInner {...props} />
    </ReactFlowProvider>
  )
}
