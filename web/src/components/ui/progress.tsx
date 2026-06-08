export function Progress({ value, max = 100, className = "" }: {
  value: number;
  max?: number;
  className?: string;
}) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className={`w-full h-2 bg-[--color-card-border] rounded-full overflow-hidden ${className}`}>
      <div
        className="h-full bg-[--color-accent] rounded-full transition-all duration-300"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
