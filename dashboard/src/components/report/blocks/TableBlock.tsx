"use client";

import { useMemo, useState } from "react";
import type { TableColumn } from "@/lib/reportBlocks";

interface TableBlockProps {
  columns: TableColumn[];
  rows: Record<string, unknown>[];
  caption?: string;
}

function formatValue(value: unknown, col: TableColumn): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") {
    switch (col.format) {
      case "percent":
        return `${(value * 100).toFixed(2)}%`;
      case "currency":
        return value.toLocaleString();
      case "compact":
        return new Intl.NumberFormat(undefined, { notation: "compact" }).format(value);
      case "integer":
        return value.toFixed(0);
      default:
        return col.numeric ? value.toFixed(2) : String(value);
    }
  }
  return String(value);
}

export default function TableBlock({ columns, rows, caption }: TableBlockProps) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const sorted = useMemo(() => {
    if (!sortKey) return rows;
    const copy = [...rows];
    copy.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av;
      }
      return sortDir === "asc"
        ? String(av ?? "").localeCompare(String(bv ?? ""))
        : String(bv ?? "").localeCompare(String(av ?? ""));
    });
    return copy;
  }, [rows, sortKey, sortDir]);

  function toggleSort(key: string) {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <div
      className="rounded-xl border bg-white dark:bg-slate-900 overflow-hidden"
      style={{ borderColor: "var(--border)" }}
    >
      {caption && (
        <div className="px-4 py-2 text-xs text-slate-500 dark:text-slate-400 border-b" style={{ borderColor: "var(--border)" }}>
          {caption}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr
              className="text-slate-600 dark:text-slate-300 border-b"
              style={{ borderColor: "var(--border)" }}
            >
              {columns.map((c) => (
                <th
                  key={c.key}
                  className={`px-3 py-2 font-medium ${c.numeric ? "text-right tabular" : "text-left"} cursor-pointer select-none`}
                  onClick={() => toggleSort(c.key)}
                  aria-sort={
                    sortKey === c.key
                      ? sortDir === "asc"
                        ? "ascending"
                        : "descending"
                      : "none"
                  }
                >
                  {c.label}
                  {sortKey === c.key && (
                    <span className="ml-1 opacity-60">{sortDir === "asc" ? "▲" : "▼"}</span>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((r, i) => (
              <tr
                key={i}
                className="border-b last:border-b-0 hover:bg-slate-50 dark:hover:bg-slate-800"
                style={{ borderColor: "var(--border)" }}
              >
                {columns.map((c) => (
                  <td
                    key={c.key}
                    className={`px-3 py-2 ${c.numeric ? "text-right tabular text-slate-900 dark:text-slate-50" : "text-slate-800 dark:text-slate-100"}`}
                  >
                    {formatValue(r[c.key], c)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
