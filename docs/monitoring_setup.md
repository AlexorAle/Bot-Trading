# Monitoring Setup Guide

## Local Development Checklist
- Docker + Docker Compose installed
- `.env` configured with `GRAFANA_PASSWORD`, optional `API_KEY`
- Install dependencies: `pip install -r requirements.txt`
- Start monitoring stack: `docker-compose -f monitoring/docker-compose.yml up -d`
- Verify Prometheus targets: http://localhost:9090/targets
- Access Grafana: http://localhost:3000 (`admin` / password)
- Check metrics endpoint: http://localhost:8080/metrics

## VPS Deployment Checklist
- Harden firewall (allow 3000, 9090, 8080)
- Configure reverse proxy with TLS
- Set environment variables (`VPS_HOST`, `ALLOWED_ORIGINS`, `API_KEY`)
- Enable Grafana authentication and change default password
- Adjust Prometheus retention per storage limits
- Configure backups for Grafana data volume
- Set up alert notification channels (email, Slack, etc.)

## Security Checklist
- Restrict `ALLOWED_ORIGINS`
- Use API key for metrics endpoint in production
- Enable HTTPS via proxy
- Secure Prometheus admin API (reverse proxy or firewall)
- Regularly rotate credentials
- Monitor for exporter downtime alerts

## Multi-Bot Support
- Register additional bots via `BotMonitor.register_bot()`
- Create dedicated dashboards per bot type
- Ensure log directories listed in `monitoring_config.yaml`
- Update alert rules for new metrics

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
```
