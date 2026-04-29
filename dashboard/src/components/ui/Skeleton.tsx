/**
 * Skeleton primitives for loading placeholders (FR-F11).
 */
import clsx from "clsx";
import type { HTMLAttributes } from "react";

interface SkeletonProps extends HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export function Skeleton({ className, ...rest }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={clsx("animate-pulse rounded-md bg-slate-200/70", className)}
      {...rest}
    />
  );
}

export function SkeletonText({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={clsx("space-y-2", className)} aria-hidden="true">
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={clsx("h-3", i === lines - 1 ? "w-2/3" : "w-full")}
        />
      ))}
    </div>
  );
}

export function SkeletonReport() {
  return (
    <div className="space-y-4 rounded-xl border border-blue-100 bg-blue-50/40 p-5">
      <Skeleton className="h-5 w-1/3" />
      <SkeletonText lines={4} />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div className="space-y-2 rounded-lg bg-white p-3">
          <Skeleton className="h-4 w-1/2" />
          <SkeletonText lines={3} />
        </div>
        <div className="space-y-2 rounded-lg bg-white p-3">
          <Skeleton className="h-4 w-1/2" />
          <SkeletonText lines={3} />
        </div>
      </div>
    </div>
  );
}
