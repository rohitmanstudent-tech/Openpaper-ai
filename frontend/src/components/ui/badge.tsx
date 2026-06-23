import { cn } from "@/lib/utils";

const variants: Record<string, string> = {
  idle: "bg-base-700 text-base-300",
  working: "bg-emerald-500/15 text-emerald-400",
  paused: "bg-amber-500/15 text-amber-400",
  error: "bg-red-500/15 text-red-400",
  completed: "bg-emerald-500/15 text-emerald-400",
  pending: "bg-base-700 text-base-400",
  in_progress: "bg-accent-500/15 text-accent-400",
  failed: "bg-red-500/15 text-red-400",
  cancelled: "bg-base-700 text-base-400",
  low: "bg-base-700 text-base-400",
  medium: "bg-amber-500/15 text-amber-400",
  high: "bg-orange-500/15 text-orange-400",
  critical: "bg-red-500/15 text-red-400",
  active: "bg-emerald-500/15 text-emerald-400",
  inactive: "bg-base-700 text-base-400",
  admin: "bg-purple-500/15 text-purple-400",
  manager: "bg-accent-500/15 text-accent-400",
  member: "bg-emerald-500/15 text-emerald-400",
  viewer: "bg-base-700 text-base-400",
};

interface BadgeProps {
  variant?: string;
  children: React.ReactNode;
  className?: string;
}

export function Badge({ variant = "idle", children, className }: BadgeProps) {
  return (
    <span className={cn(
      "inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium",
      variants[variant] || variants.idle,
      className
    )}>
      {children}
    </span>
  );
}
