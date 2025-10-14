"""Log-based metrics collector for monitoring."""

import glob
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logger import get_monitoring_logger


@dataclass
class StrategyMetrics:
    strategy_id: str
    asset: str
    portfolio_type: str
    bot_type: str
    trades: int
    win_rate: float
    pnl: float
    trades_increment: int = 0


@dataclass
class PortfolioMetrics:
    portfolio_type: str
    bot_type: str
    equity: float
    drawdown: float


@dataclass
class RegimeMetrics:
    state: str
    volatility: str
    bot_type: str


@dataclass
class ForexMetrics:
    broker: str
    spread: Dict[str, float] = field(default_factory=dict)
    swap: Dict[str, Dict[str, float]] = field(default_factory=dict)


class LogMetricsUpdater:
    """Aggregate metrics from log files for Prometheus exporter."""

    def __init__(self, directories: List[str], bot_types: Optional[List[str]] = None):
        self.directories = directories
        self.bot_types = bot_types or ["crypto"]
        self.log = get_monitoring_logger("monitoring.log_metrics_updater")
        self.last_trades_count: Dict[str, int] = {}

    def collect_snapshot(self) -> Dict[str, Any]:
        portfolio = {}
        strategies = []
        regime = None
        forex = None

        for pattern in self.directories:
            for folder in glob.glob(pattern):
                folder_path = Path(folder)
                if not folder_path.is_dir():
                    continue

                bot_type = self._infer_bot_type(folder_path)
                summary = self._load_portfolio_summary(folder_path)
                if summary:
                    portfolio_key = folder_path.name
                    portfolio[portfolio_key] = {
                        "portfolio_type": summary.get("portfolio_type", portfolio_key),
                        "bot_type": bot_type,
                        "equity": summary.get("total_equity"),
                        "drawdown": summary.get("drawdown"),
                    }

                strategies.extend(
                    self._parse_strategy_logs(folder_path, bot_type)
                )

                regime = regime or self._parse_regime(folder_path, bot_type)
                forex = forex or self._parse_forex(folder_path)

        return {
            "portfolio": portfolio,
            "strategies": [s.__dict__ for s in strategies],
            "regime": regime.__dict__ if regime else None,
            "forex": forex.__dict__ if forex else None,
        }

    def _infer_bot_type(self, folder_path: Path) -> str:
        name = folder_path.name.lower()
        if "forex" in name:
            return "forex"
        if "ml" in name:
            return "ml"
        return "crypto"

    def _load_portfolio_summary(self, folder_path: Path) -> Optional[Dict[str, Any]]:
        summary_file = folder_path / "portfolio_summary.json"
        if not summary_file.exists():
            return None

        try:
            with summary_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            portfolio_results = data.get("portfolio_results", {})
            total_equity = 0
            total_drawdown = 0
            if isinstance(portfolio_results, dict):
                for _symbol, strategies in portfolio_results.items():
                    for _strategy, details in strategies.items():
                        performance = details.get("performance", {})
                        total_equity += performance.get("final_value", 0)
                        analyzer = details.get("analyzers", {}).get("drawdown", {})
                        max_dd = analyzer.get("max", {}).get("drawdown")
                        if max_dd is not None:
                            total_drawdown = max(total_drawdown, max_dd)

            return {
                "total_equity": total_equity,
                "drawdown": total_drawdown,
                "portfolio_type": data.get("session_id", folder_path.name),
            }
        except json.JSONDecodeError as exc:
            self.log.error("Failed to parse %s: %s", summary_file, exc)
        except Exception as exc:
            self.log.exception("Unexpected error reading %s: %s", summary_file, exc)

        return None

    def _parse_strategy_logs(self, folder_path: Path, bot_type: str) -> List[StrategyMetrics]:
        strategies_dir = folder_path / "strategies"
        metrics: List[StrategyMetrics] = []

        if not strategies_dir.exists():
            return metrics

        for json_file in strategies_dir.glob("*.json"):
            try:
                with json_file.open("r", encoding="utf-8") as fh:
                    data = json.load(fh)

                strategy_id = data.get("strategy")
                asset = data.get("symbol", "unknown")
                portfolio_type = data.get("portfolio", folder_path.name)
                trades = data.get("trades", 0)
                win_rate = data.get("win_rate", 0)
                pnl = data.get("total_pnl", 0)

                key = f"{strategy_id}:{asset}:{portfolio_type}:{bot_type}"
                previous = self.last_trades_count.get(key, 0)
                increment = max(trades - previous, 0)
                self.last_trades_count[key] = trades

                metrics.append(
                    StrategyMetrics(
                        strategy_id=strategy_id,
                        asset=asset,
                        portfolio_type=portfolio_type,
                        bot_type=bot_type,
                        trades=trades,
                        win_rate=win_rate,
                        pnl=pnl,
                        trades_increment=increment,
                    )
                )

            except json.JSONDecodeError as exc:
                self.log.error("Failed to parse strategy file %s: %s", json_file, exc)
            except Exception as exc:
                self.log.exception("Error parsing strategy file %s: %s", json_file, exc)

        return metrics

    def _parse_regime(self, folder_path: Path, bot_type: str) -> Optional[RegimeMetrics]:
        regime_file = folder_path / "regime_detection.jsonl"
        if not regime_file.exists():
            return None

        try:
            last_line = self._read_last_line(regime_file)
            if not last_line:
                return None
            data = json.loads(last_line)
            return RegimeMetrics(
                state=data.get("regime", "unknown"),
                volatility=data.get("volatility", "unknown"),
                bot_type=bot_type,
            )
        except json.JSONDecodeError as exc:
            self.log.error("Failed to parse regime file %s: %s", regime_file, exc)
        except Exception as exc:
            self.log.exception("Error reading regime file %s: %s", regime_file, exc)
        return None

    def _parse_forex(self, folder_path: Path) -> Optional[ForexMetrics]:
        forex_file = folder_path / "forex_metrics.json"
        if not forex_file.exists():
            return None

        try:
            with forex_file.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return ForexMetrics(
                broker=data.get("broker", "unknown"),
                spread=data.get("spread", {}),
                swap=data.get("swap", {}),
            )
        except json.JSONDecodeError as exc:
            self.log.error("Failed to parse forex file %s: %s", forex_file, exc)
        except Exception as exc:
            self.log.exception("Error reading forex file %s: %s", forex_file, exc)
        return None

    def _read_last_line(self, file_path: Path) -> Optional[str]:
        try:
            with file_path.open("r", encoding="utf-8") as fh:
                fh.seek(0, 2)
                filesize = fh.tell()
                buffer = bytearray()
                pointer = filesize - 1

                while pointer >= 0:
                    fh.seek(pointer)
                    char = fh.read(1)
                    if char == "\n" and buffer:
                        break
                    buffer.extend(char.encode("utf-8"))
                    pointer -= 1

                return buffer[::-1].decode("utf-8") if buffer else None
        except OSError as exc:
            self.log.error("Error reading file %s: %s", file_path, exc)
        return None
