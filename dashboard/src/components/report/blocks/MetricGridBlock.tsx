"use client";

import type { MetricItem } from "@/lib/reportBlocks";
import BigNumber from "../inline/BigNumber";
import { Stagger, StaggerItem } from "../inline/Motion";

export default function MetricGridBlock({ items }: { items: MetricItem[] }) {
  if (!items || items.length === 0) return null;
  return (
    <Stagger stepMs={50}>
      <div
        className="grid gap-3"
        style={{
          gridTemplateColumns: `repeat(auto-fit, minmax(140px, 1fr))`,
        }}
      >
        {items.map((m, i) => (
          <StaggerItem key={`${m.label}-${i}`}>
            <div
              className="rounded-xl border bg-white dark:bg-slate-900 p-3"
              style={{ borderColor: "var(--border)" }}
            >
              <BigNumber
                label={m.label}
                value={m.value}
                tone={m.tone}
                delta={m.delta}
                hint={m.hint}
              />
            </div>
          </StaggerItem>
        ))}
      </div>
    </Stagger>
  );
}
