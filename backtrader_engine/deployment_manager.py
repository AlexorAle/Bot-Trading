"""
Deployment Manager - Sistema completo de deployment e infraestructura
"""

import asyncio
import logging
import time
import json
import subprocess
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path
import psutil
import docker
import yaml

logger = logging.getLogger(__name__)

class DeploymentStatus(Enum):
    """Estado de deployment"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

class InfrastructureType(Enum):
    """Tipos de infraestructura"""
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    SYSTEMD = "systemd"
    MANUAL = "manual"

@dataclass
class DeploymentConfig:
    """Configuración de deployment"""
    environment: str
    infrastructure_type: InfrastructureType
    docker_compose_file: Optional[str] = None
    kubernetes_config: Optional[str] = None
    systemd_services: List[str] = None
    health_checks: List[str] = None
    rollback_enabled: bool = True
    backup_before_deploy: bool = True
    
    def __post_init__(self):
        if self.systemd_services is None:
            self.systemd_services = []
        if self.health_checks is None:
            self.health_checks = []

@dataclass
class DeploymentResult:
    """Resultado de deployment"""
    deployment_id: str
    status: DeploymentStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    services_deployed: List[str] = None
    services_failed: List[str] = None
    logs: List[str] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.services_deployed is None:
            self.services_deployed = []
        if self.services_failed is None:
            self.services_failed = []
        if self.logs is None:
            self.logs = []

class DeploymentManager:
    """Gestor de deployment e infraestructura"""
    
    def __init__(self, config: DeploymentConfig):
        self.config = config
        self.logger = logging.getLogger("DeploymentManager")
        self.deployment_history: List[DeploymentResult] = []
        self.current_deployment: Optional[DeploymentResult] = None
        
        # Configuración de infraestructura
        self.docker_client = None
        self.systemd_services = [
            "trading-bot.service",
            "streamlit-dashboard.service",
            "investment-dashboard.service"
        ]
        
        self.logger.info(f"DeploymentManager initialized for {config.environment}")
    
    async def deploy(self, force: bool = False) -> DeploymentResult:
        """Ejecutar deployment completo"""
        deployment_id = f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.info(f"Starting deployment: {deployment_id}")
        
        # Crear resultado de deployment
        self.current_deployment = DeploymentResult(
            deployment_id=deployment_id,
            status=DeploymentStatus.IN_PROGRESS,
            start_time=datetime.now(timezone.utc)
        )
        
        try:
            # 1. Pre-deployment checks
            await self._pre_deployment_checks()
            
            # 2. Backup before deployment
            if self.config.backup_before_deploy:
                await self._backup_before_deployment()
            
            # 3. Deploy based on infrastructure type
            if self.config.infrastructure_type == InfrastructureType.DOCKER_COMPOSE:
                await self._deploy_docker_compose()
            elif self.config.infrastructure_type == InfrastructureType.KUBERNETES:
                await self._deploy_kubernetes()
            elif self.config.infrastructure_type == InfrastructureType.SYSTEMD:
                await self._deploy_systemd()
            else:
                await self._deploy_manual()
            
            # 4. Post-deployment health checks
            await self._post_deployment_health_checks()
            
            # 5. Update deployment status
            self.current_deployment.status = DeploymentStatus.COMPLETED
            self.current_deployment.end_time = datetime.now(timezone.utc)
            self.current_deployment.duration_seconds = (
                self.current_deployment.end_time - self.current_deployment.start_time
            ).total_seconds()
            
            self.logger.info(f"Deployment completed successfully: {deployment_id}")
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            self.current_deployment.status = DeploymentStatus.FAILED
            self.current_deployment.error_message = str(e)
            self.current_deployment.end_time = datetime.now(timezone.utc)
            
            # Rollback if enabled
            if self.config.rollback_enabled:
                await self._rollback_deployment()
        
        # Add to history
        self.deployment_history.append(self.current_deployment)
        
        return self.current_deployment
    
    async def _pre_deployment_checks(self):
        """Verificaciones pre-deployment"""
        self.logger.info("Running pre-deployment checks...")
        
        # Check system resources
        await self._check_system_resources()
        
        # Check dependencies
        await self._check_dependencies()
        
        # Check configuration
        await self._check_configuration()
        
        # Check network connectivity
        await self._check_network_connectivity()
        
        self.logger.info("Pre-deployment checks completed")
    
    async def _check_system_resources(self):
        """Verificar recursos del sistema"""
        try:
            # Check memory
            memory = psutil.virtual_memory()
            if memory.available < 1024 * 1024 * 1024:  # 1GB
                raise Exception("Insufficient memory available")
            
            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.free < 5 * 1024 * 1024 * 1024:  # 5GB
                raise Exception("Insufficient disk space")
            
            # Check CPU
            cpu_count = psutil.cpu_count()
            if cpu_count < 2:
                raise Exception("Insufficient CPU cores")
            
            self.logger.info("System resources check passed")
            
        except Exception as e:
            self.logger.error(f"System resources check failed: {e}")
            raise
    
    async def _check_dependencies(self):
        """Verificar dependencias"""
        try:
            # Check Python packages
            required_packages = [
                'pandas', 'numpy', 'requests', 'psutil', 'asyncio',
                'streamlit', 'fastapi', 'ccxt', 'docker'
            ]
            
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    raise Exception(f"Required package not installed: {package}")
            
            # Check system tools
            system_tools = ['docker', 'docker-compose', 'git']
            for tool in system_tools:
                try:
                    subprocess.run([tool, '--version'], capture_output=True, check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    raise Exception(f"Required system tool not available: {tool}")
            
            self.logger.info("Dependencies check passed")
            
        except Exception as e:
            self.logger.error(f"Dependencies check failed: {e}")
            raise
    
    async def _check_configuration(self):
        """Verificar configuración"""
        try:
            # Check critical files
            critical_files = [
                'configs/alert_config.json',
                'configs/bybit_x_config.json',
                '.env'
            ]
            
            for file_path in critical_files:
                if not Path(file_path).exists():
                    raise Exception(f"Critical file not found: {file_path}")
            
            # Check environment variables
            import os
            required_env_vars = ['EXCHANGE', 'API_KEY', 'SECRET', 'SYMBOL']
            for env_var in required_env_vars:
                if not os.getenv(env_var):
                    raise Exception(f"Required environment variable not set: {env_var}")
            
            self.logger.info("Configuration check passed")
            
        except Exception as e:
            self.logger.error(f"Configuration check failed: {e}")
            raise
    
    async def _check_network_connectivity(self):
        """Verificar conectividad de red"""
        try:
            import socket
            import requests
            
            # Check DNS resolution
            socket.gethostbyname('google.com')
            
            # Check HTTP connectivity
            response = requests.get('https://httpbin.org/status/200', timeout=10)
            if response.status_code != 200:
                raise Exception("HTTP connectivity test failed")
            
            self.logger.info("Network connectivity check passed")
            
        except Exception as e:
            self.logger.error(f"Network connectivity check failed: {e}")
            raise
    
    async def _backup_before_deployment(self):
        """Crear backup antes del deployment"""
        try:
            from backup_manager import global_backup_manager, BackupType
            
            self.logger.info("Creating backup before deployment...")
            
            backup_id = await global_backup_manager.create_backup(
                BackupType.FULL,
                f"Pre-deployment backup - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            
            self.current_deployment.logs.append(f"Backup created: {backup_id}")
            self.logger.info(f"Pre-deployment backup created: {backup_id}")
            
        except Exception as e:
            self.logger.error(f"Pre-deployment backup failed: {e}")
            raise
    
    async def _deploy_docker_compose(self):
        """Deploy usando Docker Compose"""
        try:
            self.logger.info("Deploying with Docker Compose...")
            
            # Check if docker-compose file exists
            compose_file = self.config.docker_compose_file or "docker-compose.yml"
            if not Path(compose_file).exists():
                raise Exception(f"Docker Compose file not found: {compose_file}")
            
            # Stop existing services
            subprocess.run(['docker-compose', 'down'], check=True)
            self.current_deployment.logs.append("Stopped existing services")
            
            # Pull latest images
            subprocess.run(['docker-compose', 'pull'], check=True)
            self.current_deployment.logs.append("Pulled latest images")
            
            # Start services
            subprocess.run(['docker-compose', 'up', '-d'], check=True)
            self.current_deployment.logs.append("Started services")
            
            # Wait for services to be ready
            await asyncio.sleep(10)
            
            # Check service status
            result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
            self.current_deployment.logs.append(f"Service status: {result.stdout}")
            
            self.logger.info("Docker Compose deployment completed")
            
        except Exception as e:
            self.logger.error(f"Docker Compose deployment failed: {e}")
            raise
    
    async def _deploy_kubernetes(self):
        """Deploy usando Kubernetes"""
        try:
            self.logger.info("Deploying with Kubernetes...")
            
            # Check if kubectl is available
            subprocess.run(['kubectl', 'version'], check=True)
            
            # Apply Kubernetes configurations
            k8s_config = self.config.kubernetes_config or "k8s/"
            if Path(k8s_config).exists():
                subprocess.run(['kubectl', 'apply', '-f', k8s_config], check=True)
                self.current_deployment.logs.append(f"Applied Kubernetes config: {k8s_config}")
            
            # Wait for deployments to be ready
            await asyncio.sleep(30)
            
            # Check deployment status
            result = subprocess.run(['kubectl', 'get', 'deployments'], capture_output=True, text=True)
            self.current_deployment.logs.append(f"Deployment status: {result.stdout}")
            
            self.logger.info("Kubernetes deployment completed")
            
        except Exception as e:
            self.logger.error(f"Kubernetes deployment failed: {e}")
            raise
    
    async def _deploy_systemd(self):
        """Deploy usando systemd"""
        try:
            self.logger.info("Deploying with systemd...")
            
            # Stop existing services
            for service in self.systemd_services:
                try:
                    subprocess.run(['sudo', 'systemctl', 'stop', service], check=True)
                    self.current_deployment.logs.append(f"Stopped service: {service}")
                except subprocess.CalledProcessError:
                    self.logger.warning(f"Service not running: {service}")
            
            # Reload systemd
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
            self.current_deployment.logs.append("Reloaded systemd daemon")
            
            # Start services
            for service in self.systemd_services:
                try:
                    subprocess.run(['sudo', 'systemctl', 'start', service], check=True)
                    subprocess.run(['sudo', 'systemctl', 'enable', service], check=True)
                    self.current_deployment.services_deployed.append(service)
                    self.current_deployment.logs.append(f"Started service: {service}")
                except subprocess.CalledProcessError as e:
                    self.current_deployment.services_failed.append(service)
                    self.logger.error(f"Failed to start service {service}: {e}")
            
            # Wait for services to be ready
            await asyncio.sleep(5)
            
            self.logger.info("Systemd deployment completed")
            
        except Exception as e:
            self.logger.error(f"Systemd deployment failed: {e}")
            raise
    
    async def _deploy_manual(self):
        """Deploy manual"""
        try:
            self.logger.info("Manual deployment...")
            
            # This would be customized based on specific requirements
            # For now, just log the manual deployment
            self.current_deployment.logs.append("Manual deployment executed")
            
            self.logger.info("Manual deployment completed")
            
        except Exception as e:
            self.logger.error(f"Manual deployment failed: {e}")
            raise
    
    async def _post_deployment_health_checks(self):
        """Health checks post-deployment"""
        self.logger.info("Running post-deployment health checks...")
        
        # Check if services are running
        await self._check_services_running()
        
        # Check health endpoints
        await self._check_health_endpoints()
        
        # Check system resources
        await self._check_system_resources()
        
        self.logger.info("Post-deployment health checks completed")
    
    async def _check_services_running(self):
        """Verificar que los servicios están corriendo"""
        try:
            if self.config.infrastructure_type == InfrastructureType.DOCKER_COMPOSE:
                result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
                if "Up" not in result.stdout:
                    raise Exception("Docker services not running")
            
            elif self.config.infrastructure_type == InfrastructureType.SYSTEMD:
                for service in self.systemd_services:
                    result = subprocess.run(['systemctl', 'is-active', service], capture_output=True, text=True)
                    if result.stdout.strip() != "active":
                        raise Exception(f"Service not active: {service}")
            
            self.logger.info("Services running check passed")
            
        except Exception as e:
            self.logger.error(f"Services running check failed: {e}")
            raise
    
    async def _check_health_endpoints(self):
        """Verificar endpoints de health"""
        try:
            import requests
            
            # Check trading bot health
            try:
                response = requests.get('http://localhost:8080/health', timeout=5)
                if response.status_code == 200:
                    self.current_deployment.logs.append("Trading bot health check passed")
                else:
                    raise Exception("Trading bot health check failed")
            except Exception as e:
                self.logger.warning(f"Trading bot health check failed: {e}")
            
            # Check Streamlit dashboard
            try:
                response = requests.get('http://localhost:8501', timeout=5)
                if response.status_code == 200:
                    self.current_deployment.logs.append("Streamlit dashboard health check passed")
                else:
                    raise Exception("Streamlit dashboard health check failed")
            except Exception as e:
                self.logger.warning(f"Streamlit dashboard health check failed: {e}")
            
            # Check Investment Dashboard
            try:
                response = requests.get('http://localhost:3000', timeout=5)
                if response.status_code == 200:
                    self.current_deployment.logs.append("Investment dashboard health check passed")
                else:
                    raise Exception("Investment dashboard health check failed")
            except Exception as e:
                self.logger.warning(f"Investment dashboard health check failed: {e}")
            
            self.logger.info("Health endpoints check completed")
            
        except Exception as e:
            self.logger.error(f"Health endpoints check failed: {e}")
            raise
    
    async def _rollback_deployment(self):
        """Rollback del deployment"""
        try:
            self.logger.info("Rolling back deployment...")
            
            if self.config.infrastructure_type == InfrastructureType.DOCKER_COMPOSE:
                # Rollback Docker Compose
                subprocess.run(['docker-compose', 'down'], check=True)
                self.current_deployment.logs.append("Rolled back Docker Compose services")
            
            elif self.config.infrastructure_type == InfrastructureType.SYSTEMD:
                # Rollback systemd services
                for service in self.systemd_services:
                    try:
                        subprocess.run(['sudo', 'systemctl', 'stop', service], check=True)
                        self.current_deployment.logs.append(f"Rolled back service: {service}")
                    except subprocess.CalledProcessError:
                        self.logger.warning(f"Service not running during rollback: {service}")
            
            # Restore from backup if available
            try:
                from backup_manager import global_backup_manager
                backups = global_backup_manager.list_backups()
                if backups:
                    latest_backup = max(backups, key=lambda x: x.created_at)
                    await global_backup_manager.restore_backup(latest_backup.id)
                    self.current_deployment.logs.append(f"Restored from backup: {latest_backup.id}")
            except Exception as e:
                self.logger.warning(f"Backup restore failed: {e}")
            
            self.current_deployment.status = DeploymentStatus.ROLLED_BACK
            self.logger.info("Deployment rollback completed")
            
        except Exception as e:
            self.logger.error(f"Deployment rollback failed: {e}")
            raise
    
    def get_deployment_status(self) -> Dict[str, Any]:
        """Obtener estado del deployment"""
        return {
            "current_deployment": self.current_deployment,
            "deployment_history": [
                {
                    "deployment_id": d.deployment_id,
                    "status": d.status.value,
                    "start_time": d.start_time.isoformat(),
                    "end_time": d.end_time.isoformat() if d.end_time else None,
                    "duration_seconds": d.duration_seconds,
                    "services_deployed": d.services_deployed,
                    "services_failed": d.services_failed
                }
                for d in self.deployment_history
            ],
            "config": {
                "environment": self.config.environment,
                "infrastructure_type": self.config.infrastructure_type.value,
                "rollback_enabled": self.config.rollback_enabled,
                "backup_before_deploy": self.config.backup_before_deploy
            }
        }
    
    def get_deployment_summary(self) -> Dict[str, Any]:
        """Obtener resumen de deployments"""
        total_deployments = len(self.deployment_history)
        successful_deployments = len([d for d in self.deployment_history if d.status == DeploymentStatus.COMPLETED])
        failed_deployments = len([d for d in self.deployment_history if d.status == DeploymentStatus.FAILED])
        rolled_back_deployments = len([d for d in self.deployment_history if d.status == DeploymentStatus.ROLLED_BACK])
        
        return {
            "total_deployments": total_deployments,
            "successful_deployments": successful_deployments,
            "failed_deployments": failed_deployments,
            "rolled_back_deployments": rolled_back_deployments,
            "success_rate": (successful_deployments / total_deployments * 100) if total_deployments > 0 else 0,
            "average_duration_seconds": sum(d.duration_seconds for d in self.deployment_history) / total_deployments if total_deployments > 0 else 0
        }
