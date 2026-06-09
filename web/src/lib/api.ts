const API_BASE = (typeof process !== "undefined" && (process.env as any).NEXT_PUBLIC_API_URL) || "/api/v1";
const API_USER = "admin";
const API_PASS = "admin";

let authToken: string | null = typeof window !== "undefined" ? localStorage.getItem("freqtrade-token") : null;
let loginPromise: Promise<void> | null = null;

async function ensureAuth(): Promise<void> {
  if (authToken) return;
  if (loginPromise) return loginPromise;
  loginPromise = (async () => {
    try {
      // Freqtrade uses HTTP Basic Auth for token login
      const basicAuth = btoa(`${API_USER}:${API_PASS}`);
      const resp = await fetch(`${API_BASE}/token/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Basic ${basicAuth}`,
        },
      });
      if (!resp.ok) throw new Error(`Login failed: ${resp.status}`);
      const data = await resp.json();
      authToken = data.access_token;
      localStorage.setItem("freqtrade-token", authToken);
    } catch (e) {
      console.error("Auth failed:", e);
    } finally {
      loginPromise = null;
    }
  })();
  return loginPromise;
}

// Auto-trigger login on load
ensureAuth();

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  await ensureAuth();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  const mergedHeaders = { ...headers, ...options?.headers };
  const resp = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: mergedHeaders,
  });
  if (resp.status === 401) {
    // Token expired — clear and retry once
    authToken = null;
    localStorage.removeItem("freqtrade-token");
    await ensureAuth();
    const retryResp = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: { ...headers, "Authorization": `Bearer ${authToken}`, ...options?.headers },
    });
    if (!retryResp.ok) {
      throw new Error(`API ${endpoint}: ${retryResp.status} ${retryResp.statusText}`);
    }
    return retryResp.json() as Promise<T>;
  }
  if (!resp.ok) {
    throw new Error(`API ${endpoint}: ${resp.status} ${resp.statusText}`);
  }
  return resp.json() as Promise<T>;
}

export type Trade = {
  trade_id: number;
  pair: string;
  base_currency: string;
  quote_currency: string;
  is_open: boolean;
  is_short: boolean;
  exchange: string;
  amount: number;
  amount_requested: number;
  stake_amount: number;
  max_stake_amount: number | null;
  strategy: string;
  enter_tag: string | null;
  timeframe: number;
  fee_open: number | null;
  fee_open_cost: number | null;
  fee_open_currency: string | null;
  fee_close: number | null;
  fee_close_cost: number | null;
  fee_close_currency: string | null;
  open_date: string;
  open_timestamp: number;
  open_fill_date: string | null;
  open_fill_timestamp: number | null;
  open_rate: number;
  open_rate_requested: number | null;
  open_trade_value: number;
  close_date: string | null;
  close_timestamp: number | null;
  close_rate: number | null;
  close_rate_requested: number | null;
  close_profit: number | null;
  close_profit_pct: number | null;
  close_profit_abs: number | null;
  profit_ratio: number | null;
  profit_pct: number | null;
  profit_abs: number | null;
  profit_fiat: number | null;
  realized_profit: number;
  realized_profit_ratio: number | null;
  exit_reason: string | null;
  exit_order_status: string | null;
  stop_loss_abs: number | null;
  stop_loss_ratio: number | null;
  stop_loss_pct: number | null;
  stoploss_last_update: string | null;
  stoploss_last_update_timestamp: number | null;
  initial_stop_loss_abs: number | null;
  initial_stop_loss_ratio: number | null;
  initial_stop_loss_pct: number | null;
  min_rate: number | null;
  max_rate: number | null;
  nr_of_successful_entries: number;
  nr_of_successful_exits: number;
  has_open_orders: boolean;
  orders: Array<{
    pair: string;
    order_id: string;
    status: string;
    remaining: number | null;
    amount: number;
    safe_price: number;
    cost: number;
    filled: number | null;
    ft_order_side: string;
    order_type: string;
    is_open: boolean;
    order_timestamp: number | null;
    order_filled_timestamp: number | null;
    ft_fee_base: number | null;
    ft_order_tag: string | null;
  }>;
  leverage: number | null;
  interest_rate: number | null;
  liquidation_price: number | null;
  funding_fees: number | null;
  trading_mode: string | null;
  amount_precision: number | null;
  price_precision: number | null;
  precision_mode: number | null;
};

