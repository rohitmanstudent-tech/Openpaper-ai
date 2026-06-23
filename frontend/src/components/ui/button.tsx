import { forwardRef, ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

const variants = {
  primary: "bg-accent-500 hover:bg-accent-600 text-white shadow-sm",
  secondary: "bg-base-800 hover:bg-base-700 text-base-200 border border-base-700/50",
  ghost: "hover:bg-base-800 text-base-400 hover:text-base-200",
  danger: "bg-red-600 hover:bg-red-700 text-white",
  outline: "border border-accent-500/30 text-accent-400 hover:bg-accent-500/10",
};

const sizes = {
  sm: "px-2.5 py-1 text-xs",
  md: "px-3 py-1.5 text-sm",
  lg: "px-4 py-2 text-sm",
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof variants;
  size?: keyof typeof sizes;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", loading, disabled, children, ...props }, ref) => {
    return (
      <button ref={ref} disabled={disabled || loading}
        className={cn(
          "inline-flex items-center justify-center rounded-md font-medium transition-all duration-150",
          "focus:outline-none focus:ring-2 focus:ring-accent-500/30",
          "disabled:opacity-40 disabled:cursor-not-allowed",
          variants[variant], sizes[size], className
        )} {...props}>
        {loading && (
          <svg className="animate-spin -ml-1 mr-1.5 h-3.5 w-3.5" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        )}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";
