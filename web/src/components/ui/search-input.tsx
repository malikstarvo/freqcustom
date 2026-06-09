import { useState, useEffect } from "react";
import { Search, X } from "lucide-react";
import { cn } from "@/lib/utils";

export function SearchInput({ value, onChange, placeholder = "Search…", className = "" }: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  className?: string;
}) {
  const [local, setLocal] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => onChange(local), 300);
    return () => clearTimeout(timer);
  }, [local, onChange]);

  return (
    <div className={cn("relative flex items-center", className)}>
      <Search size={15} className="absolute left-3 text-muted-foreground pointer-events-none" aria-hidden="true" />
      <input
        type="text"
        value={local}
        onChange={(e) => setLocal(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-8 h-9 rounded-lg bg-secondary/80 border border-border/60 text-xs text-foreground placeholder-muted-foreground motion-safe:transition-colors focus-visible:outline-none focus-visible:border-primary/80 focus-visible:bg-background"
      />
      {local && (
        <button
          onClick={() => setLocal("")}
          className="absolute right-3 text-muted-foreground hover:text-foreground transition-colors p-0.5 rounded"
          aria-label="Clear search"
        >
          <X size={12} aria-hidden="true" />
        </button>
      )}
    </div>
  );
}
