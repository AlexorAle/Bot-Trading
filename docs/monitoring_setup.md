# Monitoring Setup Guide

## Overview
This guide covers the setup and configuration of the comprehensive monitoring system for the trading bot, including Prometheus metrics collection, Grafana dashboards, and alerting.

## Architecture
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Bot Monitor**: Centralized monitoring system
- **Metrics Server**: HTTP endpoint for metrics exposure

## Local Development Checklist
- [ ] Docker + Docker Compose installed
- [ ] `.env` configured with `GRAFANA_PASSWORD`, optional `API_KEY`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Start monitoring stack: `docker-compose -f monitoring/docker-compose.yml up -d`
- [ ] Verify Prometheus targets: http://localhost:9090/targets
- [ ] Access Grafana: http://localhost:3000 (`admin` / password)
- [ ] Check metrics endpoint: http://localhost:8080/metrics

## VPS Deployment Checklist
- [ ] Harden firewall (allow 3000, 9090, 8080)
- [ ] Configure reverse proxy with TLS
- [ ] Set environment variables (`VPS_HOST`, `ALLOWED_ORIGINS`, `API_KEY`)
- [ ] Enable Grafana authentication and change default password
- [ ] Adjust Prometheus retention per storage limits
- [ ] Configure backups for Grafana data volume
- [ ] Set up alert notification channels (email, Slack, etc.)

## Security Checklist
- [ ] Restrict `ALLOWED_ORIGINS`
- [ ] Use API key for metrics endpoint in production
- [ ] Enable HTTPS via proxy
- [ ] Secure Prometheus admin API (reverse proxy or firewall)
- [ ] Regularly rotate credentials
- [ ] Monitor for exporter downtime alerts

## Multi-Bot Support
- [ ] Register additional bots via `BotMonitor.register_bot()`
- [ ] Create dedicated dashboards per bot type
- [ ] Ensure log directories listed in `monitoring_config.yaml`
- [ ] Update alert rules for new metrics

## Available Metrics

### Bot Metrics
- `bot_status`: Bot running status (1=running, 0=stopped)
- `total_equity`: Current total equity
- `daily_pnl`: Daily profit and loss
- `total_trades`: Total number of trades executed
- `active_positions`: Number of active positions

### Strategy Metrics
- `strategy_equity`: Equity per strategy
- `strategy_pnl`: PnL per strategy
- `strategy_trades`: Trades per strategy
- `strategy_win_rate`: Win rate per strategy

### Market Regime Metrics
- `current_market_regime`: Current market regime
- `regime_detection_duration_seconds`: Time to detect regime

### Risk Parity Metrics
- `risk_parity_weight`: Allocated weight per strategy
- `risk_parity_rebalance_count`: Number of rebalances

## Commands
```bash
# Start monitoring stack
docker-compose -f monitoring/docker-compose.yml up -d

# Stop stack
docker-compose -f monitoring/docker-compose.yml down

# Tail Prometheus logs
docker logs -f trading-prometheus

# Tail Grafana logs
docker logs -f trading-grafana

# Check metrics endpoint
curl http://localhost:8080/metrics

# Health check
curl http://localhost:8080/health
```

## Integration with Trading Bot

### Basic Integration
```python
from monitoring.bot_monitor import get_monitor

# Get monitor instance
monitor = get_monitor()

# Start metrics server
monitor.start_metrics_server(port=8080)

# Register bot
monitor.register_bot(
    bot_id="main_bot",
    bot_type="crypto",
    config={"symbols": ["BTC/USDT", "ETH/USDT"]}
)

# Update bot status
monitor.update_bot_status(
    bot_id="main_bot",
    status="running",
    equity=10000.0,
    trades=150,
    positions=2
)
```

### Strategy Integration
```python
# Update strategy metrics
monitor.update_strategy_metrics(
    strategy_name="VolatilityBreakout",
    symbol="BTC/USDT",
    equity=5000.0,
    pnl=250.0,
    trades=25,
    win_rate=0.68
)
```

## Troubleshooting

### Common Issues
1. **Metrics not appearing**: Check if metrics server is running on port 8080
2. **Prometheus can't scrape**: Verify `host.docker.internal:8080` is accessible
3. **Grafana login issues**: Check `GRAFANA_PASSWORD` environment variable
4. **High memory usage**: Adjust Prometheus retention settings

### Log Locations
- Prometheus: `docker logs trading-prometheus`
- Grafana: `docker logs trading-grafana`
- Bot Monitor: Application logs

## Performance Considerations
- Prometheus retention: 200h by default (adjust based on storage)
- Scrape interval: 15s for development, 30s for production
- Metrics cardinality: Keep labels minimal to avoid high memory usage
- Alert frequency: Configure appropriate `for` durations to avoid noise
