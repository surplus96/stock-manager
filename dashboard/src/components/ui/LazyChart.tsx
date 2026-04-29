/**
 * LazyChart — defer Recharts client bundle via next/dynamic (FR-F06).
 *
 * Pages still author their chart composition normally by passing a render
 * function; the Recharts import lives only in the dynamically-loaded module,
 * so initial route JS no longer pays the Recharts cost.
 *
 * Usage::
 *
 *   <LazyChart render={(R) => (
 *     <R.ResponsiveContainer width="100%" height={240}>
 *       <R.LineChart data={data}>...</R.LineChart>
 *     </R.ResponsiveContainer>
 *   )} />
 */
"use client";

import dynamic from "next/dynamic";
import type { ComponentType, ReactNode } from "react";

import { Skeleton } from "./Skeleton";

type RechartsNamespace = typeof import("recharts");
type ChartRender = (R: RechartsNamespace) => ReactNode;

interface LazyChartProps {
  render: ChartRender;
  height?: number;
}

const DynamicRechartsHost: ComponentType<LazyChartProps> = dynamic(
  async () => {
    const recharts = await import("recharts");
    const Host = ({ render }: LazyChartProps) => <>{render(recharts)}</>;
    Host.displayName = "LazyChartHost";
    return Host;
  },
  {
    ssr: false,
    loading: () => <Skeleton className="h-60 w-full" />,
  },
);

export function LazyChart(props: LazyChartProps) {
  return <DynamicRechartsHost {...props} />;
}
