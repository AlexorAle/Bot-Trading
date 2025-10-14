"""Prometheus metrics server for trading bot monitoring."""

import threading
import time
from typing import Any, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram, start_http_server

from .logger import get_monitoring_logger


class MetricsServer:
    """Manage Prometheus metrics exposure and update loop."""

    def __init__(self, config: Dict[str, Any], scrape_interval: Optional[int] = None):
        self.config = config
        self.scrape_interval = scrape_interval or config.get("scrape_interval", 15)
        self.log = get_monitoring_logger("monitoring.metrics_server")
        self.metrics = self._create_metrics()
        self.server_thread: Optional[threading.Thread] = None
        self.running = False
        self.start_time = time.time()
        self.log_updater = None

    def _create_metrics(self) -> Dict[str, Any]:
        portfolio_labels = ["portfolio_type", "bot_type"]
        strategy_labels = ["strategy_id", "asset", "portfolio_type", "bot_type"]

        metrics = {
            "portfolio_equity_total": Gauge(
                "portfolio_equity_total",
                "Total portfolio equity",
                portfolio_labels,
            ),
            "portfolio_drawdown": Gauge(
                "portfolio_drawdown",
                "Current drawdown",
                portfolio_labels,
            ),
            "strategy_trades_total": Counter(
                "strategy_trades_total",
                "Total trades by strategy",
                strategy_labels,
            ),
            "strategy_win_rate": Gauge(
                "strategy_win_rate",
                "Win rate by strategy",
                strategy_labels,
            ),
            "strategy_profit_loss": Gauge(
                "strategy_profit_loss",
                "Profit/Loss by strategy",
                strategy_labels,
            ),
            "market_regime": Gauge(
                "market_regime",
                "Current market regime",
                ["regime_type", "volatility_level", "bot_type"],
            ),
            "system_uptime_seconds": Gauge(
                "system_uptime_seconds", "System uptime in seconds"
            ),
            "last_update_timestamp": Gauge(
                "last_update_timestamp", "Last metrics update timestamp"
            ),
            "forex_spread": Gauge(
                "forex_spread",
                "Current forex spread",
                ["currency_pair", "broker"],
            ),
            "forex_swap": Gauge(
                "forex_swap",
                "Current forex swap",
                ["currency_pair", "broker", "position_type"],
            ),
            "metrics_update_duration_seconds": Histogram(
                "metrics_update_duration_seconds",
                "Histogram of metrics update duration",
                buckets=(0.1, 0.5, 1, 2, 5, 10),
            ),
        }

        return metrics

    def set_log_updater(self, updater) -> None:
        self.log_updater = updater

    def start(self) -> None:
        if self.running:
            self.log.warning("Metrics server already running")
            return

        port = self.config.get("ports", {}).get("metrics", 8080)
        try:
            start_http_server(port)
            self.log.info("Metrics server listening on port %s", port)
        except OSError as exc:
            self.log.error("Failed to start metrics server: %s", exc)
            raise

        self.running = True
        self.server_thread = threading.Thread(
            target=self._update_loop, name="monitoring-metrics-updater", daemon=True
        )
        self.server_thread.start()

    def stop(self) -> None:
        self.running = False

    def _update_loop(self) -> None:
        while self.running:
            start_time = time.time()
            try:
                self.metrics["system_uptime_seconds"].set(
                    time.time() - self.start_time
                )
                self.metrics["last_update_timestamp"].set(time.time())

                if self.log_updater is not None:
                    snapshot = self.log_updater.collect_snapshot()
                    self._update_metrics_from_snapshot(snapshot)

            except Exception as exc:
                self.log.exception("Error updating metrics: %s", exc)

            duration = time.time() - start_time
            self.metrics["metrics_update_duration_seconds"].observe(duration)
            sleep_for = max(self.scrape_interval - duration, 1)
            time.sleep(sleep_for)

    def _update_metrics_from_snapshot(self, snapshot: Dict[str, Any]) -> None:
        portfolio_metrics = snapshot.get("portfolio", {})
        for key, value in portfolio_metrics.items():
            bot_type = value.get("bot_type", "crypto")
            portfolio_type = value.get("portfolio_type", "default")
            equity = value.get("equity")
            drawdown = value.get("drawdown")

            if equity is not None:
                self.metrics["portfolio_equity_total"].labels(
                    portfolio_type=portfolio_type, bot_type=bot_type
                ).set(equity)

            if drawdown is not None:
                self.metrics["portfolio_drawdown"].labels(
                    portfolio_type=portfolio_type, bot_type=bot_type
                ).set(drawdown)

        strategy_metrics = snapshot.get("strategies", [])
        for strategy in strategy_metrics:
            labels = {
                "strategy_id": strategy.get("strategy_id", "unknown"),
                "asset": strategy.get("asset", "unknown"),
                "portfolio_type": strategy.get("portfolio_type", "default"),
                "bot_type": strategy.get("bot_type", "crypto"),
            }

            trades = strategy.get("trades")
            if trades is not None:
                counter = self.metrics["strategy_trades_total"].labels(**labels)
                increment = strategy.get("trades_increment", trades)
                counter.inc(max(increment, 0))

            win_rate = strategy.get("win_rate")
            if win_rate is not None:
                self.metrics["strategy_win_rate"].labels(**labels).set(win_rate)

            pnl = strategy.get("pnl")
            if pnl is not None:
                self.metrics["strategy_profit_loss"].labels(**labels).set(pnl)

        regime = snapshot.get("regime")
        if isinstance(regime, dict):
            self.metrics["market_regime"].labels(
                regime_type=regime.get("state", "unknown"),
                volatility_level=regime.get("volatility", "unknown"),
                bot_type=regime.get("bot_type", "crypto"),
            ).set(1)

        forex = snapshot.get("forex", {})
        spread = forex.get("spread")
        if spread:
            for pair, value in spread.items():
                self.metrics["forex_spread"].labels(
                    currency_pair=pair, broker=forex.get("broker", "unknown")
                ).set(value)

        swap = forex.get("swap")
        if swap:
            for pair, swap_info in swap.items():
                for position_type, value in swap_info.items():
                    self.metrics["forex_swap"].labels(
                        currency_pair=pair,
                        broker=forex.get("broker", "unknown"),
                        position_type=position_type,
                    ).set(value)
