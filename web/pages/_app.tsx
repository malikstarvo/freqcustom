import type { AppProps } from "next/app";
import Head from "next/head";
import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { ThemeProvider, useTheme } from "@/hooks/useTheme";
import { ToastProvider } from "@/hooks/useToast";
import { Toaster } from "@/components/ui/sonner";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Button } from "@/components/ui/button";
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
  const [status, setStatus] = useState<string>("Connecting…");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
    fetch(`${apiBase}/ping`)
      .then(r => r.json())
      .then(d => setStatus(d.status === "pong" ? "Live" : "Error"))
      .catch(() => setStatus("Offline"));
  }, []);

  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans relative" suppressHydrationWarning>
      <Head>
        <title>FreqTrade Dashboard</title>
        <meta name="description" content="FreqTrade AI Trading Dashboard" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="oklch(0.09 0.01 250)" media="(prefers-color-scheme: dark)" />
        <meta name="theme-color" content="oklch(0.98 0.005 240)" media="(prefers-color-scheme: light)" />
      </Head>
      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-[100] focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-lg">Skip to content</a>
      {/* Decorative ambient glows in background (Dark mode only) */}
      <div aria-hidden="true" className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none opacity-0 dark:opacity-100 motion-safe:transition-opacity motion-safe:duration-1000" />
      <div aria-hidden="true" className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-profit/5 rounded-full blur-[150px] pointer-events-none opacity-0 dark:opacity-100 motion-safe:transition-opacity motion-safe:duration-1000" />

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <button className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 lg:hidden motion-safe:transition-opacity motion-safe:duration-300 cursor-default" onClick={closeSidebar} aria-label="Close sidebar" />
      )}

      {/* Sidebar Navigation */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-card border-r border-border/60 flex flex-col motion-safe:transition-transform motion-safe:duration-300 lg:translate-x-0 ${
        sidebarOpen ? "translate-x-0 shadow-2xl" : "-translate-x-full"
      }`}>
        {/* Brand header */}
        <div className="h-16 px-4 sm:px-6 border-b border-border/60 flex items-center justify-between bg-card/50 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg text-primary">
              <Cpu size={20} className="motion-safe:animate-pulse" aria-hidden="true" />
            </div>
            <div>
              <h1 className="font-bold text-sm leading-none tracking-tight">FreqTrade Custom</h1>
              <span className="text-[10px] text-muted-foreground font-medium uppercase tracking-wider">Dashboard Client</span>
            </div>
          </div>
            <h2 className="sr-only">FreqTrade Dashboard</h2>
          <Button onClick={closeSidebar} variant="ghost" size="icon-sm" className="lg:hidden" aria-label="Close sidebar">
            <X aria-hidden="true" />
          </Button>
        </div>

        {/* Navigation items grouped */}
        <nav className="flex-1 py-4 sm:py-6 px-3 sm:px-4 flex flex-col gap-5 sm:gap-6  overflow-y-auto scrollbar-thin">
          {navItems.map((group) => (
            <div key={group.group} className="flex flex-col gap-2"> 
              <h3 className="px-2 sm:px-3 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider select-none">
                {group.group}
              </h3>
              <div className="flex flex-col gap-0.5"> 
                {group.items.map(({ path, label, icon: Icon }) => {
                  const isActive = router.pathname === path;
                  return (
                    <Link
                      key={path}
                      href={path}
                      onClick={closeSidebar}
                      className={`flex items-center gap-3 px-2 sm:px-3 py-2 rounded-lg text-xs font-medium motion-safe:transition-colors group ${
                        isActive
                          ? "bg-primary text-primary-foreground shadow-md shadow-primary/20"
                          : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                      }`}
                    >
                      <Icon size={16} aria-hidden="true" className={`shrink-0 motion-safe:transition-transform motion-safe:duration-200 group-hover:scale-110 ${
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
            <ShieldCheck size={14} className="text-muted-foreground" aria-hidden="true" />
            <span className="text-[10px] text-muted-foreground font-medium">Freqtrade AI v1.0.0</span>
          </div>
          <Button
            onClick={toggle}
            variant="ghost"
            size="icon-sm"
            aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
          >
            {theme === "dark" ? <Sun aria-hidden="true" /> : <Moon aria-hidden="true" />}
          </Button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top Header */}
        <header className="h-16 border-b border-border/60 px-4 sm:px-6 flex items-center justify-between bg-card/30 backdrop-blur-md shrink-0">
          <div className="flex items-center gap-4">
            <Button
              onClick={() => setSidebarOpen(true)}
              variant="outline"
              size="icon"
              className="lg:hidden"
              aria-label="Open sidebar"
            >
              <Menu aria-hidden="true" />
            </Button>
            
            {/* Page title context */}
            <div className="hidden sm:flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Bot Status:</span>
              <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full border border-border bg-background/50">
                <span className={`size-2 rounded-full ${
                  status === "Live" ? "bg-profit motion-safe:animate-pulse" : status === "Connecting…" ? "bg-warning motion-safe:animate-bounce" : "bg-loss"
                }`} />
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{status}</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Quick API status badge for mobile */}
            <div className="sm:hidden flex items-center gap-1.5 px-2 py-0.5 rounded-full border border-border bg-background/50">
              <span className={`size-1.5 rounded-full ${status === "Live" ? "bg-profit motion-safe:animate-pulse" : "bg-loss"}`} />
              <span className="text-[9px] font-semibold uppercase text-muted-foreground">{status}</span>
            </div>

            {/* Power Button or connection details */}
            <div className="p-2 bg-secondary/80 rounded-lg text-muted-foreground border border-border/40 text-xs font-semibold select-none">
              API Connection Live
            </div>
          </div>
        </header>

        {/* Content Body */}
        <main id="main-content" className="flex-1 overflow-y-auto p-4 sm:p-5 md:p-6 lg:p-8 scrollbar-thin">
          <div className="max-w-[1600px] mx-auto w-full flex flex-col gap-6"> 
            <ErrorBoundary>
              <Component {...pageProps} />
            </ErrorBoundary>
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
