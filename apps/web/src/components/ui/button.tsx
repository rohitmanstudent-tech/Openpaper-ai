import * as React from "react"
import { cn } from "@/lib/utils"

const Button = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "default" | "ghost" | "outline" | "destructive"; size?: "sm" | "md" | "lg" }>(
  ({ className, variant = "default", size = "md", ...props }, ref) => {
    const variants: Record<string, string> = {
      default: "bg-accent-500 text-white hover:bg-accent-600",
      ghost: "bg-transparent hover:bg-white/5 text-foreground",
      outline: "border border-border bg-transparent hover:bg-white/5 text-foreground",
      destructive: "bg-red-600 text-white hover:bg-red-700",
    }
    const sizes: Record<string, string> = {
      sm: "h-8 px-3 text-xs rounded-md",
      md: "h-10 px-4 text-sm rounded-lg",
      lg: "h-12 px-6 text-base rounded-lg",
    }
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center font-medium transition-colors disabled:opacity-50 disabled:pointer-events-none",
          variants[variant],
          sizes[size],
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }
