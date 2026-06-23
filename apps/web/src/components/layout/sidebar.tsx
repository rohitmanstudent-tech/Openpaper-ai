"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { Bot, MessageSquare, Cpu, Settings, LayoutDashboard, ChevronLeft, ChevronRight, CheckSquare, Puzzle, Box, BookOpen, FileText, Brain, GitBranch, History, Activity, BarChart3, Share2, Store } from "lucide-react"
import { Button } from "@/components/ui/button"

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/agents", label: "Agents", icon: Bot },
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/tasks", label: "Tasks", icon: CheckSquare },
  { href: "/workflows", label: "Workflows", icon: GitBranch },
  { href: "/workflows/runs", label: "Runs", icon: History },
  { href: "/agent-graph", label: "Agent Graph", icon: Share2 },
  { href: "/knowledge", label: "Knowledge", icon: BookOpen },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/memory", label: "Memory", icon: Brain },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/models", label: "Models", icon: Box },
  { href: "/marketplace", label: "Marketplace", icon: Store },
  { href: "/plugins", label: "Plugins", icon: Puzzle },
  { href: "/settings", label: "Settings", icon: Settings },
]

interface SidebarProps {
  collapsed: boolean
  onToggle: () => void
  mobileOpen: boolean
  onMobileClose: () => void
}

export function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }: SidebarProps) {
  const pathname = usePathname()

  return (
    <>
      {mobileOpen && <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={onMobileClose} />}

      <aside
        className={cn(
          "fixed top-0 left-0 z-50 h-full bg-base-950 border-r border-border transition-all duration-300 flex flex-col",
          collapsed ? "w-16" : "w-64",
          mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <div className={cn("flex items-center h-16 px-4 border-b border-border", collapsed ? "justify-center" : "justify-between")}>
          {!collapsed && (
            <Link href="/dashboard" className="text-lg font-bold tracking-tight text-white">
              OpenPaper
            </Link>
          )}
          {collapsed && (
            <Link href="/dashboard" className="text-lg font-bold text-accent-500">
              OP
            </Link>
          )}
        </div>

        <nav className="flex-1 py-4 space-y-1 px-2">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              onClick={onMobileClose}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                pathname.startsWith(item.href)
                  ? "bg-accent-500/10 text-accent-400"
                  : "text-muted-foreground hover:text-foreground hover:bg-white/5",
                collapsed && "justify-center px-2"
              )}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          ))}
        </nav>

        <div className="p-2 border-t border-border">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className={cn("w-full", collapsed ? "justify-center" : "justify-between")}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <>Collapse <ChevronLeft className="h-4 w-4" /></>}
          </Button>
        </div>
      </aside>
    </>
  )
}
