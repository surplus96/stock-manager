"use client";

import type { FactorBulletItem } from "@/lib/reportBlocks";
import { LazyChart } from "@/components/ui/LazyChart";

interface RadarMiniBlockProps {
  factors: FactorBulletItem[];
  max?: number;
}

export default function RadarMiniBlock({ factors, max = 100 }: RadarMiniBlockProps) {
  if (!factors || factors.length === 0) return null;
  const data = factors.map((f) => ({ factor: f.name, value: Number(f.score) }));
  return (
    <div
      className="rounded-xl border bg-white dark:bg-slate-900 p-4"
      style={{ borderColor: "var(--border)" }}
    >
      <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-50 mb-2">
        6대 팩터 프로필
      </h4>
      <LazyChart
        height={220}
        render={(R) => (
          <R.ResponsiveContainer width="100%" height={220}>
            <R.RadarChart data={data}>
              <R.PolarGrid stroke="var(--chart-grid)" />
              <R.PolarAngleAxis
                dataKey="factor"
                fontSize={11}
                stroke="var(--chart-axis)"
              />
              <R.PolarRadiusAxis domain={[0, max]} tick={false} stroke="var(--chart-grid)" />
              <R.Radar
                dataKey="value"
                stroke="var(--chart-accent)"
                fill="var(--chart-accent)"
                fillOpacity={0.22}
                strokeWidth={2}
                isAnimationActive
              />
            </R.RadarChart>
          </R.ResponsiveContainer>
        )}
      />
    </div>
  );
}
