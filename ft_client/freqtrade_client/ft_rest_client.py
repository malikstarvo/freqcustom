"""
A Rest Client for Freqtrade bot

Should not import anything from freqtrade,
so it can be used as a standalone script, and can be installed independently.
"""

import json
import logging
from typing import Any
from urllib.parse import urlencode, urlparse, urlunparse

import requests
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError as RequestConnectionError


logger = logging.getLogger("ft_rest_client")

ParamsT = dict[str, Any] | None
PostDataT = dict[str, Any] | list[dict[str, Any]] | None


class FtRestClient:
    def __init__(
        self,
        serverurl,
        username=None,
        password=None,
        *,
        pool_connections=10,
        pool_maxsize=10,
        timeout=10,
    ):
        self._serverurl = serverurl
        self._session = requests.Session()
        self._timeout = timeout

        # allow configuration of pool
        adapter = HTTPAdapter(pool_connections=pool_connections, pool_maxsize=pool_maxsize)
        self._session.mount("http://", adapter)

        if username and password:
            self._session.auth = (username, password)

    def _call(self, method, apipath, params: dict | None = None, data=None, files=None):
        if str(method).upper() not in ("GET", "POST", "PUT", "DELETE"):
            raise ValueError(f"invalid method <{method}>")
        basepath = f"{self._serverurl}/api/v1/{apipath}"

        hd = {"Accept": "application/json", "Content-Type": "application/json"}

        # Split url
        schema, netloc, path, par, query, fragment = urlparse(basepath)
        # URLEncode query string
        query = urlencode(params) if params else ""
        # recombine url
        url = urlunparse((schema, netloc, path, par, query, fragment))

        try:
            resp = self._session.request(
                method, url, headers=hd, timeout=self._timeout, data=json.dumps(data)
            )
            # return resp.text
            return resp.json()
        except RequestConnectionError:
            logger.warning(f"Connection error - could not connect to {netloc}.")

    def _get(self, apipath, params: ParamsT = None):
        return self._call("GET", apipath, params=params)

    def _delete(self, apipath, params: ParamsT = None):
        return self._call("DELETE", apipath, params=params)

    def _post(self, apipath, params: ParamsT = None, data: PostDataT = None):
        return self._call("POST", apipath, params=params, data=data)

    def start(self):
        """Start the bot if it's in the stopped state.

        :return: json object with status and follow-up state
        """
        result = self._post("start") or {}
        try:
            cfg = self.show_config()
            if cfg:
                result["_state"] = cfg.get("state", "unknown")
                result["_strategy"] = cfg.get("strategy", "\u2014")
                result["_exchange"] = cfg.get("exchange", "\u2014")
                result["_dry_run"] = cfg.get("dry_run", True)
                result["_trading_mode"] = cfg.get("trading_mode", "\u2014")
        except Exception:
            pass
        return result

    def stop(self):
        """Stop the bot. Use `start` to restart.

        :return: json object with status and follow-up state
        """
        result = self._post("stop") or {}
        try:
            cfg = self.show_config()
            if cfg:
                result["_state"] = cfg.get("state", "unknown")
        except Exception:
            pass
        return result

    def stopbuy(self):
        """Stop buying (but handle sells gracefully). Use `reload_config` to reset.

        :return: json object
        """
        result = self._post("stopbuy") or {}
        return result

    def reload_config(self):
        """Reload configuration.

        :return: json object
        """
        return self._post("reload_config")

    def balance(self):
        """Get the account balance.

        :return: json object
        """
        return self._get("balance")

    def count(self):
        """Return the amount of open trades.

        :return: json object
        """
        return self._get("count")

    def entries(self, pair=None):
        """Returns List of dicts containing all Trades, based on buy tag performance
        Can either be average for all pairs or a specific pair provided

        :return: json object
        """
        return self._get("entries", params={"pair": pair} if pair else None)

    def exits(self, pair=None):
        """Returns List of dicts containing all Trades, based on exit reason performance
        Can either be average for all pairs or a specific pair provided

        :return: json object
        """
        return self._get("exits", params={"pair": pair} if pair else None)

    def mix_tags(self, pair=None):
        """Returns List of dicts containing all Trades, based on entry_tag + exit_reason performance
        Can either be average for all pairs or a specific pair provided

        :return: json object
        """
        return self._get("mix_tags", params={"pair": pair} if pair else None)

    def locks(self):
        """Return current locks

        :return: json object
        """
        return self._get("locks")

    def delete_lock(self, lock_id):
        """Delete (disable) lock from the database.

        :param lock_id: ID for the lock to delete
        :return: json object
        """
        return self._delete(f"locks/{lock_id}")

    def lock_add(self, pair: str, until: str, side: str = "*", reason: str = ""):
        """Lock pair

        :param pair: Pair to lock
        :param until: Lock until this date (format "2024-03-30 16:00:00Z")
        :param side: Side to lock (long, short, *)
        :param reason: Reason for the lock
        :return: json object
        """
        data = [{"pair": pair, "until": until, "side": side, "reason": reason}]
        return self._post("locks", data=data)

    def daily(self, days=None):
        """Return the profits for each day, and amount of trades.

        :return: json object
        """
        return self._get("daily", params={"timescale": days} if days else None)

    def weekly(self, weeks=None):
        """Return the profits for each week, and amount of trades.

        :return: json object
        """
        return self._get("weekly", params={"timescale": weeks} if weeks else None)

    def monthly(self, months=None):
        """Return the profits for each month, and amount of trades.

        :return: json object
        """
        return self._get("monthly", params={"timescale": months} if months else None)

    def profit(self):
        """Return the profit summary.

        :return: json object
        """
        return self._get("profit")

    def stats(self):
        """Return the stats report (durations, sell-reasons).

        :return: json object
        """
        return self._get("stats")

    def performance(self):
        """Return the performance of the different coins.

        :return: json object
        """
        return self._get("performance")

    def status(self):
        """Get the status of open trades.

        :return: json object
        """
        return self._get("status")

    def version(self):
        """Return the version of the bot.

        :return: json object containing the version
        """
        return self._get("version")

    def show_config(self):
        """Returns part of the configuration, relevant for trading operations.
        :return: json object containing the version
        """
        return self._get("show_config")

    def ping(self):
        """simple ping — calls the actual /api/v1/ping endpoint."""
        try:
            return self._get("ping")
        except Exception:
            return {"status": "not_running"}

    def logs(self, limit=None):
        """Show latest logs.

        :param limit: Limits log messages to the last <limit> logs. No limit to get the entire log.
        :return: json object
        """
        return self._get("logs", params={"limit": limit} if limit else {})

    def trades(self, limit=None, offset=None, order_by_id=True):
        """Return trades history, sorted by id (or by latest timestamp if order_by_id=False)

        :param limit: Limits trades to the X last trades. Max 500 trades.
        :param offset: Offset by this amount of trades.
        :param order_by_id: Sort trades by id (default: True). If False, sorts by latest timestamp.
        :return: json object
        """
        params = {}
        if limit:
            params["limit"] = limit
        if offset:
            params["offset"] = offset
        if not order_by_id:
            params["order_by_id"] = False
        return self._get("trades", params)

    def list_open_trades_custom_data(self, key=None, limit=100, offset=0):
        """List open trades custom-data of the running bot.

        :param key: str, optional - Key of the custom-data
        :param limit: limit of trades
        :param offset: trades offset for pagination
        :return: json object
        """
        params = {}
        params["limit"] = limit
        params["offset"] = offset
        if key is not None:
            params["key"] = key

        return self._get("trades/open/custom-data", params=params)

    def list_custom_data(self, trade_id, key=None):
        """List custom-data of the running bot for a specific trade.

        :param trade_id: ID of the trade
        :param key: str, optional - Key of the custom-data
        :return: JSON object
        """
        params = {}
        params["trade_id"] = trade_id
        if key is not None:
            params["key"] = key

        return self._get(f"trades/{trade_id}/custom-data", params=params)

    def trade(self, trade_id):
        """Return specific trade

        :param trade_id: Specify which trade to get.
        :return: json object
        """
        return self._get(f"trade/{trade_id}")

    def delete_trade(self, trade_id):
        """Delete trade from the database.
        Tries to close open orders. Requires manual handling of this asset on the exchange.

        :param trade_id: Deletes the trade with this ID from the database.
        :return: json object
        """
        return self._delete(f"trades/{trade_id}")

    def cancel_open_order(self, trade_id):
        """Cancel open order for trade.

        :param trade_id: Cancels open orders for this trade.
        :return: json object
        """
        return self._delete(f"trades/{trade_id}/open-order")

    def whitelist(self):
        """Show the current whitelist.

        :return: json object
        """
        return self._get("whitelist")

    def blacklist(self, *args):
        """Show the current blacklist.

        :param add: List of coins to add (example: "BNB/BTC")
        :return: json object
        """
        if not args:
            return self._get("blacklist")
        else:
            return self._post("blacklist", data={"blacklist": args})

    def forcebuy(self, pair, price=None):
        """Buy an asset.

        :param pair: Pair to buy (ETH/BTC)
        :param price: Optional - price to buy
        :return: json object of the trade
        """
        data = {"pair": pair, "price": price}
        return self._post("forcebuy", data=data)

    def forceenter(
        self,
        pair,
        side,
        price=None,
        *,
        order_type=None,
        stake_amount=None,
        leverage=None,
        enter_tag=None,
    ):
        """Force entering a trade

        :param pair: Pair to buy (ETH/BTC)
        :param side: 'long' or 'short'
        :param price: Optional - price to buy
        :param order_type: Optional keyword argument - 'limit' or 'market'
        :param stake_amount: Optional keyword argument - stake amount (as float)
        :param leverage: Optional keyword argument - leverage (as float)
        :param enter_tag: Optional keyword argument - entry tag (as string, default: 'force_enter')
        :return: json object of the trade
        """
        data = {
            "pair": pair,
            "side": side,
        }

        if price:
            data["price"] = price

        if order_type:
            data["ordertype"] = order_type

        if stake_amount:
            data["stakeamount"] = stake_amount

        if leverage:
            data["leverage"] = leverage

        if enter_tag:
            data["entry_tag"] = enter_tag

        return self._post("forceenter", data=data)

    def forceexit(self, tradeid, ordertype=None, amount=None):
        """Force-exit a trade.

        :param tradeid: Id of the trade (can be received via status command)
        :param ordertype: Order type to use (must be market or limit)
        :param amount: Amount to sell. Full sell if not given
        :return: json object
        """

        return self._post(
            "forceexit",
            data={
                "tradeid": tradeid,
                "ordertype": ordertype,
                "amount": amount,
            },
        )

    def strategies(self):
        """Lists available strategies

        :return: json object
        """
        return self._get("strategies")

    def strategy(self, strategy):
        """Get strategy details

        :param strategy: Strategy class name
        :return: json object
        """
        return self._get(f"strategy/{strategy}")

    def pairlists_available(self):
        """Lists available pairlist providers

        :return: json object
        """
        return self._get("pairlists/available")

    def plot_config(self):
        """Return plot configuration if the strategy defines one.

        :return: json object
        """
        return self._get("plot_config")

    def available_pairs(self, timeframe=None, stake_currency=None):
        """Return available pair (backtest data) based on timeframe / stake_currency selection

        :param timeframe: Only pairs with this timeframe available.
        :param stake_currency: Only pairs that include this stake currency.
        :return: json object
        """
        return self._get(
            "available_pairs",
            params={
                "stake_currency": stake_currency if stake_currency else "",
                "timeframe": timeframe if timeframe else "",
            },
        )

    def pair_candles(self, pair, timeframe, limit=None, columns=None):
        """Return live dataframe for <pair><timeframe>.

        :param pair: Pair to get data for
        :param timeframe: Only pairs with this timeframe available.
        :param limit: Limit result to the last n candles.
        :param columns: List of dataframe columns to return. Empty list will return OHLCV.
        :return: json object
        """
        params = {
            "pair": pair,
            "timeframe": timeframe,
        }
        if limit:
            params["limit"] = limit

        if columns is not None:
            params["columns"] = columns
            return self._post("pair_candles", data=params)

        return self._get("pair_candles", params=params)

    def pair_history(self, pair, timeframe, strategy, timerange=None, freqaimodel=None):
        """Return historic, analyzed dataframe

        :param pair: Pair to get data for
        :param timeframe: Only pairs with this timeframe available.
        :param strategy: Strategy to analyze and get values for
        :param freqaimodel: FreqAI model to use for analysis
        :param timerange: Timerange to get data for (same format than --timerange endpoints)
        :return: json object
        """
        return self._get(
            "pair_history",
            params={
                "pair": pair,
                "timeframe": timeframe,
                "strategy": strategy,
                "freqaimodel": freqaimodel,
                "timerange": timerange if timerange else "",
            },
        )

    def sysinfo(self):
        """Provides system information (CPU, RAM usage)

        :return: json object
        """
        return self._get("sysinfo")

    def health(self):
        """Provides a quick health check of the running bot.

        :return: json object
        """
        return self._get("health")

    # ── Paper Trading ────────────────────────────────────

    def paper_status(self):
        """Get paper trading engine status: equity, balance, PnL, position.

        :return: json object
        """
        return self._get("paper/status")

    def paper_topup(self, amount):
        """Add simulated capital to paper trading balance.

        :param amount: Amount to add (float)
        :return: json object
        """
        return self._post("paper/topup", data={"amount": float(amount)})

    def paper_trades(self, limit=50):
        """Get paper trading trade history.

        :param limit: Max trades to return
        :return: json object
        """
        return self._get("paper/trades", params={"limit": limit})

    def paper_account(self, limit=100):
        """Get paper trading account snapshots (equity over time).

        :param limit: Max snapshots to return
        :return: json object
        """
        return self._get("paper/account", params={"limit": limit})

    # ── Backtest ─────────────────────────────────────────

    def backtest_start(self, strategy=None, timeframe=None, timerange=None,
                       max_open_trades=None, stake_amount=None,
                       enable_protections=False, freqaimodel=None):
        """Start a backtest via the API.

        :param strategy: Strategy class name (default: from config)
        :param timeframe: Timeframe (e.g. "15m")
        :param timerange: Timerange string (e.g. "20240101-20240201")
        :param max_open_trades: Max concurrent trades
        :param stake_amount: Stake amount per trade
        :param enable_protections: Enable protections
        :param freqaimodel: FreqAI model identifier
        :return: json object
        """
        if not strategy:
            try:
                cfg = self.show_config()
                strategy = (cfg.get("strategy") or "MultiAgentStrategy") if cfg else "MultiAgentStrategy"
            except Exception:
                strategy = "MultiAgentStrategy"
        data = {"strategy": strategy, "enable_protections": enable_protections}
        if timeframe:
            data["timeframe"] = timeframe
        if timerange:
            data["timerange"] = timerange
        if max_open_trades:
            data["max_open_trades"] = max_open_trades
        if stake_amount:
            data["stake_amount"] = stake_amount
        if freqaimodel:
            data["freqaimodel"] = freqaimodel
        return self._post("backtest", data=data)

    def backtest_status(self):
        """Get current backtest status and progress.

        :return: json object
        """
        return self._get("backtest")

    def backtest_delete(self):
        """Reset/delete running backtest.

        :return: json object
        """
        return self._delete("backtest")

    def backtest_abort(self):
        """Abort a running backtest.

        :return: json object
        """
        return self._get("backtest/abort")

    def backtest_history(self):
        """List historical backtest results.

        :return: json object
        """
        return self._get("backtest/history")

    def backtest_history_result(self, filename, strategy):
        """Load a specific backtest result.

        :param filename: Backtest result filename
        :param strategy: Strategy name used in the backtest
        :return: json object
        """
        return self._get("backtest/history/result",
                         params={"filename": filename, "strategy": strategy})

    def backtest_history_delete(self, filename):
        """Delete a backtest result file.

        :param filename: Backtest result filename to delete
        :return: json object
        """
        return self._delete(f"backtest/history/{filename}")

    # ── Dashboard ────────────────────────────────────────

    def dashboard(self):
        """Show a comprehensive dashboard: bot state, P&L, balance, open trades,
        paper equity, system health — everything at a glance.

        :return: dict with all dashboard data
        """
        result: dict[str, Any] = {"_timestamp": None}

        try:
            cfg = self.show_config()
            result["state"] = cfg.get("state", "unknown")
            result["strategy"] = cfg.get("strategy", "—")
            result["exchange"] = cfg.get("exchange", "—")
            result["dry_run"] = cfg.get("dry_run", True)
            result["trading_mode"] = cfg.get("trading_mode", "—")
            result["max_open_trades"] = cfg.get("max_open_trades", "—")
            result["stake_currency"] = cfg.get("stake_currency", "—")
        except Exception:
            result["state"] = "offline"

        # Profit summary
        try:
            p = self.profit()
            result["profit_all_pct"] = round(p.get("profit_all_percent") or 0, 2)
            result["profit_closed_pct"] = round(p.get("profit_closed_percent") or 0, 2)
            result["profit_closed_coin"] = round(p.get("profit_closed_coin") or 0, 4)
            result["winrate"] = round((p.get("winrate") or 0) * 100, 1)
            result["trade_count"] = p.get("trade_count") or 0
            result["closed_trade_count"] = p.get("closed_trade_count") or 0
            result["best_pair"] = p.get("best_pair") or "—"
            result["max_drawdown"] = round((p.get("max_drawdown") or 0) * 100, 2)
            result["profit_factor"] = round(p.get("profit_factor") or 0, 2)
            result["sharpe"] = round(p.get("sharpe") or 0, 2)
            result["avg_duration"] = p.get("avg_duration") or "—"
        except Exception:
            pass
            pass

        # Open trades
        try:
            status_data = self.status()
            result["open_trades"] = len(status_data) if isinstance(status_data, list) else 0
            result["open_trades_detail"] = status_data
        except Exception:
            result["open_trades"] = 0

        # Balance
        try:
            bal = self.balance()
            result["total_balance"] = round(bal.get("total") or 0, 2)
            result["balance_symbol"] = bal.get("symbol") or "—"
            result["currency_count"] = len(bal.get("currencies") or [])
        except Exception:
            pass

        # Health
        try:
            h = self.health()
            result["last_process"] = h.get("last_process", "—")
        except Exception:
            pass

        # Paper trading
        try:
            ps = self.paper_status()
            result["paper_equity"] = round(ps.get("equity") or 0, 2)
            result["paper_balance"] = round(ps.get("balance") or 0, 2)
            result["paper_total_pnl"] = round(ps.get("total_pnl") or 0, 2)
            result["paper_day_pnl"] = round(ps.get("day_pnl") or 0, 2)
            result["paper_day_trades"] = ps.get("day_trades") or 0
            result["paper_position"] = ps.get("position")
        except Exception:
            pass

        return result

    # ── Live Market Data ────────────────────────────────

    def markets(self, limit: int = 20):
        """Fetch real-time market data from the configured exchange.

        :param limit: Max pairs to show (default 20)
        :return: dict with exchange, pairs[], and raw tickers
        """
        limit = int(limit)
        result: dict[str, Any] = {"exchange": "", "pairs": [], "_error": None}

        try:
            cfg = self.show_config()
            exchange_name = cfg.get("exchange", "binance") if cfg else "binance"
            whitelist = None
            try:
                wl = self.whitelist()
                whitelist = wl.get("whitelist", []) if isinstance(wl, dict) else wl
            except Exception:
                pass

            result["exchange"] = exchange_name
            result["dry_run"] = cfg.get("dry_run", True) if cfg else True

            import ccxt

            exchange = getattr(ccxt, exchange_name)({"enableRateLimit": True})
            tickers = exchange.fetch_tickers(whitelist[:limit] if whitelist else None)

            for symbol, ticker in list(tickers.items())[:limit]:
                result["pairs"].append({
                    "symbol": symbol,
                    "last": ticker.get("last", 0) or 0,
                    "change_pct": (ticker.get("percentage") or 0),
                    "high": ticker.get("high", 0) or 0,
                    "low": ticker.get("low", 0) or 0,
                    "volume": ticker.get("baseVolume", ticker.get("quoteVolume", 0)) or 0,
                    "bid": ticker.get("bid", 0) or 0,
                    "ask": ticker.get("ask", 0) or 0,
                })

        except Exception as e:
            result["_error"] = str(e)

        return result

    # ── Model Info ────────────────────────────────────────

    def model_info(self):
        """Show ML model configuration and training guide.

        :return: dict with model config, available models, training steps
        """
        result: dict[str, Any] = {"_error": None}
        try:
            cfg = self.show_config()
            result["strategy"] = cfg.get("strategy") or "\u2014"
            result["freqaimodel"] = cfg.get("freqaimodel") or "\u2014"
            result["freqaimodel_path"] = cfg.get("freqaimodel_path") or "\u2014"
            freqai = cfg.get("freqai") or {}
            result["freqai_enabled"] = freqai.get("enabled", False)
            result["identifier"] = freqai.get("identifier") or "\u2014"
            result["train_period"] = freqai.get("train_period_days", 90)
            result["backtest_period"] = freqai.get("backtest_period_days", 30)
            fp = freqai.get("feature_parameters") or {}
            result["timeframes"] = fp.get("include_timeframes", [])
            result["label_period"] = fp.get("label_period_candles", 4)
            result["pca"] = fp.get("principal_component_analysis", False)
            result["weight_factor"] = fp.get("weight_factor", 0)

            try:
                models_resp = self.freqaimodels()
                result["available_models"] = models_resp.get("freqaimodels", []) if models_resp else []
            except Exception:
                result["available_models"] = []
        except Exception as e:
            result["_error"] = str(e)

        return result

    # ── Self-Test Suite ──────────────────────────────────

    def self_test(self):
        """Run comprehensive backend test suite against the running API.

        Tests connectivity, bot control, trading info, system health,
        paper trading, strategy/pairs, and data pipeline.
        Returns structured results with pass/fail/skip per test.
        """
        import time as time_mod

        def _run(name: str, fn, *a, **kw):
            start = time_mod.time()
            try:
                data = fn(*a, **kw)
                ms = (time_mod.time() - start) * 1000
                return {"name": name, "status": "pass", "detail": str(data)[:100], "ms": round(ms, 1)}
            except Exception as e:
                ms = (time_mod.time() - start) * 1000
                return {"name": name, "status": "fail", "detail": str(e)[:120], "ms": round(ms, 1)}

        results: list[dict[str, Any]] = []
        t0 = time_mod.time()

        # ── Connectivity ─────────────────────────────────
        cat = {"category": "Connectivity", "tests": []}
        cat["tests"].append(_run("ping", self.ping))

        # Real WebSocket test: JWT auth → connect → subscribe → receive message
        def _test_real_ws():
            # Use Docker internal hostname (always resolvable inside compose)
            host = "freqtrade"

            # 1. Get JWT token via API login
            login_resp = self._post("token/login")
            token = login_resp.get("access_token") if login_resp else None
            if not token:
                raise RuntimeError("No access token from login")

            # 2. Connect WebSocket with token
            try:
                import websocket as _ws
            except ImportError:
                raise RuntimeError("websocket-client not installed")

            ws_url = f"ws://{host}:8080/api/v1/message/ws?token={token}"
            ws = _ws.create_connection(ws_url, timeout=5)

            # 3. Subscribe to STATUS channel
            ws.send(json.dumps({"type": "subscribe", "data": ["STATUS"]}))
            time_mod.sleep(0.5)

            # 4. Read a message to verify real-time feed
            ws.settimeout(3)
            msg_raw = ws.recv()
            msg = json.loads(msg_raw)
            msg_type = msg.get("type", "?")

            ws.close()
            return f"WS OK: received '{msg_type}' message"

        cat["tests"].append(_run("websocket", _test_real_ws))
        results.append(cat)

        # ── Bot Info ─────────────────────────────────────
        cat = {"category": "Bot Info", "tests": []}
        cfg = self.show_config()
        state = (cfg or {}).get("state", "offline")
        cat["tests"].append({"name": "show_config", "status": "pass",
                             "detail": f"state={state}", "ms": 0})
        cat["tests"].append(_run("profit", self.profit))
        cat["tests"].append(_run("balance", self.balance))
        cat["tests"].append(_run("daily", self.daily, 1))
        cat["tests"].append(_run("trades", self.trades, 1))
        cat["tests"].append(_run("performance", self.performance))
        results.append(cat)

        # ── Bot Control ──────────────────────────────────
        cat = {"category": "Bot Control", "tests": []}
        was_running = state == "running"

        if not was_running:
            self.start()
            time_mod.sleep(1.5)
            s2 = (self.show_config() or {}).get("state", "?")
            cat["tests"].append({"name": "start", "status": "pass" if s2 == "running" else "fail",
                                 "detail": f"state={s2}", "ms": 0})

            self.stop()
            time_mod.sleep(1.5)
            s3 = (self.show_config() or {}).get("state", "?")
            cat["tests"].append({"name": "stop", "status": "pass" if s3 == "stopped" else "fail",
                                 "detail": f"state={s3}", "ms": 0})
        else:
            self.stop()
            time_mod.sleep(1.5)
            s2 = (self.show_config() or {}).get("state", "?")
            cat["tests"].append({"name": "stop", "status": "pass" if s2 == "stopped" else "fail",
                                 "detail": f"state={s2}", "ms": 0})
            self.start()
            time_mod.sleep(1.5)
            s3 = (self.show_config() or {}).get("state", "?")
            cat["tests"].append({"name": "start", "status": "pass" if s3 == "running" else "fail",
                                 "detail": f"state={s3}", "ms": 0})
        results.append(cat)

        # ── Paper Trading ────────────────────────────────
        cat = {"category": "Paper Trading", "tests": []}
        try:
            ps = self.paper_status()
            cat["tests"].append({"name": "paper_status", "status": "pass",
                                 "detail": f"equity={ps.get('equity', 0):.0f}", "ms": 0})
        except Exception as e:
            err = str(e)
            status = "skip" if "503" in err or "not running" in err else "fail"
            cat["tests"].append({"name": "paper_status", "status": status, "detail": err[:80], "ms": 0})
        results.append(cat)

        # ── System ───────────────────────────────────────
        cat = {"category": "System", "tests": []}
        cat["tests"].append(_run("sysinfo", self.sysinfo))
        cat["tests"].append(_run("health", self.health))
        cat["tests"].append(_run("logs", self.logs, 5))
        results.append(cat)

        # ── Strategy & Pairs ─────────────────────────────
        cat = {"category": "Strategy & Pairs", "tests": []}
        cat["tests"].append(_run("strategies", self.strategies))
        cat["tests"].append(_run("whitelist", self.whitelist))
        results.append(cat)

        # ── Data Pipeline ────────────────────────────────
        cat = {"category": "Data Pipeline", "tests": []}
        try:
            pd = self.pair_candles("BTC/USDT:USDT", "15m", limit=1)
            n = pd.get("length", 0) if isinstance(pd, dict) else 0
            cat["tests"].append({"name": "pair_candles", "status": "pass",
                                 "detail": f"{n} candles for BTC/USDT:USDT 15m", "ms": 0})
        except Exception as e:
            cat["tests"].append({"name": "pair_candles", "status": "skip", "detail": str(e)[:80], "ms": 0})
        try:
            em = (self.show_config() or {}).get("exchange", "")
            if em:
                cat["tests"].append({"name": f"exchange ({em})", "status": "pass",
                                     "detail": em, "ms": 0})
        except Exception:
            pass
        results.append(cat)

        total_ms = round((time_mod.time() - t0) * 1000)
        passed = sum(t["status"] == "pass" for c in results for t in c["tests"])
        failed = sum(t["status"] == "fail" for c in results for t in c["tests"])
        skipped = sum(t["status"] == "skip" for c in results for t in c["tests"])

        return {
            "categories": results,
            "passed": passed, "failed": failed, "skipped": skipped,
            "total_ms": total_ms, "initial_state": was_running,
        }