export type Profit = {
  profit_closed_coin: number;
  profit_closed_percent_mean: number;
  profit_closed_ratio_mean: number;
  profit_closed_percent_sum: number;
  profit_closed_ratio_sum: number;
  profit_closed_percent: number;
  profit_closed_ratio: number;
  profit_closed_fiat: number;
  profit_all_coin: number;
  profit_all_percent_mean: number;
  profit_all_ratio_mean: number;
  profit_all_percent_sum: number;
  profit_all_ratio_sum: number;
  profit_all_percent: number;
  profit_all_ratio: number;
  profit_all_fiat: number;
  trade_count: number;
  closed_trade_count: number;
  first_trade_date: string;
  first_trade_humanized: string;
  first_trade_timestamp: number;
  latest_trade_date: string;
  latest_trade_humanized: string;
  latest_trade_timestamp: number;
  avg_duration: string;
  best_pair: string;
  best_rate: number;
  best_pair_profit_ratio: number;
  best_pair_profit_abs: number;
  winning_trades: number;
  losing_trades: number;
  profit_factor: number;
  winrate: number;
  expectancy: number;
  expectancy_ratio: number;
  sharpe: number;
  sortino: number;
  sqn: number;
  calmar: number;
  cagr: number;
  max_drawdown: number;
  max_drawdown_abs: number;
  max_drawdown_start: string;
  max_drawdown_start_timestamp: number;
  max_drawdown_end: string;
  max_drawdown_end_timestamp: number;
  current_drawdown: number;
  current_drawdown_abs: number;
  current_drawdown_high: number;
  current_drawdown_start: string;
  current_drawdown_start_timestamp: number;
  trading_volume: number | null;
  bot_start_timestamp: number;
  bot_start_date: string;
};

export type Balance = {
  currencies: Array<{
    currency: string;
    free: number;
    balance: number;
    used: number;
    bot_owned: number | null;
    est_stake: number;
    est_stake_bot: number | null;
    stake: string;
    side: string;
    is_position: boolean;
    position: number;
    is_bot_managed: boolean;
  }>;
  total: number;
  total_bot: number;
  symbol: string;
  value: number;
  value_bot: number;
  stake: string;
  note: string;
  starting_capital: number;
  starting_capital_ratio: number;
  starting_capital_pct: number;
  starting_capital_fiat: number;
  starting_capital_fiat_ratio: number;
  starting_capital_fiat_pct: number;
};

export type Health = {
  last_process: string | null;
  last_process_ts: number | null;
  bot_start: string | null;
  bot_start_ts: number | null;
  bot_startup: string | null;
  bot_startup_ts: number | null;
};

export type PerformanceEntry = {
  pair: string;
  profit_ratio: number;
  profit_pct: number;
  profit_abs: number;
  count: number;
};

export type PaperStatus = {
  state: string;
  equity: number;
  balance: number;
  total_pnl: number;
  day_pnl: number;
  day_trades: number;
  bar_count: number;
  uptime_sec: number;
  position: {
    id: number;
    symbol: string;
    direction: string;
    entry_price: number;
    stop_price: number;
    quantity: number;
    bars_held: number;
    entry_fee: number;
    open_ts: string;
  } | null;
};

export type PaperTrade = {
  id: number;
  symbol: string;
  direction: string;
  entry_price: number;
  exit_price: number;
  size: number;
  net_pnl: number;
  return_pct: number;
  holding_bars: number;
  exit_reason: string;
  entry_ts: string;
  exit_ts: string;
};

export type TopUpEntry = {
  id: number;
  ts: string;
  amount: number;
  balance_before: number;
  balance_after: number;
};

export type DailyRecord = {
  date: string;
  abs_profit: number;
  rel_profit: number;
  starting_balance: number;
  fiat_value: number;
  trade_count: number;
};

