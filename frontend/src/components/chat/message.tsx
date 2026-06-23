"use client";

import { cn } from "@/lib/utils";
import { Bot, User } from "lucide-react";

interface MessageProps {
  role: "user" | "agent";
  content: string;
  timestamp?: string;
  isStreaming?: boolean;
}

export function Message({ role, content, timestamp, isStreaming }: MessageProps) {
  return (
    <div className={cn(
      "flex gap-3 animate-fade-in",
      role === "user" ? "justify-end" : "justify-start"
    )}>
      {role === "agent" && (
        <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-lg bg-accent-500/10">
          <Bot size={14} className="text-accent-400" />
        </div>
      )}
      <div className={cn(
        "max-w-[70%] rounded-lg px-4 py-2.5",
        role === "user"
          ? "bg-accent-500/10 border border-accent-500/20"
          : "bg-base-800/60 border border-base-700/30"
      )}>
        <p className="text-sm text-base-200 leading-relaxed whitespace-pre-wrap">
          {content}
          {isStreaming && <span className="inline-block w-1.5 h-4 bg-accent-400 ml-0.5 animate-pulse-subtle" />}
        </p>
        {timestamp && (
          <p className="mt-1 text-[11px] text-base-500">{timestamp}</p>
        )}
      </div>
      {role === "user" && (
        <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-lg bg-base-800">
          <User size={14} className="text-base-400" />
        </div>
      )}
    </div>
  );
}
