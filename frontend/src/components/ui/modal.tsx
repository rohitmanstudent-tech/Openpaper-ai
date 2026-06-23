"use client";

import { useEffect, ReactNode } from "react";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
}

export function Modal({ open, onClose, title, children, className }: ModalProps) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className={cn(
        "relative w-full max-w-lg animate-fade-in rounded-lg border border-base-700/50 bg-base-900 p-6 shadow-xl",
        className
      )}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-base font-semibold text-base-100">{title}</h2>
          <button onClick={onClose} className="rounded p-1 text-base-500 transition-colors hover:text-base-300 hover:bg-base-800">
            <X size={16} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
