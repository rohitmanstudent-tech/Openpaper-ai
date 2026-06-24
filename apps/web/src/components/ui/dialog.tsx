import * as React from "react"
import { cn } from "@/lib/utils"
import { X } from "lucide-react"

function Dialog({ open, onOpenChange, children }: { open: boolean; onOpenChange: (v: boolean) => void; children: React.ReactNode }) {
  const childrenArray = React.Children.toArray(children)
  const trigger = childrenArray.find(
    (c) => React.isValidElement(c) && (c as React.ReactElement).type === DialogTrigger
  )
  const content = childrenArray.filter(
    (c) => !(React.isValidElement(c) && (c as React.ReactElement).type === DialogTrigger)
  )
  return (
    <>
      {trigger}
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => onOpenChange(false)} />
          <div className="relative z-50 w-full max-w-lg rounded-xl border border-border bg-card shadow-lg">
            <button onClick={() => onOpenChange(false)} className="absolute right-4 top-4 rounded-sm opacity-70 hover:opacity-100">
              <X className="h-4 w-4" />
            </button>
            {content}
          </div>
        </div>
      )}
    </>
  )
}

function DialogTrigger({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) {
  return <span onClick={onClick}>{children}</span>
}

function DialogHeader({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("flex flex-col space-y-1.5 p-6 pb-0", className)} {...props} />
}

function DialogTitle({ className, ...props }: React.HTMLAttributes<HTMLHeadingElement>) {
  return <h2 className={cn("text-lg font-semibold text-white", className)} {...props} />
}

function DialogContent({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-6 pt-4", className)} {...props} />
}

export { Dialog, DialogTrigger, DialogHeader, DialogTitle, DialogContent }
