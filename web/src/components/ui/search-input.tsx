import { useState, useEffect } from "react";
import { Search, X } from "lucide-react";
import { cn } from "@/lib/utils";

export function SearchInput({ value, onChange, placeholder = "Search...", className = "" }: {
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
      <Search size={15} className="absolute left-3 text-muted-foreground pointer-events-none" />
      <input
        type="text"
        value={local}
        onChange={(e) => setLocal(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-8 h-9 rounded-lg bg-secondary/80 border border-border/60 text-xs text-foreground placeholder-muted-foreground transition-all focus:outline-none focus:border-primary/80 focus:bg-background"
      />
      {local && (
        <button
          onClick={() => setLocal("")}
          className="absolute right-3 text-muted-foreground hover:text-foreground transition-colors p-0.5 rounded"
        >
          <X size={12} />
        </button>
      )}
    </div>
  );
}
