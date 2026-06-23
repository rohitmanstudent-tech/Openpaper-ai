import * as React from "react"
import { cn } from "@/lib/utils"

const badgeVariants = {
  default: "bg-accent-500/10 text-accent-400 border-accent-500/20",
  secondary: "bg-base-800 text-muted-foreground border-border",
  destructive: "bg-red-500/10 text-red-400 border-red-500/20",
  success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  outline: "bg-transparent text-foreground border-border",
}

function Badge({ className, variant = "default", ...props }: React.HTMLAttributes<HTMLDivElement> & { variant?: keyof typeof badgeVariants }) {
  return <div className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors", badgeVariants[variant], className)} {...props} />
}

export { Badge, badgeVariants }
