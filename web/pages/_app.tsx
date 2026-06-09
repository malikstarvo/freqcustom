import type { AppProps } from "next/app";
import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { ThemeProvider, useTheme } from "@/hooks/useTheme";
import { ToastProvider } from "@/hooks/useToast";
import { Toaster } from "@/components/ui/sonner";
import {
  LayoutDashboard, BarChart3, Wallet, ArrowRightLeft,
  Activity, FileText, Settings, Server, Cpu,
  DollarSign, Brain, Globe, Database, Sparkles, Eye, Radio,
  Menu, X, Sun, Moon, Power, ShieldCheck
} from "lucide-react";
import "@/index.css";

const navItems = [
  {
    group: "Overview",
    items: [
      { path: "/overview", label: "Overview", icon: Eye },
      { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    ]
  },
  {
    group: "Trading Operations",
    items: [
      { path: "/trading", label: "Live Trading", icon: Activity },
      { path: "/trades", label: "Trades History", icon: ArrowRightLeft },
      { path: "/balance", label: "Balances", icon: Wallet },
      { path: "/paper", label: "Paper Trading", icon: DollarSign },
    ]
  },
  {
    group: "AI & Market Data",
    items: [
      { path: "/market", label: "Market Data", icon: Globe },
      { path: "/collector", label: "Data Collector", icon: Radio },
      { path: "/data-quality", label: "Data Quality", icon: Database },
      { path: "/features", label: "AI Features", icon: Sparkles },
      { path: "/model", label: "ML Models", icon: Brain },
    ]
  },
  {
    group: "System & Tools",
    items: [
      { path: "/backtest", label: "Backtesting", icon: BarChart3 },
      { path: "/logs", label: "Bot Logs", icon: FileText },
      { path: "/config", label: "Configuration", icon: Settings },
      { path: "/system", label: "System Status", icon: Server },
    ]
  }
];

function AppContent({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const { theme, toggle } = useTheme();
  const [status, setStatus] = useState<string>("connecting");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
    fetch(`${apiBase}/ping`)
      .then(r => r.json())
      .then(d => setStatus(d.status === "pong" ? "live" : "error"))
      .catch(() => setStatus("offline"));
  }, []);

  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans relative">
      {/* Decorative ambient glows in background (Dark mode only) */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none opacity-0 dark:opacity-100 transition-opacity duration-1000" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-profit/5 rounded-full blur-[150px] pointer-events-none opacity-0 dark:opacity-100 transition-opacity duration-1000" />

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden transition-all duration-300" onClick={closeSidebar} />
      )}

      {/* Sidebar Navigation */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-card border-r border-border/60 flex flex-col transition-all duration-300 lg:translate-x-0 ${
        sidebarOpen ? "translate-x-0 shadow-2xl" : "-translate-x-full"
      }`}>
        {/* Brand header */}
        <div className="h-16 px-6 border-b border-border/60 flex items-center justify-between bg-card/50 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg text-primary">
              <Cpu size={20} className="animate-pulse" />
            </div>
            <div>
              <h1 className="font-bold text-sm leading-none tracking-tight">FreqTrade Custom</h1>
              <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">Dashboard Client</span>
            </div>
          </div>
          <button onClick={closeSidebar} className="lg:hidden p-1.5 rounded-md text-muted-foreground hover:text-foreground hover:bg-secondary transition-all">
            <X size={16} />
          </button>
        </div>

        {/* Navigation items grouped */}
        <nav className="flex-1 py-6 px-4 space-y-6 overflow-y-auto scrollbar-thin">
          {navItems.map((group) => (
            <div key={group.group} className="space-y-2">
              <h3 className="px-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider select-none">
                {group.group}
              </h3>
              <div className="space-y-0.5">
                {group.items.map(({ path, label, icon: Icon }) => {
                  const isActive = router.pathname === path;
                  return (
                    <Link
                      key={path}
                      href={path}
                      onClick={closeSidebar}
                      className={`flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-all group ${
                        isActive
                          ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                          : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                      }`}
                    >
                      <Icon size={16} className={`shrink-0 transition-transform duration-200 group-hover:scale-110 ${
                        isActive ? "text-primary-foreground" : "text-muted-foreground group-hover:text-foreground"
                      }`} />
                      <span>{label}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-border/60 bg-card/50 backdrop-blur-md flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck size={14} className="text-muted-foreground" />
            <span className="text-[10px] text-muted-foreground font-medium">Freqtrade AI v1.0.0</span>
          </div>
          <button
            onClick={toggle}
            className="p-2 rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-all"
            title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? <Sun size={14} /> : <Moon size={14} />}
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top Header */}
        <header className="h-16 border-b border-border/60 px-6 flex items-center justify-between bg-card/30 backdrop-blur-md shrink-0">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground transition-all"
            >
              <Menu size={18} />
            </button>
            
            {/* Page title context */}
            <div className="hidden sm:flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Bot Status:</span>
              <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border border-border bg-background/50">
                <span className={`w-2 h-2 rounded-full ${
                  status === "live" ? "bg-profit animate-pulse" : status === "connecting" ? "bg-warning animate-bounce" : "bg-loss"
                }`} />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{status}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick API status badge for mobile */}
            <div className="sm:hidden flex items-center gap-1.5 px-2 py-0.5 rounded-full border border-border bg-background/50">
              <span className={`w-1.5 h-1.5 rounded-full ${status === "live" ? "bg-profit animate-pulse" : "bg-loss"}`} />
              <span className="text-[9px] font-semibold uppercase text-muted-foreground">{status}</span>
            </div>

            {/* Power Button or connection details */}
            <div className="p-2 bg-secondary/80 rounded-lg text-muted-foreground border border-border/40 text-xs font-semibold select-none">
              API Connection Live
            </div>
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8 scrollbar-thin">
          <div className="max-w-[1600px] mx-auto w-full space-y-6">
            <Component {...pageProps} />
          </div>
        </main>
      </div>
    </div>
  );
}

export default function App(props: AppProps) {
  return (
    <ThemeProvider>
      <ToastProvider>
        <AppContent {...props} />
        <Toaster />
      </ToastProvider>
    </ThemeProvider>
  );
}
