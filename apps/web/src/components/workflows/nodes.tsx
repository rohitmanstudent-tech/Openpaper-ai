"use client"

import { memo } from "react"
import { Handle, Position, type NodeProps } from "@xyflow/react"
import { Bot, Search, Mail, Globe, Clock, GitBranch, Zap, Brain } from "lucide-react"

const NODE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  trigger: Zap,
  agent: Bot,
  knowledge_search: Search,
  condition: GitBranch,
  delay: Clock,
  http_request: Globe,
  email_sender: Mail,
  memory_store: Brain,
}

const NODE_COLORS: Record<string, string> = {
  trigger: "text-emerald-400 border-emerald-500/30 bg-emerald-500/5",
  agent: "text-accent-400 border-accent-500/30 bg-accent-500/5",
  knowledge_search: "text-cyan-400 border-cyan-500/30 bg-cyan-500/5",
  condition: "text-amber-400 border-amber-500/30 bg-amber-500/5",
  delay: "text-purple-400 border-purple-500/30 bg-purple-500/5",
  http_request: "text-blue-400 border-blue-500/30 bg-blue-500/5",
  email_sender: "text-rose-400 border-rose-500/30 bg-rose-500/5",
  memory_store: "text-violet-400 border-violet-500/30 bg-violet-500/5",
}

function BaseNode({ data, selected, type }: NodeProps & { type: string }) {
  const Icon = NODE_ICONS[type] || Bot
  const color = NODE_COLORS[type] || "text-muted-foreground border-border bg-base-900"

  return (
    <div className={`
      px-4 py-3 rounded-xl border-2 min-w-[180px] shadow-lg backdrop-blur-sm
      transition-all duration-200
      ${color}
      ${selected ? "ring-2 ring-accent-500 shadow-accent-500/20" : ""}
    `}>
      <Handle type="target" position={Position.Top} className="w-3 h-3 !bg-accent-500 border-2 border-base-950" />
      <div className="flex items-center gap-2">
        <Icon className="h-4 w-4 shrink-0" />
        <span className="text-sm font-medium text-foreground">{String(data.label || type)}</span>
      </div>
      {data.description ? (
        <p className="text-xs text-muted-foreground mt-1 truncate">{String(data.description)}</p>
      ) : null}
      <Handle type="source" position={Position.Bottom} className="w-3 h-3 !bg-accent-500 border-2 border-base-950" />
      {type === "condition" && (
        <>
          <Handle type="source" position={Position.Bottom} id="true" className="w-3 h-3 !bg-emerald-500 border-2 border-base-950 -translate-x-4" style={{ bottom: -8 }} />
          <Handle type="source" position={Position.Bottom} id="false" className="w-3 h-3 !bg-red-500 border-2 border-base-950 translate-x-4" style={{ bottom: -8 }} />
        </>
      )}
    </div>
  )
}

export const TriggerNode = memo((props: NodeProps) => <BaseNode {...props} type="trigger" />)
export const AgentNode = memo((props: NodeProps) => <BaseNode {...props} type="agent" />)
export const KnowledgeSearchNode = memo((props: NodeProps) => <BaseNode {...props} type="knowledge_search" />)
export const ConditionNode = memo((props: NodeProps) => <BaseNode {...props} type="condition" />)
export const DelayNode = memo((props: NodeProps) => <BaseNode {...props} type="delay" />)
export const HttpRequestNode = memo((props: NodeProps) => <BaseNode {...props} type="http_request" />)
export const EmailSenderNode = memo((props: NodeProps) => <BaseNode {...props} type="email_sender" />)
export const MemoryStoreNode = memo((props: NodeProps) => <BaseNode {...props} type="memory_store" />)

export const NODE_TYPES = {
  trigger: TriggerNode,
  agent: AgentNode,
  knowledge_search: KnowledgeSearchNode,
  condition: ConditionNode,
  delay: DelayNode,
  http_request: HttpRequestNode,
  email_sender: EmailSenderNode,
  memory_store: MemoryStoreNode,
}

export const NODE_DEFINITIONS = [
  { type: "trigger", label: "Trigger", icon: Zap, color: "text-emerald-400", description: "Start workflow execution" },
  { type: "agent", label: "Agent", icon: Bot, color: "text-accent-400", description: "CEO, Sales, Research, or Buyer Finder" },
  { type: "knowledge_search", label: "Knowledge Search", icon: Search, color: "text-cyan-400", description: "Search documents semantically" },
  { type: "condition", label: "Condition", icon: GitBranch, color: "text-amber-400", description: "Branch based on field value" },
  { type: "delay", label: "Delay", icon: Clock, color: "text-purple-400", description: "Wait before next node" },
  { type: "http_request", label: "HTTP Request", icon: Globe, color: "text-blue-400", description: "Call external API" },
  { type: "email_sender", label: "Email", icon: Mail, color: "text-rose-400", description: "Send notification" },
  { type: "memory_store", label: "Memory Store", icon: Brain, color: "text-violet-400", description: "Store in agent memory" },
]
