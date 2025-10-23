#!/bin/bash

# Setup Infrastructure Script
# Este script configura la infraestructura para el bot de trading

SCRIPT_DIR="/home/alex/proyectos/bot-trading"
INFRASTRUCTURE_DIR="$SCRIPT_DIR/infrastructure"
LOG_FILE="$SCRIPT_DIR/logs/infrastructure_setup.log"

echo "Setting up infrastructure for Trading Bot..."

# Crear directorio de logs si no existe
mkdir -p "$SCRIPT_DIR/logs"

# Función para logging
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log "Starting infrastructure setup..."

# 1. Verificar dependencias del sistema
log "Checking system dependencies..."

# Verificar Docker
if command -v docker &> /dev/null; then
    log "✅ Docker is installed"
    docker --version
else
    log "❌ Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    log "✅ Docker installed. Please log out and back in for group changes."
fi

# Verificar Docker Compose
if command -v docker-compose &> /dev/null; then
    log "✅ Docker Compose is installed"
    docker-compose --version
else
    log "❌ Docker Compose not found. Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    log "✅ Docker Compose installed"
fi

# Verificar Python y pip
if command -v python3 &> /dev/null; then
    log "✅ Python3 is installed"
    python3 --version
else
    log "❌ Python3 not found. Installing Python3..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
    log "✅ Python3 installed"
fi

# 2. Configurar entorno virtual
log "Setting up Python virtual environment..."

if [ ! -d "$SCRIPT_DIR/venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    log "✅ Virtual environment created"
else
    log "✅ Virtual environment already exists"
fi

# Activar entorno virtual
source "$SCRIPT_DIR/venv/bin/activate"

# Instalar dependencias
log "Installing Python dependencies..."
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"
pip install streamlit fastapi uvicorn prometheus-client psutil docker
log "✅ Python dependencies installed"

# 3. Configurar Docker Compose
log "Setting up Docker Compose configuration..."

# Crear directorio de infraestructura
mkdir -p "$INFRASTRUCTURE_DIR"

# Verificar que docker-compose.yml existe
if [ -f "$INFRASTRUCTURE_DIR/docker-compose.yml" ]; then
    log "✅ Docker Compose configuration found"
else
    log "❌ Docker Compose configuration not found"
    exit 1
fi

# 4. Configurar systemd services
log "Setting up systemd services..."

# Copiar archivos de systemd
sudo cp "$INFRASTRUCTURE_DIR/systemd/trading-bot.service" /etc/systemd/system/
sudo cp "$INFRASTRUCTURE_DIR/systemd/streamlit-dashboard.service" /etc/systemd/system/

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicios
sudo systemctl enable trading-bot.service
sudo systemctl enable streamlit-dashboard.service

log "✅ Systemd services configured"

# 5. Configurar Nginx
log "Setting up Nginx reverse proxy..."

# Instalar Nginx
if command -v nginx &> /dev/null; then
    log "✅ Nginx is installed"
else
    log "Installing Nginx..."
    sudo apt update
    sudo apt install -y nginx
    log "✅ Nginx installed"
fi

# Copiar configuración de Nginx
sudo cp "$INFRASTRUCTURE_DIR/nginx/nginx.conf" /etc/nginx/nginx.conf

# Verificar configuración
sudo nginx -t
if [ $? -eq 0 ]; then
    log "✅ Nginx configuration is valid"
    sudo systemctl restart nginx
    sudo systemctl enable nginx
    log "✅ Nginx started and enabled"
else
    log "❌ Nginx configuration is invalid"
    exit 1
fi

# 6. Configurar Prometheus y Grafana
log "Setting up monitoring stack..."

# Crear directorios para Prometheus y Grafana
mkdir -p "$INFRASTRUCTURE_DIR/prometheus"
mkdir -p "$INFRASTRUCTURE_DIR/grafana/provisioning/datasources"
mkdir -p "$INFRASTRUCTURE_DIR/grafana/provisioning/dashboards"

# Verificar que prometheus.yml existe
if [ -f "$INFRASTRUCTURE_DIR/prometheus.yml" ]; then
    log "✅ Prometheus configuration found"
else
    log "❌ Prometheus configuration not found"
    exit 1
fi

# 7. Configurar firewall
log "Setting up firewall..."

# Verificar si ufw está instalado
if command -v ufw &> /dev/null; then
    log "Configuring UFW firewall..."
    
    # Permitir SSH
    sudo ufw allow ssh
    
    # Permitir puertos HTTP y HTTPS
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    
    # Permitir puertos de servicios
    sudo ufw allow 8080/tcp  # Trading Bot metrics
    sudo ufw allow 8501/tcp  # Streamlit Dashboard
    sudo ufw allow 3000/tcp  # Investment Dashboard
    sudo ufw allow 9090/tcp  # Prometheus
    sudo ufw allow 3001/tcp  # Grafana
    
    # Habilitar firewall
    sudo ufw --force enable
    
    log "✅ Firewall configured"
else
    log "⚠️ UFW not found. Please configure firewall manually"
fi

# 8. Configurar SSL/TLS (opcional)
log "Setting up SSL/TLS..."

# Crear directorio para certificados
mkdir -p "$INFRASTRUCTURE_DIR/nginx/ssl"

# Generar certificado autofirmado para desarrollo
if [ ! -f "$INFRASTRUCTURE_DIR/nginx/ssl/cert.pem" ]; then
    log "Generating self-signed certificate for development..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$INFRASTRUCTURE_DIR/nginx/ssl/key.pem" \
        -out "$INFRASTRUCTURE_DIR/nginx/ssl/cert.pem" \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    log "✅ Self-signed certificate generated"
else
    log "✅ SSL certificate already exists"
fi

# 9. Configurar backups
log "Setting up backup configuration..."

# Crear directorio de backups
mkdir -p "$SCRIPT_DIR/backups"

# Configurar cron job para backups
log "Setting up backup cron job..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd $SCRIPT_DIR && python3 scripts/backup_automation.py backup --schedule >> $SCRIPT_DIR/logs/backup_cron.log 2>&1") | crontab -

