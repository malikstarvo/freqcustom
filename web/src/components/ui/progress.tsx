import { cn } from "@/lib/utils";

export function Progress({ value, max = 100, className = "" }: {
  value: number;
  max?: number;
  className?: string;
}) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  return (
    <div className={cn("w-full h-2 bg-secondary rounded-full overflow-hidden border border-border/20", className)}>
      <div
        className="h-full bg-gradient-to-r from-primary to-primary/80 rounded-full motion-safe:transition-[width] duration-500 ease-out shadow-[0_0_8px_rgba(var(--primary),0.5)]"
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}