export type DailyResponse = {
  data: DailyRecord[];
  fiat_display_currency: string;
  stake_currency: string;
};

export type SysInfo = {
  cpu_pct: number[];
  cpu_load: Array<{ cpu: number; pct: number }>;
  cpu_load_avg: Record<string, number>;
  cpu_count: number;
  cpu_avg: number;
  ram_pct: number;
};

export type LogResponse = {
  log_count: number;
  logs: string[][];
};

export type BacktestStatus = {
  status: string;
  running: boolean;
  status_msg: string;
  step: string;
  progress: number;
  trade_count: number | null;
  backtest_result: Record<string, unknown> | null;
};

export type BacktestHistoryEntry = {
  filename: string;
  strategy: string;
  run_id: string;
  backtest_start_time: number;
  notes: string | null;
  backtest_start_ts: number | null;
  backtest_end_ts: number | null;
  timeframe: string | null;
  timeframe_detail: string | null;
};

export type BacktestPayload = {
  strategy: string;
  timeframe?: string | null;
  timeframe_detail?: string | null;
  timerange?: string | null;
  max_open_trades?: number | string | null;
  stake_amount?: string | number | null;
  enable_protections: boolean;
  dry_run_wallet?: number | null;
  backtest_cache?: string | null;
  freqaimodel?: string | null;
  freqai?: { identifier: string } | null;
};

export type MarketModel = {
  symbol: string;
  base: string;
  quote: string;
  spot: boolean;
  swap: boolean;
};

export type MarketResponse = {
  markets: Record<string, MarketModel>;
  exchange_id: string;
};

export type StrategyListResponse = {
  strategies: string[];
};

export type FreqAIModelListResponse = {
  freqaimodels: string[];
};

export type ShowConfig = {
  version: string;
  strategy_version: string | null;
  api_version: number;
  dry_run: boolean;
  trading_mode: string;
  margin_mode: string;
  short_allowed: boolean;
  stake_currency: string;
  stake_amount: string;
  available_capital: number | null;
  stake_currency_decimals: number;
  max_open_trades: number | string;
  minimal_roi: Record<string, unknown>;
  stoploss: number | null;
  stoploss_on_exchange: boolean;
  trailing_stop: boolean | null;
  trailing_stop_positive: number | null;
  trailing_stop_positive_offset: number | null;
  trailing_only_offset_is_reached: boolean | null;
  unfilledtimeout: Record<string, unknown> | null;
  order_types: Record<string, unknown> | null;
  use_custom_stoploss: boolean | null;
  timeframe: string | null;
  timeframe_ms: number;
  timeframe_min: number;
  exchange: string;
  demo_trading: boolean;
  strategy: string | null;
  force_entry_enable: boolean;
  exit_pricing: Record<string, unknown>;
  entry_pricing: Record<string, unknown>;
  bot_name: string;
  state: string;
  runmode: string;
  position_adjustment_enable: boolean;
  max_entry_position_adjustment: number;
};

export type StatusMsg = {
  status: string;
};

export type PairHistory = {
  strategy: string;
  pair: string;
  timeframe: string;
  timeframe_ms: number;
  columns: string[];
  all_columns: string[];
  data: Array<Array<number | string | null>>;
  length: number;
  buy_signals: number;
  sell_signals: number;
  enter_long_signals: number;
  exit_long_signals: number;
  enter_short_signals: number;
  exit_short_signals: number;
  last_analyzed: string;
  last_analyzed_ts: number;
  data_start_ts: number;
  data_start: string;
  data_stop: string;
  data_stop_ts: number;
};

export type WhitelistResponse = {
  whitelist: string[];
  length: number;
  method: string[];
};

export type AvailablePairs = {
  length: number;
  pairs: string[];
  pair_interval: Array<[string, string]>;
};