log "✅ Backup cron job configured"

# 10. Verificar configuración
log "Verifying infrastructure setup..."

# Verificar que todos los servicios pueden iniciarse
log "Testing service configurations..."

# Test Docker Compose
cd "$INFRASTRUCTURE_DIR"
if docker-compose config > /dev/null 2>&1; then
    log "✅ Docker Compose configuration is valid"
else
    log "❌ Docker Compose configuration is invalid"
fi

# Test systemd services
if systemctl is-enabled trading-bot.service > /dev/null 2>&1; then
    log "✅ Trading Bot service is enabled"
else
    log "❌ Trading Bot service is not enabled"
fi

if systemctl is-enabled streamlit-dashboard.service > /dev/null 2>&1; then
    log "✅ Streamlit Dashboard service is enabled"
else
    log "❌ Streamlit Dashboard service is not enabled"
fi

# Test Nginx
if sudo nginx -t > /dev/null 2>&1; then
    log "✅ Nginx configuration is valid"
else
    log "❌ Nginx configuration is invalid"
fi

# 11. Mostrar resumen
log "Infrastructure setup completed!"
log "=========================================="
log "Services configured:"
log "  - Trading Bot (systemd + docker-compose)"
log "  - Streamlit Dashboard (systemd + docker-compose)"
log "  - Investment Dashboard (docker-compose)"
log "  - Prometheus (docker-compose)"
log "  - Grafana (docker-compose)"
log "  - Nginx Reverse Proxy"
log "  - Redis Cache"
log "  - PostgreSQL Database"
log ""
log "Ports configured:"
log "  - 80/443: Nginx (HTTP/HTTPS)"
log "  - 8080: Trading Bot metrics"
log "  - 8501: Streamlit Dashboard"
log "  - 3000: Investment Dashboard"
log "  - 9090: Prometheus"
log "  - 3001: Grafana"
log ""
log "Next steps:"
log "  1. Start services: sudo systemctl start trading-bot streamlit-dashboard"
log "  2. Or use Docker Compose: cd infrastructure && docker-compose up -d"
log "  3. Check logs: journalctl -u trading-bot -f"
log "  4. Access dashboard: http://localhost:8501"
log ""
log "Logs saved to: $LOG_FILE"
