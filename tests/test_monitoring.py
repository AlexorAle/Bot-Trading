import json
import os
import tempfile
import time
import unittest
from unittest.mock import MagicMock

from monitoring.metrics_server import MetricsServer
from monitoring.log_metrics_updater import LogMetricsUpdater


class TestMonitoring(unittest.TestCase):
    def setUp(self):
        self.test_config = {
            "ports": {"metrics": 9101},
            "scrape_interval": 1,
        }

    def test_metrics_server_initializes(self):
        server = MetricsServer(self.test_config)
        server.set_log_updater(MagicMock(collect_snapshot=lambda: {}))
        server.start()
        time.sleep(2)
        server.stop()
        self.assertTrue(server.running is False)

    def test_log_metrics_updater_parses_strategy_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            strategies_dir = os.path.join(tmpdir, "strategies")
            os.makedirs(strategies_dir)

            strategy_file = os.path.join(strategies_dir, "test_strategy.json")
            with open(strategy_file, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "strategy": "TestStrategy",
                        "symbol": "BTCUSDT",
                        "portfolio": "portfolio_1",
                        "performance": {"final_value": 10500, "total_return": 5.0},
                        "analyzers": {
                            "trades": {
                                "total": {"total": 10},
                                "won": {"total": 6},
                            }
                        },
                    },
                    fh,
                )

            updater = LogMetricsUpdater([tmpdir])
            snapshot = updater.collect_snapshot()

            self.assertIn("strategies", snapshot)
            self.assertEqual(snapshot["strategies"][0]["strategy_id"], "TestStrategy")


if __name__ == "__main__":
    unittest.main()
