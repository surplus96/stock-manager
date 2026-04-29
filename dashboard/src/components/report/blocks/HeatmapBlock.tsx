"use client";

/**
 * HeatmapBlock — CSS-grid SVG-free heatmap (correlation / generic heat).
 *
 * Using a grid of coloured boxes rather than a Recharts chart lets us
 * support arbitrary N×N matrices with annotations while staying small
 * and responsive. For correlation mode the scale clamps to [-1, 1] and
 * uses a diverging red/blue palette; heat mode uses [min, max] linear.
 */

interface HeatmapBlockProps {
  xs: string[];
  ys: string[];
  matrix: number[][];
  scale?: "correlation" | "heat";
}

function correlationColor(v: number): string {
  const c = Math.max(-1, Math.min(1, v));
  if (c >= 0) {
    // blue gradient 0→1
    const alpha = c.toFixed(2);
    return `rgba(59, 130, 246, ${alpha})`;
  }
  const alpha = Math.abs(c).toFixed(2);
  return `rgba(239, 68, 68, ${alpha})`;
}

function heatColor(v: number, min: number, max: number): string {
  if (max === min) return "rgba(59, 130, 246, 0.3)";
  const t = (v - min) / (max - min);
  const alpha = Math.max(0.05, Math.min(1, t)).toFixed(2);
  return `rgba(59, 130, 246, ${alpha})`;
}

export default function HeatmapBlock({
  xs,
  ys,
  matrix,
  scale = "correlation",
}: HeatmapBlockProps) {
  if (!xs.length || !ys.length || !matrix.length) return null;
  const flat = matrix.flat();
  const min = Math.min(...flat);
  const max = Math.max(...flat);
  const cols = xs.length;
  return (
    <div
      className="rounded-xl border bg-white dark:bg-slate-900 p-4 overflow-x-auto"
      style={{ borderColor: "var(--border)" }}
    >
      <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-50 mb-2">
        {scale === "correlation" ? "상관관계" : "히트맵"}
      </h4>
      <div
        className="inline-grid gap-0.5"
        style={{ gridTemplateColumns: `80px repeat(${cols}, 48px)` }}
      >
        <div />
        {xs.map((x) => (
          <div
            key={x}
            className="text-[10px] text-slate-500 dark:text-slate-400 text-center truncate"
            title={x}
          >
            {x}
          </div>
        ))}
        {ys.map((y, rowIdx) => (
          <div key={y} style={{ display: "contents" }}>
            <div
              className="text-[10px] text-slate-600 dark:text-slate-300 text-right pr-1 truncate tabular"
              title={y}
            >
              {y}
            </div>
            {matrix[rowIdx]?.map((v, colIdx) => {
              const bg =
                scale === "correlation" ? correlationColor(v) : heatColor(v, min, max);
              return (
                <div
                  key={`${y}-${colIdx}`}
                  className="relative h-8 flex items-center justify-center rounded-sm text-[10px] tabular font-medium"
                  style={{ backgroundColor: bg, color: "#0f172a" }}
                  title={`${y} × ${xs[colIdx]}: ${v.toFixed(2)}`}
                >
                  {v.toFixed(2)}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
