import type { AppProps } from "next/app";
import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { ThemeProvider } from "@/hooks/useTheme";
import { ToastProvider } from "@/hooks/useToast";
import {
  LayoutDashboard, BarChart3, Wallet, ArrowRightLeft,
  Activity, FileText, Settings, Server, Cpu,
  DollarSign, Brain, Globe, Database, Sparkles, Eye, Radio,
  Menu, X, Sun, Moon
} from "lucide-react";
import "@/index.css";

const navItems = [
  { path: "/overview", label: "Overview", icon: Eye },
  { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/trading", label: "Trading", icon: Activity },
  { path: "/trades", label: "Trades", icon: ArrowRightLeft },
  { path: "/balance", label: "Balance", icon: Wallet },
  { path: "/paper", label: "Paper", icon: DollarSign },
  { path: "/market", label: "Market", icon: Globe },
  { path: "/collector", label: "Collector", icon: Radio },
  { path: "/data-quality", label: "Data Quality", icon: Database },
  { path: "/features", label: "Features", icon: Sparkles },
  { path: "/model", label: "Model", icon: Brain },
  { path: "/backtest", label: "Backtest", icon: BarChart3 },
  { path: "/logs", label: "Logs", icon: FileText },
  { path: "/config", label: "Config", icon: Settings },
  { path: "/system", label: "System", icon: Server },
];

function AppContent({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const [status, setStatus] = useState<string>("connecting");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const saved = localStorage.getItem("freqtrade-theme") as "dark" | "light" | null;
    if (saved) setTheme(saved);
    else setTheme(window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
  }, []);

  useEffect(() => {
    localStorage.setItem("freqtrade-theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
    fetch(`${apiBase}/ping`)
      .then(r => r.json())
      .then(d => setStatus(d.status === "pong" ? "live" : "error"))
      .catch(() => setStatus("offline"));
  }, []);

  const toggle = () => setTheme(t => t === "dark" ? "light" : "dark");
  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="flex h-screen">
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={closeSidebar} />
      )}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-56 bg-[--color-card-bg] border-r border-[--color-card-border] flex flex-col transition-transform duration-200 lg:translate-x-0 ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="p-4 border-b border-[--color-card-border] flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-[--color-accent] flex items-center gap-2">
              <Cpu size={22} /> FreqTrade
            </h1>
            <div className="flex items-center gap-1.5 mt-1">
              <span className={`w-2 h-2 rounded-full ${status === "live" ? "bg-[--color-profit]" : "bg-[--color-loss]"}`} />
              <span className="text-xs text-[--color-text-secondary]">{status}</span>
            </div>
          </div>
          <button onClick={closeSidebar} className="lg:hidden p-1 text-[--color-text-secondary] hover:text-[--color-text-primary]">
            <X size={20} />
          </button>
        </div>
        <nav className="flex-1 py-4 px-2 space-y-1 overflow-y-auto">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link key={path} href={path} onClick={closeSidebar}
              className={`flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${router.pathname === path ? "bg-[--color-accent]/10 text-[--color-accent]" : "text-[--color-text-secondary] hover:bg-gray-800 hover:text-white"}`}>
              <Icon size={18} />{label}
            </Link>
          ))}
        </nav>
        <div className="p-4 border-t border-[--color-card-border] flex items-center justify-between">
          <span className="text-xs text-[--color-text-secondary]">v1.0.0 · Freqtrade + AI</span>
          <button onClick={toggle} className="p-1.5 rounded-md text-[--color-text-secondary] hover:bg-[--color-card-border] hover:text-[--color-text-primary] transition-colors" title={theme === "dark" ? "Switch to light" : "Switch to dark"}>
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-4 lg:p-6 min-w-0">
        <div className="lg:hidden flex items-center gap-3 mb-4">
          <button onClick={() => setSidebarOpen(true)} className="p-2 rounded-md bg-[--color-card-bg] border border-[--color-card-border] text-[--color-text-secondary]">
            <Menu size={20} />
          </button>
          <h1 className="text-lg font-bold text-[--color-accent]">FreqTrade</h1>
          <div className="flex-1" />
          <button onClick={toggle} className="p-2 rounded-md bg-[--color-card-bg] border border-[--color-card-border] text-[--color-text-secondary]">
            {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
          </button>
        </div>
        <Component {...pageProps} />
      </main>
    </div>
  );
}

export default function App(props: AppProps) {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AppContent {...props} />
      </ToastProvider>
    </ThemeProvider>
  );
}
