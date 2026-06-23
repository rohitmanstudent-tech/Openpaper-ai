"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, LayoutDashboard } from "lucide-react";
import { cn } from "@/lib/utils";

const labelMap: Record<string, string> = {
  "dashboard": "Dashboard",
  "agents": "Agents",
  "chat": "Chat",
  "memory": "Memory",
  "tasks": "Tasks",
  "settings": "Settings",
  "provider-center": "Provider Center",
  "model-battle": "Model Battle",
  "workflows": "Workflows",
  "knowledge": "Knowledge Base",
  "cost-analytics": "Cost Analytics",
  "agent-graph": "Agent Graph",
  "marketplace": "Marketplace",
};

export function Breadcrumbs() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length <= 1) return null;

  return (
    <nav className="flex items-center gap-1.5 text-xs text-base-500">
      <Link href="/dashboard" className="transition-colors hover:text-base-300">
        <LayoutDashboard size={12} />
      </Link>
      {segments.slice(1).map((segment, index) => {
        const href = "/" + segments.slice(0, segments.indexOf(segment) + 1).join("/");
        const label = labelMap[segment] || segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, " ");
        const isLast = index === segments.slice(1).length - 1;
        return (
          <span key={href} className="flex items-center gap-1.5">
            <ChevronRight size={10} />
            {isLast ? (
              <span className="text-base-300">{label}</span>
            ) : (
              <Link href={href} className="transition-colors hover:text-base-300">
                {label}
              </Link>
            )}
          </span>
        );
      })}
    </nav>
  );
}