export const api = {
  ping: () => fetchJSON<{ status: string }>("/ping"),

  profit: () => fetchJSON<Profit>("/profit"),
  profitAll: () => fetchJSON<{ all: Profit; long: Profit | null; short: Profit | null }>("/profit_all"),
  balance: () => fetchJSON<Balance>("/balance"),
  count: () => fetchJSON<{ current: number; max: number; total_stake: number }>("/count"),
  performance: () => fetchJSON<PerformanceEntry[]>("/performance"),
  trades: (limit = 50) => fetchJSON<{ trades: Trade[]; trades_count: number }>(`/trades?limit=${limit}`),
  trade: (id: number) => fetchJSON<Trade>(`/trade/${id}`),
  health: () => fetchJSON<Health>("/health"),

  daily: (timescale = 7) => fetchJSON<DailyResponse>(`/daily?timescale=${timescale}`),
  weekly: (timescale = 4) => fetchJSON<DailyResponse>(`/weekly?timescale=${timescale}`),
  monthly: (timescale = 3) => fetchJSON<DailyResponse>(`/monthly?timescale=${timescale}`),

  sysinfo: () => fetchJSON<SysInfo>("/sysinfo"),
  logs: (limit = 100) => fetchJSON<LogResponse>(`/logs?limit=${limit}`),
  showConfig: () => fetchJSON<ShowConfig>("/show_config"),

  strategies: () => fetchJSON<StrategyListResponse>("/strategies"),
  markets: () => fetchJSON<MarketResponse>("/markets"),
  freqaimodels: () => fetchJSON<FreqAIModelListResponse>("/freqaimodels"),

  backtest: () => fetchJSON<BacktestStatus>("/backtest"),
  backtestStart: (payload: BacktestPayload) => fetchJSON<BacktestStatus>("/backtest", { method: "POST", body: JSON.stringify(payload) }),
  backtestDelete: () => fetchJSON<BacktestStatus>("/backtest", { method: "DELETE" }),
  backtestHistory: () => fetchJSON<BacktestHistoryEntry[]>("/backtest/history"),
  backtestHistoryResult: (filename: string, strategy: string) => fetchJSON<BacktestStatus>(`/backtest/history/result?filename=${encodeURIComponent(filename)}&strategy=${encodeURIComponent(strategy)}`),
  backtestHistoryDelete: (file: string) => fetchJSON<BacktestHistoryEntry[]>(`/backtest/history/${encodeURIComponent(file)}`, { method: "DELETE" }),

  start: () => fetchJSON<StatusMsg>("/start", { method: "POST" }),
  stop: () => fetchJSON<StatusMsg>("/stop", { method: "POST" }),
  reloadConfig: () => fetchJSON<StatusMsg>("/reload_config", { method: "POST" }),

  pairCandles: (pair: string, timeframe: string, limit = 100) => fetchJSON<PairHistory>(`/pair_candles?pair=${encodeURIComponent(pair)}&timeframe=${timeframe}&limit=${limit}`),
  availablePairs: (timeframe?: string, stake_currency?: string) => fetchJSON<AvailablePairs>(`/available_pairs${timeframe ? `?timeframe=${timeframe}` : ""}${stake_currency ? `&stake_currency=${stake_currency}` : ""}`),
  whitelist: () => fetchJSON<WhitelistResponse>("/whitelist"),
  blacklist: () => fetchJSON<{ blacklist: string[]; length: number }>("/blacklist"),

  paperStatus: () => fetchJSON<PaperStatus>("/paper/status"),
  paperTrades: (limit = 50) => fetchJSON<PaperTrade[]>(`/paper/trades?limit=${limit}`),
  paperAccount: (limit = 100) => fetchJSON<Array<{ ts: string; balance: number; equity: number; unrealized_pnl: number; day_pnl: number; day_trades: number }>>(`/paper/account?limit=${limit}`),
  paperTopUp: (amount: number) => fetchJSON<{ old_balance: number; new_balance: number; amount: number }>("/paper/topup", { method: "POST", body: JSON.stringify({ amount }) }),

  forceEnter: (pair: string, price?: number) => fetchJSON<unknown>("/forceenter", { method: "POST", body: JSON.stringify({ pair, price }) }),
  forceExit: (tradeid: number) => fetchJSON<unknown>("/forceexit", { method: "POST", body: JSON.stringify({ tradeid }) }),
  deleteTrade: (tradeid: number) => fetchJSON<unknown>(`/trades/${tradeid}`, { method: "DELETE" }),
};
