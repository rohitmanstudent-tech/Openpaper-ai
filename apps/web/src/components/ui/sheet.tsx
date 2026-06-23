import * as React from "react"
import { cn } from "@/lib/utils"
import { X } from "lucide-react"

function Sheet({ open, onOpenChange, children }: { open: boolean; onOpenChange: (v: boolean) => void; children: React.ReactNode }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50">
      <div className="fixed inset-0 bg-black/50" onClick={() => onOpenChange(false)} />
      <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md border-l border-border bg-base-950 shadow-lg">
        <div className="flex items-center justify-between p-4 border-b border-border">
          <button onClick={() => onOpenChange(false)} className="rounded-lg p-1 hover:bg-white/5">
            <X className="h-5 w-5 text-muted-foreground" />
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}

export { Sheet }
