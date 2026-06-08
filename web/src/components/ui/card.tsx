export function Card({ title, children, className = "" }: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`bg-[--color-card-bg] border border-[--color-card-border] rounded-lg p-4 ${className}`}>
      {title && <h3 className="text-sm font-semibold text-[--color-text-secondary] mb-3 uppercase tracking-wide">{title}</h3>}
      {children}
    </div>
  );
}

export function StatCard({ label, value, subtitle = "", trend = "" }: {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
}) {
  const isPositive = trend.startsWith("+");
  const isNegative = trend.startsWith("-");

  return (
    <Card>
      <div className="flex flex-col gap-1">
        <span className="text-xs text-[--color-text-secondary] uppercase">{label}</span>
        <span className="text-2xl font-bold">{value}</span>
        {subtitle && <span className="text-xs text-[--color-text-secondary]">{subtitle}</span>}
        {trend && (
          <span className={`text-xs ${isPositive ? "text-[--color-profit]" : isNegative ? "text-[--color-loss]" : "text-[--color-text-secondary]"}`}>
            {trend}
          </span>
        )}
      </div>
    </Card>
  );
}

export function Badge({ label, variant = "default" }: { label: string; variant?: "default" | "success" | "danger" | "warning" }) {
  const colors = {
    default: "bg-gray-700 text-gray-300",
    success: "bg-green-900/50 text-green-400",
    danger: "bg-red-900/50 text-red-400",
    warning: "bg-yellow-900/50 text-yellow-400",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${colors[variant]}`}>
      {label}
    </span>
  );
}
