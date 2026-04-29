/**
 * AsyncBoundary — standardize loading / error / data states (FR-F10).
 *
 * Wraps a piece of UI with a unified pattern so every feature shows loading
 * and error states the same way.
 */
"use client";

import type { ReactNode } from "react";

interface AsyncBoundaryProps {
  loading: boolean;
  error?: string | null;
  loadingFallback: ReactNode;
  onRetry?: () => void;
  children: ReactNode;
}

export function AsyncBoundary({
  loading,
  error,
  loadingFallback,
  onRetry,
  children,
}: AsyncBoundaryProps) {
  if (loading) {
    return <>{loadingFallback}</>;
  }
  if (error) {
    return (
      <div
        role="alert"
        aria-live="assertive"
        className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700"
      >
        <p className="font-semibold">요청 처리 중 오류가 발생했습니다.</p>
        <p className="mt-1">{error}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 rounded-md border border-red-300 bg-white dark:bg-slate-900 px-3 py-1.5 text-xs font-medium text-red-700 hover:bg-red-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500 focus-visible:ring-offset-2"
          >
            다시 시도
          </button>
        )}
      </div>
    );
  }
  return <>{children}</>;
}
