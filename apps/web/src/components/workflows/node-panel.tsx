"use client"

import type { WorkflowNode } from "@/stores/workflows"
import { NODE_DEFINITIONS } from "./nodes"

interface NodePanelProps {
  onAddNode: (node: WorkflowNode) => void
}

export function NodePanel({ onAddNode }: NodePanelProps) {
  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData("application/reactflow", nodeType)
    event.dataTransfer.effectAllowed = "move"
  }

  return (
    <div className="w-64 bg-base-950 border-r border-border p-4 space-y-3 overflow-y-auto shrink-0">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Nodes</h3>
      <div className="space-y-2">
        {NODE_DEFINITIONS.map((def) => {
          const Icon = def.icon
          return (
            <div
              key={def.type}
              draggable
              onDragStart={(e) => onDragStart(e, def.type)}
              className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-base-900 border border-border cursor-grab active:cursor-grabbing hover:border-accent-500/30 hover:bg-base-800 transition-colors"
            >
              <Icon className={`h-4 w-4 ${def.color}`} />
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground">{def.label}</p>
                <p className="text-xs text-muted-foreground truncate">{def.description}</p>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
