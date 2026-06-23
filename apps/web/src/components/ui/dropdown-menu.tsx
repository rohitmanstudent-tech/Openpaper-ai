import * as React from "react"
import { cn } from "@/lib/utils"
import { ChevronDown } from "lucide-react"

interface DropdownMenuContextType {
  open: boolean
  setOpen: (v: boolean) => void
}
const DropdownMenuContext = React.createContext<DropdownMenuContextType>({ open: false, setOpen: () => {} })

function DropdownMenu({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = React.useState(false)
  return (
    <DropdownMenuContext.Provider value={{ open, setOpen }}>
      <div className="relative inline-block">
        {React.Children.map(children, (child) => {
          if (React.isValidElement(child) && child.type === DropdownMenuTrigger) {
            return React.cloneElement(child as React.ReactElement<{ onClick?: () => void }>, { onClick: () => setOpen(!open) })
          }
          if (React.isValidElement(child) && child.type === DropdownMenuContent && open) {
            return (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
                <div className="absolute z-50 mt-1 min-w-[8rem]">
                  {child}
                </div>
              </>
            )
          }
          return child
        })}
      </div>
    </DropdownMenuContext.Provider>
  )
}

function DropdownMenuTrigger({ children, ...props }: React.HTMLAttributes<HTMLButtonElement>) {
  return <button type="button" className="flex items-center gap-1" {...props}>{children}</button>
}

function DropdownMenuContent({ className, children, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("rounded-lg border border-border bg-card text-card-foreground shadow-md p-1 min-w-[160px]", className)} {...props}>
      {children}
    </div>
  )
}

function DropdownMenuItem({ className, children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        "relative flex w-full cursor-default items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-white/5 data-[disabled]:opacity-50",
        className
      )}
      {...props}
    >
      {children}
    </button>
  )
}

function DropdownMenuLabel({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-2 py-1.5 text-xs font-medium text-muted-foreground", className)} {...props} />
}

function DropdownMenuSeparator({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("h-px bg-border my-1", className)} {...props} />
}

export { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator }
