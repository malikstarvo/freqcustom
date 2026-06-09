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
import { Separator } from "@/components/ui/separator";
import { TooltipProvider } from "@/components/ui/tooltip";
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuItem,
  SidebarMenuButton,
  SidebarTrigger,
  SidebarInset,
  SidebarSeparator,
} from "@/components/ui/sidebar";
import {
  LayoutDashboard, BarChart3, Wallet, ArrowRightLeft,
  Activity, FileText, Settings, Server, Cpu,
  DollarSign, Brain, Globe, Database, Sparkles, Eye, Radio,
  Sun, Moon, ShieldCheck
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
  const [status, setStatus] = useState<string>("Connecting\u2026");

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
    fetch(`${apiBase}/ping`)
      .then(r => r.json())
      .then(d => setStatus(d.status === "pong" ? "Live" : "Error"))
      .catch(() => setStatus("Offline"));
  }, []);

  return (
    <div className="relative flex h-screen w-full overflow-hidden bg-background text-foreground font-sans" suppressHydrationWarning>
      <Head>
        <title>FreqTrade Dashboard</title>
        <meta name="description" content="FreqTrade AI Trading Dashboard" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="oklch(0.09 0.01 250)" media="(prefers-color-scheme: dark)" />
        <meta name="theme-color" content="oklch(0.98 0.005 240)" media="(prefers-color-scheme: light)" />
      </Head>

      <a href="#main-content" className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-[100] focus:px-4 focus:py-2 focus:bg-primary focus:text-primary-foreground focus:rounded-md focus:text-sm">
        Skip to content
      </a>

      {/* Decorative ambient glows */}
      <div aria-hidden="true" className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none opacity-0 dark:opacity-100 motion-safe:transition-opacity motion-safe:duration-1000" />
      <div aria-hidden="true" className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-profit/5 rounded-full blur-[150px] pointer-events-none opacity-0 dark:opacity-100 motion-safe:transition-opacity motion-safe:duration-1000" />

      <TooltipProvider>
        <SidebarProvider defaultOpen>
          {/* ── Sidebar ── */}
          <Sidebar collapsible="icon">
            <SidebarHeader className="gap-3 px-4 py-4">
              <div className="flex items-center gap-3">
                <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Cpu className="size-5 motion-safe:animate-pulse" aria-hidden="true" />
                </div>
                <div className="flex flex-col gap-0.5">
                  <h1 className="text-sm font-bold leading-none tracking-tight">FreqTrade AI</h1>
                  <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                    Dashboard v2.0
                  </span>
                </div>
              </div>
              <h2 className="sr-only">FreqTrade Dashboard</h2>
            </SidebarHeader>

            <SidebarContent className="px-2">
              {navItems.map((group) => (
                <SidebarGroup key={group.group}>
                  <SidebarGroupLabel className="text-[11px]">{group.group}</SidebarGroupLabel>
                  <SidebarMenu>
                    {group.items.map(({ path, label, icon: Icon }) => {
                      const isActive = router.pathname === path;
                      return (
                        <SidebarMenuItem key={path}>
                          <SidebarMenuButton asChild isActive={isActive} tooltip={label}>
                            <Link href={path}>
                              <Icon />
                              <span>{label}</span>
                            </Link>
                          </SidebarMenuButton>
                        </SidebarMenuItem>
                      );
                    })}
                  </SidebarMenu>
                </SidebarGroup>
              ))}
            </SidebarContent>

            <SidebarFooter className="gap-0">
              <SidebarSeparator />
              <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="size-4 text-muted-foreground" aria-hidden="true" />
                  <span className="text-[11px] text-muted-foreground font-medium">Freqtrade AI v1.0.0</span>
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
            </SidebarFooter>
          </Sidebar>

          {/* ── Main Content ── */}
          <SidebarInset>
            <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-border/60 bg-card/30 backdrop-blur-md px-4 sm:px-6">
              <div className="flex items-center gap-3">
                <SidebarTrigger />
                <Separator orientation="vertical" className="h-6" />
                <div className="hidden sm:flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Bot Status:</span>
                  <div className="flex items-center gap-1.5 rounded-full border border-border bg-background/50 px-2.5 py-1">
                    <span className={[
                      "size-2 rounded-full",
                      status === "Live" ? "bg-profit motion-safe:animate-pulse" :
                      status === "Connecting\u2026" ? "bg-warning motion-safe:animate-bounce" : "bg-loss"
                    ].join(" ")} />
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                      {status}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="sm:hidden flex items-center gap-1.5 rounded-full border border-border bg-background/50 px-2 py-1">
                  <span className={[
                    "size-1.5 rounded-full",
                    status === "Live" ? "bg-profit motion-safe:animate-pulse" : "bg-loss"
                  ].join(" ")} />
                  <span className="text-[10px] font-semibold uppercase text-muted-foreground">{status}</span>
                </div>
                <div className="rounded-lg border border-border/40 bg-secondary/80 px-3 py-1.5 text-xs font-semibold text-muted-foreground select-none">
                  API Connection Live
                </div>
              </div>
            </header>

            <main id="main-content" className="flex-1 overflow-y-auto scrollbar-thin p-4 sm:p-5 md:p-6 lg:p-8">
              <div className="mx-auto w-full max-w-[1600px] flex flex-col gap-6">
                <ErrorBoundary>
                  <Component {...pageProps} />
                </ErrorBoundary>
              </div>
            </main>
          </SidebarInset>
        </SidebarProvider>
      </TooltipProvider>
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
