"use client";

import type { FactorBulletItem } from "@/lib/reportBlocks";

function scoreColor(score: number): string {
  if (score >= 70) return "var(--chart-pos)";
  if (score >= 45) return "var(--chart-accent)";
  if (score >= 30) return "#f59e0b";
  return "var(--chart-neg)";
}

export default function FactorBulletBlock({ factors }: { factors: FactorBulletItem[] }) {
  if (!factors || factors.length === 0) return null;
  return (
    <div
      className="rounded-xl border bg-white dark:bg-slate-900 p-4 space-y-3"
      style={{ borderColor: "var(--border)" }}
    >
      <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-50">팩터 점수</h4>
      <ul className="space-y-2">
        {factors.map((f, i) => {
          const score = Math.max(0, Math.min(100, Number(f.score) || 0));
          const color = scoreColor(score);
          return (
            <li key={`${f.name}-${i}`} className="text-xs">
              <div className="flex items-baseline justify-between">
                <span className="font-medium text-slate-700 dark:text-slate-200">
                  {f.name}
                </span>
                <span className="tabular text-slate-900 dark:text-slate-50">
                  {score.toFixed(0)}
                </span>
              </div>
              <div
                className="mt-1 h-1.5 rounded-full overflow-hidden"
                style={{ backgroundColor: "var(--chart-grid)" }}
              >
                <div
                  className="h-full rounded-full transition-[width] duration-500 ease-out"
                  style={{ width: `${score}%`, backgroundColor: color }}
                />
              </div>
              {f.note && (
                <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400">
                  {f.note}
                </p>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
