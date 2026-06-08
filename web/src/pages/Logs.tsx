import { useEffect, useState, useRef } from "react";
import { Card, Badge } from "@/components/ui/card";
import { SearchInput } from "@/components/ui/search-input";
import { api } from "@/lib/api";
import { FileText, ScrollText, AlertTriangle, Info, XCircle } from "lucide-react";

type LogLevel = "ALL" | "INFO" | "WARNING" | "ERROR";

export default function Logs() {
  const [logs, setLogs] = useState<string[][]>([]);
  const [filter, setFilter] = useState<LogLevel>("ALL");
  const [search, setSearch] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);
  const [logCount, setLogCount] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  const fetchLogs = async () => {
    try {
      const resp = await api.logs(500);
      setLogs(resp.logs);
      setLogCount(resp.log_count);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const filtered = logs.filter((entry) => {
    const level = entry[1]?.toUpperCase() ?? "";
    if (filter !== "ALL" && level !== filter) return false;
    if (search) {
      const text = entry.slice(1).join(" ").toLowerCase();
      if (!text.includes(search.toLowerCase())) return false;
    }
    return true;
  });

  const levelColor = (level: string) => {
    const l = level.toUpperCase();
    if (l.includes("ERROR")) return "text-[--color-loss] bg-red-950/50 border-red-500/30";
    if (l.includes("WARN")) return "text-[--color-warning] bg-yellow-950/50 border-yellow-500/30";
    if (l.includes("INFO")) return "text-[--color-accent] bg-cyan-950/50 border-cyan-500/30";
    return "text-[--color-text-secondary] bg-gray-800/50 border-gray-700/30";
  };

  const levelIcon = (level: string) => {
    const l = level.toUpperCase();
    if (l.includes("ERROR")) return <XCircle size={12} className="text-[--color-loss]" />;
    if (l.includes("WARN")) return <AlertTriangle size={12} className="text-[--color-warning]" />;
    return <Info size={12} className="text-[--color-accent]" />;
  };

  const filters: LogLevel[] = ["ALL", "INFO", "WARNING", "ERROR"];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2">
          <FileText className="text-[--color-accent]" /> Logs
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[--color-text-secondary]">{logCount} total lines</span>
          <Badge label={`${filtered.length} shown`} variant="default" />
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-col md:flex-row gap-3">
        <div className="flex gap-1">
          {filters.map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filter === f
                  ? "bg-[--color-accent] text-[#0f1119]"
                  : "bg-[--color-card-bg] border border-[--color-card-border] text-[--color-text-secondary] hover:text-[--color-text-primary]"
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search logs..."
          className="flex-1 max-w-md"
        />
        <button
          onClick={() => setAutoScroll(!autoScroll)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            autoScroll
              ? "bg-[--color-accent]/10 text-[--color-accent]"
              : "bg-[--color-card-bg] border border-[--color-card-border] text-[--color-text-secondary]"
          }`}
        >
          <ScrollText size={12} />
          {autoScroll ? "Auto-scroll ON" : "Auto-scroll OFF"}
        </button>
      </div>

      {/* Log List */}
      <Card title="Bot Logs">
        <div
          ref={scrollRef}
          className="overflow-auto max-h-[70vh] font-mono text-xs space-y-0.5"
        >
          {filtered.map((entry, i) => {
            const level = entry[1] ?? "";
            const timestamp = entry[0] ?? "";
            const message = entry.slice(2).join(" ");
            return (
              <div
                key={i}
                className={`flex items-start gap-2 py-1 px-2 rounded border ${levelColor(level)}`}
              >
                {levelIcon(level)}
                <span className="text-[--color-text-secondary] shrink-0 w-20">{timestamp}</span>
                <span className="font-semibold shrink-0 w-14">{level}</span>
                <span className="text-[--color-text-primary] break-all">{message}</span>
              </div>
            );
          })}
          {filtered.length === 0 && (
            <div className="py-8 text-center text-[--color-text-secondary]">
              No logs match your filter
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
