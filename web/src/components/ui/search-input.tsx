import { useState, useEffect } from "react";
import { Search, X } from "lucide-react";

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
    <div className={`relative ${className}`}>
      <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[--color-text-secondary]" />
      <input
        type="text"
        value={local}
        onChange={(e) => setLocal(e.target.value)}
        placeholder={placeholder}
        className="w-full pl-9 pr-8 py-2 bg-[--color-card-bg] border border-[--color-card-border] rounded-lg text-sm text-[--color-text-primary] focus:outline-none focus:border-[--color-accent]"
      />
      {local && (
        <button onClick={() => setLocal("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-[--color-text-secondary] hover:text-[--color-text-primary]">
          <X size={14} />
        </button>
      )}
    </div>
  );
}
