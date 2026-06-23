"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Workflow, Plus, Play, Pause, GitBranch, GripVertical, ArrowRight, Settings, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface WorkflowItem {
  id: number; name: string; description: string;
  status: "active" | "paused" | "draft";
  steps: number; last_run: string; agent: string;
}

const initialWorkflows: WorkflowItem[] = [
  { id: 1, name: "Lead Qualification", description: "Score and qualify inbound leads", status: "active", steps: 5, last_run: "2m ago", agent: "Sales Agent" },
  { id: 2, name: "Market Research", description: "Weekly competitor analysis pipeline", status: "active", steps: 4, last_run: "15m ago", agent: "Research Agent" },
  { id: 3, name: "Onboarding Sequences", description: "New user onboarding workflow", status: "paused", steps: 7, last_run: "2h ago", agent: "Operations Agent" },
  { id: 4, name: "Q4 Report Generation", description: "Quarterly business review", status: "draft", steps: 3, last_run: "Never", agent: "CEO Agent" },
  { id: 5, name: "Buyer Intent Analysis", description: "Track and score buyer signals", status: "active", steps: 6, last_run: "45m ago", agent: "Buyer Finder" },
];

const stepExamples = [
  { id: 1, type: "trigger", label: "Webhook Received", color: "text-accent-400" },
  { id: 2, type: "agent", label: "Research Agent", color: "text-emerald-400" },
  { id: 3, type: "condition", label: "Score > 80?", color: "text-amber-400" },
  { id: 4, type: "action", label: "Send to CRM", color: "text-base-400" },
];

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState(initialWorkflows);
  const [selected, setSelected] = useState<WorkflowItem | null>(null);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-base-100">Workflows</h1>
          <p className="mt-0.5 text-sm text-base-400">Build and manage agent automation pipelines</p>
        </div>
        <Button>
          <Plus size={15} className="mr-1.5" />
          New Workflow
        </Button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Workflow list */}
        <div className="lg:col-span-1 space-y-3">
          {workflows.map((w) => (
            <button key={w.id} onClick={() => setSelected(w)}
              className={cn(
                "w-full text-left rounded-lg border p-3 transition-all",
                selected?.id === w.id
                  ? "border-accent-500/40 bg-accent-500/5"
                  : "border-base-700/50 bg-base-900/60 card-hover"
              )}>
              <div className="flex items-center justify-between mb-1">
                <p className="text-sm font-medium text-base-100">{w.name}</p>
                <Badge variant={w.status === "active" ? "working" : w.status === "paused" ? "paused" : "pending"}>
                  {w.status}
                </Badge>
              </div>
              <p className="text-xs text-base-500 line-clamp-1">{w.description}</p>
              <div className="mt-2 flex items-center gap-3 text-[11px] text-base-500">
                <span>{w.steps} steps</span>
                <span>{w.agent}</span>
                <span className="ml-auto">{w.last_run}</span>
              </div>
            </button>
          ))}
        </div>

        {/* Workflow detail / canvas */}
        <div className="lg:col-span-2">
          {selected ? (
            <Card className="p-4">
              <div className="flex items-center justify-between mb-4 pb-4 border-b border-base-700/30">
                <div>
                  <h2 className="text-base font-semibold text-base-100">{selected.name}</h2>
                  <p className="text-xs text-base-500">{selected.description}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button className="rounded-md border border-base-700/50 px-2.5 py-1.5 text-xs text-base-400 transition-colors hover:border-base-600 hover:text-base-200">
                    <Settings size={13} />
                  </button>
                  <button className="rounded-md border border-base-700/50 px-2.5 py-1.5 text-xs text-base-400 transition-colors hover:border-base-600 hover:text-base-200">
                    <Trash2 size={13} />
                  </button>
                  <Button size="sm">{selected.status === "active" ? <><Pause size={13} className="mr-1" />Pause</> : <><Play size={13} className="mr-1" />Run</>}</Button>
                </div>
              </div>

              {/* Pipeline visual */}
              <div className="space-y-2">
                {stepExamples.map((step, i) => (
                  <div key={step.id}>
                    <div className={cn(
                      "flex items-center gap-3 rounded-md border border-base-700/30 bg-base-800/30 px-3 py-2.5",
                      "transition-colors hover:border-base-600/50"
                    )}>
                      <GripVertical size={13} className="text-base-600 cursor-grab" />
                      <div className="flex items-center gap-2">
                        <div className={cn(
                          "h-1.5 w-1.5 rounded-full",
                          step.type === "trigger" ? "bg-accent-400" :
                          step.type === "agent" ? "bg-emerald-400" :
                          step.type === "condition" ? "bg-amber-400" : "bg-base-400"
                        )} />
                        <span className="text-xs font-medium text-base-300">{step.label}</span>
                      </div>
                      <span className="text-[10px] text-base-600 uppercase tracking-wider">{step.type}</span>
                    </div>
                    {i < stepExamples.length - 1 && (
                      <div className="flex justify-center py-1">
                        <ArrowRight size={12} className="text-base-600" />
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <button className="mt-4 flex w-full items-center justify-center gap-2 rounded-md border border-dashed border-base-700/50 py-2.5 text-xs text-base-500 transition-colors hover:border-base-600 hover:text-base-300">
                <Plus size={13} />
                Add Step
              </button>
            </Card>
          ) : (
            <Card className="flex flex-col items-center justify-center py-16">
              <GitBranch size={40} className="mb-3 text-base-700" />
              <p className="text-sm font-medium text-base-500">Select a workflow</p>
              <p className="text-xs text-base-600">Choose a workflow from the list to view its pipeline</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
