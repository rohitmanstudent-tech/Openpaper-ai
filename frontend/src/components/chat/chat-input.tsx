"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { Send, Sparkles } from "lucide-react";

interface ChatInputProps {
  onSend: (content: string) => void;
  loading?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, loading, placeholder }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if (!value.trim() || loading) return;
    onSend(value.trim());
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 160) + "px";
    }
  };

  return (
    <div className="relative rounded-lg border border-base-700/50 bg-base-900/80 px-3 py-2.5 transition-colors focus-within:border-accent-500/40">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onInput={handleInput}
        placeholder={placeholder || "Message your agents..."}
        rows={1}
        className="w-full resize-none bg-transparent text-sm text-base-100 placeholder-base-500 outline-none scrollbar-thin"
        disabled={loading}
      />
      <div className="flex items-center justify-between pt-1.5">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-base-500">AI-powered</span>
          <Sparkles size={11} className="text-accent-400" />
        </div>
        <button
          onClick={handleSend}
          disabled={!value.trim() || loading}
          className="flex items-center gap-1.5 rounded-md bg-accent-500 px-2.5 py-1 text-[11px] font-medium text-white transition-colors hover:bg-accent-600 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? (
            <div className="h-3 w-3 animate-spin rounded-full border border-white border-t-transparent" />
          ) : (
            <>
              <Send size={12} />
              Send
            </>
          )}
        </button>
      </div>
    </div>
  );
}
