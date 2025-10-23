"""
Health Check Endpoint - API endpoint para health checks
"""

import json
import asyncio
from typing import Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from health_checker import TradingBotHealthChecker

class HealthEndpoint:
    """Endpoint de health check para el dashboard"""
    
    def __init__(self, bot_instance=None):
        self.bot_instance = bot_instance
        self.health_checker = TradingBotHealthChecker(bot_instance)
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Obtener estado de salud completo"""
        try:
            # Run all health checks
            health_results = await self.health_checker.run_all_checks()
            overall_status = self.health_checker.get_overall_status()
            summary = self.health_checker.get_status_summary()
            
            return {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_status": overall_status.value,
                "summary": summary,
                "checks": {
                    name: {
                        "status": check.status.value,
                        "message": check.message,
                        "response_time_ms": check.response_time_ms,
                        "timestamp": check.timestamp.isoformat(),
                        "details": check.details or {}
                    }
                    for name, check in health_results.items()
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "overall_status": "unknown"
            }
    
    async def get_quick_health(self) -> Dict[str, Any]:
        """Obtener health check rápido (solo estado general)"""
        try:
            overall_status = self.health_checker.get_overall_status()
            summary = self.health_checker.get_status_summary()
            
            return {
                "status": "success",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "overall_status": overall_status.value,
                "healthy_checks": summary["healthy_checks"],
                "warning_checks": summary["warning_checks"],
                "critical_checks": summary["critical_checks"],
                "total_checks": summary["total_checks"]
            }
        except Exception as e:
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "overall_status": "unknown"
            }

# Función para usar desde el dashboard
async def get_bot_health_status() -> Dict[str, Any]:
    """Función helper para obtener estado de salud del bot"""
    try:
        # Intentar importar el bot si está disponible
        from paper_trading_main import VSTRUTradingBot
        
        # Crear endpoint
        endpoint = HealthEndpoint()
        
        # Obtener estado rápido
        return await endpoint.get_quick_health()
        
    except ImportError:
        # Si no se puede importar el bot, retornar estado desconocido
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": "Bot not available",
            "overall_status": "unknown"
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "overall_status": "unknown"
        }

if __name__ == "__main__":
    # Test del endpoint
    async def test_health():
        endpoint = HealthEndpoint()
        health = await endpoint.get_health_status()
        print(json.dumps(health, indent=2))
    
    asyncio.run(test_health())
