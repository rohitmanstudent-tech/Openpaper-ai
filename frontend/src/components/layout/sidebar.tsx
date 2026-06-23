"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  Brain,
  CheckSquare,
  Settings,
  LogOut,
  ChevronLeft,
  Radio,
  Swords,
  Workflow,
  Library,
  BarChart3,
  Share2,
  Store,
  PanelRightOpen,
  PanelRightClose,
} from "lucide-react";
import { useState } from "react";

const primaryNav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/dashboard/agents", label: "Agents", icon: Bot },
  { href: "/dashboard/chat", label: "Chat", icon: MessageSquare },
];

const workspaceNav = [
  { href: "/dashboard/workflows", label: "Workflows", icon: Workflow },
  { href: "/dashboard/knowledge", label: "Knowledge", icon: Library },
  { href: "/dashboard/memory", label: "Memory", icon: Brain },
  { href: "/dashboard/tasks", label: "Tasks", icon: CheckSquare },
];

const aiNav = [
  { href: "/dashboard/provider-center", label: "Providers", icon: Radio },
  { href: "/dashboard/model-battle", label: "Model Battle", icon: Swords },
  { href: "/dashboard/cost-analytics", label: "Cost Analytics", icon: BarChart3 },
  { href: "/dashboard/agent-graph", label: "Agent Graph", icon: Share2 },
  { href: "/dashboard/marketplace", label: "Marketplace", icon: Store },
];

const bottomNav = [
  { href: "/dashboard/settings", label: "Settings", icon: Settings },
];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
  onMobileClose?: () => void;
}

function NavSection({ items, collapsed, label }: { items: typeof primaryNav; collapsed: boolean; label?: string }) {
  const pathname = usePathname();

  return (
    <div className="space-y-0.5">
      {label && !collapsed && (
        <p className="px-3 pb-1 pt-3 text-[11px] font-medium uppercase tracking-widest text-base-500">{label}</p>
      )}
      {items.map((item) => {
        const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-all",
              isActive
                ? "nav-active"
                : "nav-inactive",
              collapsed && "justify-center px-0"
            )}
            title={collapsed ? item.label : undefined}
          >
            <item.icon size={18} className={cn("shrink-0", isActive ? "text-accent-400" : "text-base-400")} />
            {!collapsed && <span>{item.label}</span>}
          </Link>
        );
      })}
    </div>
  );
}

export function Sidebar({ collapsed, onToggle, onMobileClose }: SidebarProps) {
  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  };

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-base-700/50 bg-base-900 transition-all duration-200",
        collapsed ? "w-[56px]" : "w-[240px]"
      )}
    >
      <div className={cn(
        "flex h-12 items-center border-b border-base-700/50",
        collapsed ? "justify-center" : "justify-between px-3"
      )}>
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-accent-500">
              <span className="text-[10px] font-bold text-white">OA</span>
            </div>
            <span className="text-sm font-semibold text-base-100">OpenPaper</span>
          </Link>
        )}
        {collapsed && (
          <Link href="/dashboard">
            <div className="flex h-7 w-7 items-center justify-center rounded bg-accent-500">
              <span className="text-[10px] font-bold text-white">OA</span>
            </div>
          </Link>
        )}
        <button
          onClick={onToggle}
          className={cn(
            "rounded p-1 text-base-500 transition-colors hover:text-base-300",
            collapsed && "hidden"
          )}
        >
          <ChevronLeft size={14} />
        </button>
      </div>

      <nav className="flex-1 space-y-3 overflow-y-auto px-2 py-3">
        <NavSection items={primaryNav} collapsed={collapsed} />
        <div className="border-t border-base-700/30" />
        <NavSection items={workspaceNav} collapsed={collapsed} label="Workspace" />
        <div className="border-t border-base-700/30" />
        <NavSection items={aiNav} collapsed={collapsed} label="AI" />
      </nav>

      <div className="border-t border-base-700/50 p-2">
        <button
          onClick={onToggle}
          className={cn(
            "flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-base-500 transition-all hover:text-base-300 hover:bg-base-800/50",
            collapsed && "justify-center px-0"
          )}
          title="Collapse sidebar"
        >
          <PanelRightClose size={18} />
          {!collapsed && <span>Collapse</span>}
        </button>
        <button
          onClick={handleLogout}
          className={cn(
            "flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-base-500 transition-all hover:text-red-400 hover:bg-base-800/50",
            collapsed && "justify-center px-0"
          )}
        >
          <LogOut size={18} />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  );
}
