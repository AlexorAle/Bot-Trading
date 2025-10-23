#!/usr/bin/env python3
"""
Deployment Script - Script para deployment automatizado
"""

import asyncio
import sys
import logging
import argparse
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backtrader_engine.deployment_manager import DeploymentManager, DeploymentConfig, InfrastructureType

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deployment.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def deploy_docker_compose(environment: str = "production"):
    """Deploy usando Docker Compose"""
    logger.info(f"Starting Docker Compose deployment for {environment}")
    
    config = DeploymentConfig(
        environment=environment,
        infrastructure_type=InfrastructureType.DOCKER_COMPOSE,
        docker_compose_file="infrastructure/docker-compose.yml",
        health_checks=[
            "http://localhost:8080/health",
            "http://localhost:8501",
            "http://localhost:3000"
        ],
        rollback_enabled=True,
        backup_before_deploy=True
    )
    
    deployment_manager = DeploymentManager(config)
    result = await deployment_manager.deploy()
    
    return result

async def deploy_systemd(environment: str = "production"):
    """Deploy usando systemd"""
    logger.info(f"Starting systemd deployment for {environment}")
    
    config = DeploymentConfig(
        environment=environment,
        infrastructure_type=InfrastructureType.SYSTEMD,
        systemd_services=[
            "trading-bot.service",
            "streamlit-dashboard.service",
            "investment-dashboard.service"
        ],
        health_checks=[
            "http://localhost:8080/health",
            "http://localhost:8501",
            "http://localhost:3000"
        ],
        rollback_enabled=True,
        backup_before_deploy=True
    )
    
    deployment_manager = DeploymentManager(config)
    result = await deployment_manager.deploy()
    
    return result

async def deploy_kubernetes(environment: str = "production"):
    """Deploy usando Kubernetes"""
    logger.info(f"Starting Kubernetes deployment for {environment}")
    
    config = DeploymentConfig(
        environment=environment,
        infrastructure_type=InfrastructureType.KUBERNETES,
        kubernetes_config="infrastructure/k8s/",
        health_checks=[
            "http://localhost:8080/health",
            "http://localhost:8501",
            "http://localhost:3000"
        ],
        rollback_enabled=True,
        backup_before_deploy=True
    )
    
    deployment_manager = DeploymentManager(config)
    result = await deployment_manager.deploy()
    
    return result

async def deploy_manual(environment: str = "production"):
    """Deploy manual"""
    logger.info(f"Starting manual deployment for {environment}")
    
    config = DeploymentConfig(
        environment=environment,
        infrastructure_type=InfrastructureType.MANUAL,
        health_checks=[
            "http://localhost:8080/health",
            "http://localhost:8501",
            "http://localhost:3000"
        ],
        rollback_enabled=True,
        backup_before_deploy=True
    )
    
    deployment_manager = DeploymentManager(config)
    result = await deployment_manager.deploy()
    
    return result

async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Trading Bot Deployment")
    parser.add_argument("infrastructure", choices=[
        "docker-compose", "systemd", "kubernetes", "manual"
    ], help="Infrastructure type for deployment")
    parser.add_argument("--environment", default="production", 
                       help="Deployment environment")
    parser.add_argument("--output", help="Output file for deployment report")
    parser.add_argument("--force", action="store_true", 
                       help="Force deployment even if checks fail")
    parser.add_argument("--verbose", action="store_true", 
                       help="Verbose output")
    
    args = parser.parse_args()
    
    try:
        # Select deployment method
        if args.infrastructure == "docker-compose":
            result = await deploy_docker_compose(args.environment)
        elif args.infrastructure == "systemd":
            result = await deploy_systemd(args.environment)
        elif args.infrastructure == "kubernetes":
            result = await deploy_kubernetes(args.environment)
        elif args.infrastructure == "manual":
            result = await deploy_manual(args.environment)
        
        # Mostrar resultado
        print(f"\n{'='*60}")
        print(f"DEPLOYMENT REPORT")
        print(f"{'='*60}")
        print(f"Deployment ID: {result.deployment_id}")
        print(f"Status: {result.status.value}")
        print(f"Start Time: {result.start_time}")
        print(f"End Time: {result.end_time}")
        print(f"Duration: {result.duration_seconds:.1f} seconds")
        
        if result.services_deployed:
            print(f"Services Deployed: {', '.join(result.services_deployed)}")
        
        if result.services_failed:
            print(f"Services Failed: {', '.join(result.services_failed)}")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        # Mostrar logs
        if result.logs:
            print(f"\nDeployment Logs:")
            for log in result.logs:
                print(f"  {log}")
        
        # Guardar reporte si se especifica archivo
        if args.output:
            report = {
                "deployment_id": result.deployment_id,
                "status": result.status.value,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "duration_seconds": result.duration_seconds,
                "services_deployed": result.services_deployed,
                "services_failed": result.services_failed,
                "logs": result.logs,
                "error_message": result.error_message
            }
            
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Deployment report saved to: {args.output}")
        
        # Determinar código de salida
        if result.status.value == "completed":
            print(f"\n✅ Deployment completed successfully!")
            sys.exit(0)
        elif result.status.value == "failed":
            print(f"\n❌ Deployment failed!")
            sys.exit(1)
        elif result.status.value == "rolled_back":
            print(f"\n🔄 Deployment rolled back!")
            sys.exit(2)
        else:
            print(f"\n⚠️ Deployment status: {result.status.value}")
            sys.exit(3)
    
    except KeyboardInterrupt:
        logger.info("Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
