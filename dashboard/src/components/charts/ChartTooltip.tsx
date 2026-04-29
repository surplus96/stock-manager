"use client";

/**
 * ChartTooltip — shared Recharts tooltip component for rich-visual-reports.
 *
 * Uses CSS palette tokens so light/dark modes swap without extra wiring.
 * Supports multi-value payloads (e.g. candle = open/high/low/close).
 */

import type { ReactNode } from "react";

interface PayloadEntry {
  name?: string | number;
  dataKey?: string | number;
  value?: number | string;
  color?: string;
  payload?: Record<string, unknown>;
}

interface ChartTooltipProps {
  active?: boolean;
  label?: string | number;
  payload?: PayloadEntry[];
  /** Optional formatter per dataKey. Falls back to `${value}`. */
  formatter?: (key: string, value: unknown) => ReactNode;
  /** Optional label formatter (e.g. date). */
  labelFormatter?: (label: string | number | undefined) => ReactNode;
}

export function ChartTooltip({
  active,
  label,
  payload,
  formatter,
  labelFormatter,
}: ChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div
      role="tooltip"
      className="rounded-md px-3 py-2 text-xs shadow-lg tabular"
      style={{
        backgroundColor: "var(--chart-tooltip-bg)",
        color: "var(--chart-tooltip-fg)",
      }}
    >
      {label !== undefined && (
        <div className="font-mono opacity-80 mb-1">
          {labelFormatter ? labelFormatter(label) : String(label)}
        </div>
      )}
      <ul className="space-y-0.5">
        {payload.map((p, i) => {
          const key = String(p.dataKey ?? p.name ?? i);
          const rendered = formatter ? formatter(key, p.value) : String(p.value);
          return (
            <li key={i} className="flex items-center gap-2">
              {p.color && (
                <span
                  aria-hidden="true"
                  className="inline-block w-2 h-2 rounded-full"
                  style={{ backgroundColor: p.color }}
                />
              )}
              <span className="opacity-80">{String(p.name ?? key)}</span>
              <span className="font-semibold">{rendered}</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
