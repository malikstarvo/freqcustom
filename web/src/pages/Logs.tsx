import { useEffect, useState, useRef } from "react";
import { Card, Badge } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Empty } from "@/components/ui/empty";
import { SearchInput } from "@/components/ui/search-input";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { FileText, ScrollText, AlertTriangle, Info, XCircle } from "lucide-react";

type LogLevel = "ALL" | "INFO" | "WARNING" | "ERROR";

export default function Logs() {
  const [logs, setLogs] = useState<string[][]>([]);
  const [filter, setFilter] = useState<LogLevel>("ALL");
  const [search, setSearch] = useState("");
  const [autoScroll, setAutoScroll] = useState(true);
  const [logCount, setLogCount] = useState(0);
  const [loading, setLoading] = useState(true);
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
    fetchLogs().finally(() => setLoading(false));
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
    if (l.includes("ERROR")) return "text-loss bg-loss/10 border-loss/25";
    if (l.includes("WARN")) return "text-warning bg-warning/10 border-warning/25";
    if (l.includes("INFO")) return "text-primary bg-primary/10 border-primary/25";
    return "text-muted-foreground bg-muted/50 border-border/30";
  };

  const levelIcon = (level: string) => {
    const l = level.toUpperCase();
    if (l.includes("ERROR")) return <XCircle className="size-3.5 text-loss" />;
    if (l.includes("WARN")) return <AlertTriangle className="size-3.5 text-warning" />;
    return <Info className="size-3.5 text-primary" />;
  };

  const filters: LogLevel[] = ["ALL", "INFO", "WARNING", "ERROR"];

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold flex items-center gap-2.5">
          <FileText className="size-5 text-primary" aria-hidden="true" /> Logs
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{logCount} total lines</span>
          <Badge label={`${filtered.length} shown`} variant="default" />
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-3">
        <div className="flex flex-wrap gap-1">
          {filters.map((f) => (
            <Button
              key={f}
              onClick={() => setFilter(f)}
              variant={filter === f ? "default" : "outline"}
              size="sm"
            >
              {f}
            </Button>
          ))}
        </div>
        <SearchInput
          value={search}
          onChange={setSearch}
          placeholder="Search logs\u2026"
          className="flex-1 max-w-md"
        />
        <Button
          onClick={() => setAutoScroll(!autoScroll)}
          variant={autoScroll ? "default" : "outline"}
          size="sm"
        >
          <ScrollText data-icon="inline-start" aria-hidden="true" />
          {autoScroll ? "Auto-scroll ON" : "Auto-scroll OFF"}
        </Button>
      </div>

      <Card title="Bot Logs">
        {loading ? (
          <div className="flex items-center justify-center h-40 text-sm text-muted-foreground">
            Loading logs\u2026
          </div>
        ) : (
          <div
            ref={scrollRef}
            className="overflow-auto max-h-[70vh] font-mono text-xs flex flex-col gap-0.5"
          >
            {filtered.map((entry, i) => {
              const level = entry[1] ?? "";
              const timestamp = entry[0] ?? "";
              const message = entry.slice(2).join(" ");
              return (
                <div
                  key={i}
                  className={cn("flex items-start gap-2 px-2.5 py-2 rounded-lg border", levelColor(level))}
                >
                  {levelIcon(level)}
                  <span className="text-muted-foreground shrink-0 w-20">{timestamp}</span>
                  <span className="font-semibold shrink-0 w-14">{level}</span>
                  <span className="break-all">{message}</span>
                </div>
              );
            })}
            {filtered.length === 0 && (
              <Empty icon={FileText} title="No Logs" description="No logs match your filter" />
            )}
          </div>
        )}
      </Card>
    </div>
  );
}
