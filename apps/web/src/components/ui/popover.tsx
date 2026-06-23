import * as React from "react"
import { cn } from "@/lib/utils"

function Popover({ open, onOpenChange, children }: { open?: boolean; onOpenChange?: (v: boolean) => void; children: React.ReactNode }) {
  const [internalOpen, setInternalOpen] = React.useState(false)
  const isOpen = open ?? internalOpen
  const setIsOpen = onOpenChange ?? setInternalOpen
  return (
    <div className="relative inline-block">
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child) && child.type === PopoverTrigger) {
          return React.cloneElement(child as React.ReactElement<{ onClick?: () => void }>, { onClick: () => setIsOpen(!isOpen) })
        }
        if (React.isValidElement(child) && child.type === PopoverContent && isOpen) {
          return (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
              <div className="absolute z-50 mt-1">
                {child}
              </div>
            </>
          )
        }
        return child
      })}
    </div>
  )
}

function PopoverTrigger({ children, ...props }: React.HTMLAttributes<HTMLButtonElement>) {
  return <button type="button" {...props}>{children}</button>
}

function PopoverContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("rounded-lg border border-border bg-card text-card-foreground shadow-md p-4 min-w-[200px]", className)} {...props}>
      {children}
    </div>
  )
}

export { Popover, PopoverTrigger, PopoverContent }
