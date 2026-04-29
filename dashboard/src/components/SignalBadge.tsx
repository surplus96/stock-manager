const SIGNAL_COLORS: Record<string, { bg: string; text: string }> = {
  "Strong Buy":  { bg: "bg-emerald-100", text: "text-emerald-700" },
  "Buy":         { bg: "bg-green-100",   text: "text-green-700" },
  "Weak Buy":    { bg: "bg-lime-100",    text: "text-lime-700" },
  "Hold":        { bg: "bg-slate-100 dark:bg-slate-800",   text: "text-slate-700 dark:text-slate-200" },
  "Weak Sell":   { bg: "bg-orange-100",  text: "text-orange-700" },
  "Sell":        { bg: "bg-red-100",     text: "text-red-700" },
  "Strong Sell": { bg: "bg-red-200",     text: "text-red-800" },
};

export default function SignalBadge({ signal }: { signal: string }) {
  const colors = SIGNAL_COLORS[signal] || { bg: "bg-gray-100", text: "text-gray-600" };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${colors.bg} ${colors.text}`}>
      {signal}
    </span>
  );
}
