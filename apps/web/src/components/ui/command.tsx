import * as React from "react"
import { cn } from "@/lib/utils"

function Command({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-lg border border-border bg-card shadow-md", className)} {...props}>{children}</div>
}

function CommandInput({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex items-center border-b border-border px-3">
      <input className={cn("flex h-11 w-full bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground", className)} {...props} />
    </div>
  )
}

function CommandList({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("max-h-72 overflow-y-auto p-1", className)} {...props}>{children}</div>
}

function CommandEmpty({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("py-6 text-center text-sm text-muted-foreground", className)} {...props}>{children}</div>
}

function CommandGroup({ className, heading, children, ...props }: React.HTMLAttributes<HTMLDivElement> & { heading?: string }) {
  return (
    <div className={cn("overflow-hidden p-1", className)} {...props}>
      {heading && <div className="px-2 py-1.5 text-xs font-medium text-muted-foreground">{heading}</div>}
      {children}
    </div>
  )
}

function CommandItem({ className, children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "relative flex w-full cursor-default items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-white/5 aria-selected:bg-white/5 data-[disabled]:opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem }
