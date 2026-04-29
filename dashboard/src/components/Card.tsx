import { ReactNode } from "react";

interface CardProps {
  title?: string;
  children: ReactNode;
  className?: string;
  action?: ReactNode;
}

export default function Card({ title, children, className = "", action }: CardProps) {
  return (
    <div
      className={`rounded-xl border bg-white dark:bg-slate-900 ${className}`}
      style={{ borderColor: "var(--border)", boxShadow: "var(--shadow-card)" }}
    >
      {title && (
        <div
          className="flex items-center justify-between px-5 py-3 border-b"
          style={{ borderColor: "var(--border)" }}
        >
          {/* FR-PSP-T01 — display serif on card titles */}
          <h3 className="font-display text-base font-semibold text-slate-900 dark:text-slate-50">{title}</h3>
          {action}
        </div>
      )}
      <div className="p-5 text-slate-900 dark:text-slate-50">{children}</div>
    </div>
  );
}
