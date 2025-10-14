"""Monitoring registry for multiple bot instances."""

import threading
import time
from typing import Any, Dict, Optional

from .logger import get_monitoring_logger


class BotMonitor:
    """Track registered bots and update metrics server with their data."""

    def __init__(self) -> None:
        self.bots: Dict[str, Dict[str, Any]] = {}
        self.metrics_server = None
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.log = get_monitoring_logger("monitoring.bot_monitor")

    def register_bot(self, bot_id: str, bot_type: str, bot_instance: Any) -> None:
        self.bots[bot_id] = {
            "type": bot_type,
            "instance": bot_instance,
            "last_metrics": {},
            "last_update": time.time(),
            "status": "active",
        }
        self.log.info("Registered bot %s (%s)", bot_id, bot_type)

    def unregister_bot(self, bot_id: str) -> None:
        if bot_id in self.bots:
            del self.bots[bot_id]
            self.log.info("Unregistered bot %s", bot_id)

    def get_bot_status(self, bot_id: str) -> Dict[str, Any]:
        bot = self.bots.get(bot_id)
        if not bot:
            return {"status": "not_found"}
        return {
            "status": bot.get("status", "unknown"),
            "type": bot.get("type"),
            "last_update": bot.get("last_update"),
        }

    def start_monitoring(self, metrics_server, interval: int = 10) -> None:
        if self.running:
            self.log.warning("Bot monitoring already running")
            return

        self.metrics_server = metrics_server
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="monitoring-bot-registry",
            daemon=True,
            args=(interval,),
        )
        self.monitor_thread.start()

    def stop_monitoring(self) -> None:
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

    def _monitor_loop(self, interval: int) -> None:
        while self.running:
            try:
                for bot_id, bot_info in list(self.bots.items()):
                    instance = bot_info.get("instance")
                    if instance is None:
                        continue

                    if hasattr(instance, "get_metrics"):
                        try:
                            metrics = instance.get_metrics()
                            bot_info["last_metrics"] = metrics
                            bot_info["last_update"] = time.time()
                            bot_info["status"] = "active"
                            if self.metrics_server:
                                self.metrics_server._update_metrics_from_snapshot(metrics)
                        except Exception as exc:
                            self.log.exception(
                                "Error collecting metrics from %s: %s", bot_id, exc
                            )
                            bot_info["status"] = "error"
                    else:
                        self.log.debug("Bot %s has no get_metrics method", bot_id)

                time.sleep(interval)
            except Exception as exc:
                self.log.exception("Error in bot monitoring loop: %s", exc)
                time.sleep(interval)
