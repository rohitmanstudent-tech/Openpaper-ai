"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { usePathname } from "next/navigation";
import { Sidebar } from "./sidebar";
import { Breadcrumbs } from "./breadcrumbs";
import { getToken } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Menu, X } from "lucide-react";

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [loaded, setLoaded] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const token = getToken();
    if (!token) {
      router.push("/login");
    } else {
      setLoaded(true);
    }
  }, [router]);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  if (!loaded) {
    return (
      <div className="flex h-screen items-center justify-center bg-base-950">
        <div className="h-5 w-5 animate-spin rounded-full border border-accent-500 border-t-transparent" />
      </div>
    );
  }

  const pageTitle = pathname.split("/").pop()?.replace(/-/g, " ") || "Dashboard";

  return (
    <div className="flex h-screen bg-base-950">
      {/* Desktop sidebar */}
      <div className={cn("hidden md:flex", collapsed ? "w-[56px]" : "w-[240px]")}>
        <Sidebar collapsed={collapsed} onToggle={() => setCollapsed(!collapsed)} />
      </div>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="absolute left-0 top-0 h-full animate-slide-in">
            <Sidebar collapsed={false} onToggle={() => setMobileOpen(false)} onMobileClose={() => setMobileOpen(false)} />
          </div>
        </div>
      )}

      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar */}
        <header className="flex h-12 items-center gap-3 border-b border-base-700/50 px-4">
          <button
            onClick={() => setMobileOpen(true)}
            className="rounded p-1 text-base-400 hover:text-base-200 md:hidden"
          >
            <Menu size={18} />
          </button>
          <Breadcrumbs />
          <div className="flex-1" />
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-accent-500/20 text-[11px] font-medium text-accent-400">
              U
            </div>
          </div>
        </header>

        {/* Page content */}
        <div className="flex-1 overflow-auto">
          <div className="mx-auto w-full max-w-[1400px] px-6 py-6">
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
