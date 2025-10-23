"""
Prometheus Server - Servidor HTTP para métricas Prometheus
"""

import asyncio
import logging
from aiohttp import web
from aiohttp.web import Request, Response
import time
from typing import Dict, Any
from metrics_collector import global_metrics_collector

logger = logging.getLogger(__name__)

class PrometheusServer:
    """Servidor HTTP para métricas Prometheus"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_get("/metrics", self.metrics_handler)
        self.app.router.add_get("/health", self.health_handler)
        self.app.router.add_get("/", self.root_handler)
        self.logger = logging.getLogger("PrometheusServer")
    
    async def metrics_handler(self, request: Request) -> Response:
        """Handler para endpoint /metrics"""
        try:
            # Obtener métricas en formato Prometheus
            metrics_data = global_metrics_collector.export_prometheus_format()
            
            return Response(
                text=metrics_data,
                content_type="text/plain; version=0.0.4; charset=utf-8"
            )
        except Exception as e:
            self.logger.error(f"Error generating metrics: {e}")
            return Response(
                text=f"# ERROR: {e}\n",
                content_type="text/plain; version=0.0.4; charset=utf-8",
                status=500
            )
    
    async def health_handler(self, request: Request) -> Response:
        """Handler para endpoint /health"""
        try:
            # Obtener estado de salud básico
            bot_status = global_metrics_collector.get_metric("bot_status")
            websocket_status = global_metrics_collector.get_metric("websocket_connected")
            
            health_data = {
                "status": "healthy" if (bot_status and bot_status.value > 0) else "unhealthy",
                "timestamp": time.time(),
                "bot_running": bool(bot_status and bot_status.value > 0),
                "websocket_connected": bool(websocket_status and websocket_status.value > 0)
            }
            
            return Response(
                json=health_data,
                content_type="application/json"
            )
        except Exception as e:
            self.logger.error(f"Error in health check: {e}")
            return Response(
                json={"status": "error", "error": str(e)},
                content_type="application/json",
                status=500
            )
    
    async def root_handler(self, request: Request) -> Response:
        """Handler para endpoint raíz"""
        return Response(
            text="Trading Bot Metrics Server\n\nEndpoints:\n- /metrics - Prometheus metrics\n- /health - Health check\n",
            content_type="text/plain"
        )
    
    async def start(self):
        """Iniciar servidor"""
        try:
            runner = web.AppRunner(self.app)
            await runner.setup()
            
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            
            self.logger.info(f"Prometheus server started on {self.host}:{self.port}")
            self.logger.info(f"Metrics available at: http://{self.host}:{self.port}/metrics")
            self.logger.info(f"Health check at: http://{self.host}:{self.port}/health")
            
            return runner
        except Exception as e:
            self.logger.error(f"Failed to start Prometheus server: {e}")
            raise
    
    async def stop(self, runner):
        """Detener servidor"""
        try:
            await runner.cleanup()
            self.logger.info("Prometheus server stopped")
        except Exception as e:
            self.logger.error(f"Error stopping Prometheus server: {e}")

async def start_prometheus_server(host: str = "0.0.0.0", port: int = 8080):
    """Función helper para iniciar el servidor Prometheus"""
    server = PrometheusServer(host, port)
    runner = await server.start()
    return server, runner

if __name__ == "__main__":
    # Test del servidor
    async def main():
        server = PrometheusServer()
        runner = await server.start()
        
        try:
            # Mantener el servidor corriendo
            await asyncio.sleep(3600)  # 1 hora
        except KeyboardInterrupt:
            print("Stopping server...")
        finally:
            await server.stop(runner)
    
    asyncio.run(main())
