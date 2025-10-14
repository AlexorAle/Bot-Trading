Guía de Implementación: Monitoreo Unificado con Grafana y Prometheus
Framework: Python + Backtrader con Grafana y Prometheus
Versión: Octubre 2025
Autor: Grok AI Assistant (Revisado y adaptado por Gemini AI)
Estado: Guía de implementación para CURSOR IDE — Fase 3 del Roadmap Maestro

🎯 OBJETIVO GENERAL DEL TUTORIAL
Esta guía explica cómo incorporar Grafana como herramienta de monitoreo visual en tiempo real para el portafolio de bots de trading. Grafana actuará como el frontend del MetricsHub planificado.

Beneficios Clave:

Monitoreo unificado de estrategias en cripto y futuro forex.

Visualización de métricas clave (PnL neto, drawdown, equity curves, win rate, y correlaciones).

Alertas en tiempo real basadas en los objetivos de Fase 2 (Win Rate >45%, Drawdown <1%).

🧱 INTEGRACIÓN CON LA ARQUITECTURA EXISTENTE
Grafana se conecta vía Prometheus (base de datos de series temporales) para recolectar métricas expuestas por los bots en Python.

Componente Maestro	Rol en el Monitoreo (Grafana)
PortfolioManager	Expone métricas agregadas (PnL total, drawdown por portafolio).
RiskParityAllocator	Visualiza pesos dinámicos y rebalanceos en gráficos.
MarketRegimeDetector	Dashboards por régimen (bull/bear) con alertas de activación.
Hybrid Logging System (.jsonl)	Los logs se parsean para obtener las métricas base que Prometheus scrapea.
MetricsHub (en desarrollo)	Grafana actúa como el frontend final del MetricsHub.

Exportar a Hojas de cálculo
🛠️ PREREQUISITOS PARA LA IMPLEMENTACIÓN
Asegúrate de tener:

VPS/Server: Con Ubuntu o similar para despliegue remoto.

Docker: Instalado para ejecutar los contenedores de Prometheus y Grafana.

Librería Python: prometheus_client (pip install prometheus_client).

Bots: Estrategias operativas de Fase 2 (Win Rate ≈33%, DD <1% actuales).

⚙️ PASOS PARA INTEGRAR GRAFANA (Tutorial Paso a Paso)
1. Instalar y Configurar Prometheus
Prometheus recolecta las métricas expuestas por los bots.

Instalación vía Docker: Crea un archivo docker-compose.yml:

YAML

version: '3'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
Configurar prometheus.yml: Define el job para hacer scrape de tus bots (el endpoint será expuesto por Python):

YAML

scrape_configs:
  - job_name: 'trading_bots'
    static_configs:
      - targets: ['host.docker.internal:8000']  # Ajustar a la IP/host de tu bot en el VPS
2. Exponer Métricas desde el Bot en Python
Implementa prometheus_client en el PortfolioManager o en un thread secundario para exponer los datos en el puerto 8000.

Acción para CURSOR:

Define las métricas clave usando labels para diferenciar entre activos (crypto/forex) y estrategias (strategy_id).

Crea una función (e.g., update_and_expose_metrics()) que lea periódicamente (cada 60 segundos) el estado del PortfolioEngine y los datos del Hybrid Logging System (.jsonl).

Implementa el siguiente código para exponer los datos:

Python

from prometheus_client import start_http_server, Gauge
import time

# Metrics Definition (aligned with project architecture)
pnl_net = Gauge('pnl_net_total', 'PnL neto total', ['portfolio_type'])
drawdown_percent = Gauge('drawdown_percent', 'Drawdown porcentual', ['strategy_id', 'asset'])
equity = Gauge('equity_curve', 'Equity actual', ['portfolio_type'])
# Añadir: risk_parity_weight

def expose_metrics():
    start_http_server(8000)  # Endpoint /metrics
    while True:
        # Lógica: Actualizar los valores de las Gauges leyendo del PortfolioManager
        pnl_net.labels('crypto').set(PortfolioManager.get_pnl_total('crypto')) 
        drawdown_percent.labels('ema_conservative', 'BTC').set(2.3) # Ejemplo
        time.sleep(60)
3. Configurar Grafana
Agrega Grafana a tu stack de Docker.

Instalación: Añade el servicio al docker-compose.yml:

YAML

services:
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
Acceso: Ejecuta docker-compose up -d. Accede a http://IP_VPS:3000.

Conectar Datasource: Conecta Prometheus (URL: http://prometheus:9090).

4. Crear Dashboards y Alertas
Acción para CURSOR:

Panel de Rendimiento: Crea un gráfico de línea para las curvas de equity (Cripto y Forex).

Panel de Riesgo (Risk Parity): Crea un gráfico de barras que muestre el peso actual de cada estrategia (Cripto/Forex) usando la métrica risk_parity_weight.

Alertas: Configura reglas de notificación (email/Slack) basadas en tus objetivos:

Alerta de Riesgo: Si drawdown_percent{portfolio_type="crypto"} > 1.0 (tu límite de Fase 2).

Alerta de Rendimiento: Si win_rate_average{strategy_id="..."} < 45 (tu objetivo de Fase 2).

⏭️ PRÓXIMOS PASOS (FASE 3 - Roadmap Consolidado)
Tarea	Descripción	Estado
1. Despliegue de Monitoreo	Completar la implementación de Docker (Prometheus/Grafana) y prometheus_client.	🟢 En Curso
2. MetricsHub Dashboard	Configuración final de los paneles de Grafana para visualizar KPIs, correlaciones y performance.	🔜 Planificada
3. Multi-símbolo Testing	Backtesting expandido: BTC, ETH, SOL, BNB.	🔜 Planificada
4. ML Regime Prediction	Integrar el Modelo SVM/LSTM para anticipar regímenes y mostrar predicciones en el Dashboard de Grafana.	🔜 Planificada
5. Dynamic Parameter Adjustment	Ajuste adaptativo según equity rolling y volatilidad.	🔜 Planificada
