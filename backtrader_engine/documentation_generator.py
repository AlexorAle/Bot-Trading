"""
Documentation Generator - Sistema de generación automática de documentación
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import ast
import inspect

logger = logging.getLogger(__name__)

class DocumentationType(Enum):
    """Tipos de documentación"""
    API_DOCS = "api_docs"
    ARCHITECTURE = "architecture"
    USER_GUIDE = "user_guide"
    DEVELOPER_GUIDE = "developer_guide"
    COMPLIANCE = "compliance"
    OPERATIONS = "operations"

@dataclass
class DocumentationSection:
    """Sección de documentación"""
    title: str
    content: str
    subsections: List['DocumentationSection'] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.subsections is None:
            self.subsections = []
        if self.metadata is None:
            self.metadata = {}

class DocumentationGenerator:
    """Generador automático de documentación"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger("DocumentationGenerator")
        self.docs_dir = self.project_root / "docs"
        self.docs_dir.mkdir(exist_ok=True)
        
        # Configuración de documentación
        self.doc_config = {
            "api_docs": {
                "output_dir": "docs/api",
                "formats": ["markdown", "json"],
                "include_examples": True
            },
            "architecture": {
                "output_dir": "docs/architecture",
                "formats": ["markdown", "mermaid"],
                "include_diagrams": True
            },
            "user_guide": {
                "output_dir": "docs/user",
                "formats": ["markdown", "html"],
                "include_screenshots": True
            },
            "developer_guide": {
                "output_dir": "docs/developer",
                "formats": ["markdown", "rst"],
                "include_code_examples": True
            },
            "compliance": {
                "output_dir": "docs/compliance",
                "formats": ["markdown", "pdf"],
                "include_audit_trails": True
            },
            "operations": {
                "output_dir": "docs/operations",
                "formats": ["markdown", "yaml"],
                "include_runbooks": True
            }
        }
        
        self.logger.info("DocumentationGenerator initialized")
    
    async def generate_all_documentation(self) -> Dict[str, Any]:
        """Generar toda la documentación"""
        self.logger.info("Generating all documentation...")
        
        results = {}
        
        # Generar documentación de API
        results["api_docs"] = await self.generate_api_documentation()
        
        # Generar documentación de arquitectura
        results["architecture"] = await self.generate_architecture_documentation()
        
        # Generar guía de usuario
        results["user_guide"] = await self.generate_user_guide()
        
        # Generar guía de desarrollador
        results["developer_guide"] = await self.generate_developer_guide()
        
        # Generar documentación de compliance
        results["compliance"] = await self.generate_compliance_documentation()
        
        # Generar documentación de operaciones
        results["operations"] = await self.generate_operations_documentation()
        
        self.logger.info("All documentation generated successfully")
        return results
    
    async def generate_api_documentation(self) -> Dict[str, Any]:
        """Generar documentación de API"""
        self.logger.info("Generating API documentation...")
        
        api_docs = {
            "title": "Trading Bot API Documentation",
            "version": "2.0.0",
            "description": "Complete API documentation for the Trading Bot system",
            "endpoints": [],
            "models": [],
            "examples": []
        }
        
        # Documentar endpoints del bot
        bot_endpoints = [
            {
                "path": "/health",
                "method": "GET",
                "description": "Health check endpoint",
                "response": {
                    "status": "string",
                    "timestamp": "string",
                    "uptime": "number"
                }
            },
            {
                "path": "/metrics",
                "method": "GET",
                "description": "Prometheus metrics endpoint",
                "response": "Prometheus format metrics"
            },
            {
                "path": "/api/trading/status",
                "method": "GET",
                "description": "Get trading bot status",
                "response": {
                    "running": "boolean",
                    "balance": "number",
                    "positions": "array",
                    "signals": "array"
                }
            },
            {
                "path": "/api/trading/start",
                "method": "POST",
                "description": "Start trading bot",
                "response": {
                    "success": "boolean",
                    "message": "string"
                }
            },
            {
                "path": "/api/trading/stop",
                "method": "POST",
                "description": "Stop trading bot",
                "response": {
                    "success": "boolean",
                    "message": "string"
                }
            }
        ]
        
        api_docs["endpoints"] = bot_endpoints
        
        # Documentar modelos de datos
        data_models = [
            {
                "name": "TradingSignal",
                "description": "Trading signal data structure",
                "fields": {
                    "symbol": "string",
                    "side": "string",
                    "price": "number",
                    "confidence": "number",
                    "timestamp": "string"
                }
            },
            {
                "name": "BotState",
                "description": "Bot state data structure",
                "fields": {
                    "balance": "number",
                    "total_trades": "number",
                    "signals_generated": "number",
                    "start_time": "string",
                    "last_update": "string"
                }
            }
        ]
        
        api_docs["models"] = data_models
        
        # Guardar documentación
        output_dir = self.docs_dir / "api"
        output_dir.mkdir(exist_ok=True)
        
        # Guardar como JSON
        with open(output_dir / "api_docs.json", "w") as f:
            json.dump(api_docs, f, indent=2)
        
        # Guardar como Markdown
        markdown_content = self._generate_api_markdown(api_docs)
        with open(output_dir / "api_docs.md", "w") as f:
            f.write(markdown_content)
        
        self.logger.info("API documentation generated")
        return {"status": "success", "files": ["api_docs.json", "api_docs.md"]}
    
    async def generate_architecture_documentation(self) -> Dict[str, Any]:
        """Generar documentación de arquitectura"""
        self.logger.info("Generating architecture documentation...")
        
        architecture_docs = {
            "title": "Trading Bot Architecture",
            "version": "2.0.0",
            "description": "Complete architecture documentation for the Trading Bot system",
            "components": [],
            "diagrams": [],
            "deployment": {}
        }
        
        # Documentar componentes principales
        components = [
            {
                "name": "Trading Bot Core",
                "description": "Main trading bot orchestrator",
                "file": "backtrader_engine/paper_trading_main.py",
                "dependencies": ["signal_engine", "exchanges", "state_manager"],
                "responsibilities": [
                    "Signal generation",
                    "Trade execution",
                    "State management",
                    "Error handling"
                ]
            },
            {
                "name": "Signal Engine",
                "description": "Trading signal generation system",
                "file": "backtrader_engine/signal_engine.py",
                "dependencies": ["technical_indicators", "ml_models"],
                "responsibilities": [
                    "Technical analysis",
                    "ML model inference",
                    "Signal validation",
                    "Signal ranking"
                ]
            },
            {
                "name": "Exchange Interface",
                "description": "Exchange API integration",
                "file": "backtrader_engine/exchanges/bybit_paper_trader.py",
                "dependencies": ["ccxt", "websocket"],
                "responsibilities": [
                    "Market data streaming",
                    "Order execution",
                    "Position management",
                    "Balance tracking"
                ]
            },
            {
                "name": "State Manager",
                "description": "Bot state persistence",
                "file": "backtrader_engine/state_manager.py",
                "dependencies": ["json", "datetime"],
                "responsibilities": [
                    "State serialization",
                    "State persistence",
                    "State recovery",
                    "Auto-save"
                ]
            },
            {
                "name": "Error Handler",
                "description": "Error handling and recovery",
                "file": "backtrader_engine/error_handler.py",
                "dependencies": ["logging", "asyncio"],
                "responsibilities": [
                    "Error classification",
                    "Circuit breakers",
                    "Retry logic",
                    "Error reporting"
                ]
            },
            {
                "name": "Health Checker",
                "description": "System health monitoring",
                "file": "backtrader_engine/health_checker.py",
                "dependencies": ["psutil", "requests"],
                "responsibilities": [
                    "System health checks",
                    "Service monitoring",
                    "Health reporting",
                    "Alert generation"
                ]
            },
            {
                "name": "Metrics Collector",
                "description": "Metrics collection and export",
                "file": "backtrader_engine/metrics_collector.py",
                "dependencies": ["prometheus_client"],
                "responsibilities": [
                    "Metrics collection",
                    "Metrics export",
                    "Performance tracking",
                    "System monitoring"
                ]
            },
            {
                "name": "Alert Manager",
                "description": "Alert and notification system",
                "file": "backtrader_engine/alert_manager.py",
                "dependencies": ["telegram", "email"],
                "responsibilities": [
                    "Alert generation",
                    "Notification delivery",
                    "Rate limiting",
                    "Alert history"
                ]
            },
            {
                "name": "Backup Manager",
                "description": "Backup and recovery system",
                "file": "backtrader_engine/backup_manager.py",
                "dependencies": ["tarfile", "hashlib"],
                "responsibilities": [
                    "Backup creation",
                    "Backup restoration",
                    "Backup integrity",
                    "Backup cleanup"
                ]
            },
            {
                "name": "Disaster Recovery",
                "description": "Disaster recovery system",
                "file": "backtrader_engine/disaster_recovery.py",
                "dependencies": ["backup_manager"],
                "responsibilities": [
                    "Disaster detection",
                    "Recovery planning",
                    "Recovery execution",
                    "System validation"
                ]
            }
        ]
        
        architecture_docs["components"] = components
        
        # Generar diagramas Mermaid
        mermaid_diagrams = [
            self._generate_system_architecture_diagram(),
            self._generate_data_flow_diagram(),
            self._generate_deployment_diagram()
        ]
        
        architecture_docs["diagrams"] = mermaid_diagrams
        
        # Guardar documentación
        output_dir = self.docs_dir / "architecture"
        output_dir.mkdir(exist_ok=True)
        
        # Guardar como JSON
        with open(output_dir / "architecture.json", "w") as f:
            json.dump(architecture_docs, f, indent=2)
        
        # Guardar como Markdown
        markdown_content = self._generate_architecture_markdown(architecture_docs)
        with open(output_dir / "architecture.md", "w") as f:
            f.write(markdown_content)
        
        # Guardar diagramas Mermaid
        for i, diagram in enumerate(mermaid_diagrams):
            with open(output_dir / f"diagram_{i+1}.mmd", "w") as f:
                f.write(diagram)
        
        self.logger.info("Architecture documentation generated")
        return {"status": "success", "files": ["architecture.json", "architecture.md", "diagram_1.mmd", "diagram_2.mmd", "diagram_3.mmd"]}
    
    async def generate_user_guide(self) -> Dict[str, Any]:
        """Generar guía de usuario"""
        self.logger.info("Generating user guide...")
        
        user_guide = {
            "title": "Trading Bot User Guide",
            "version": "2.0.0",
            "description": "Complete user guide for the Trading Bot system",
            "sections": []
        }
        
        sections = [
            {
                "title": "Getting Started",
                "content": """
# Getting Started

## Prerequisites
- Python 3.10+
- Virtual environment
- API keys for exchanges
- Telegram bot token (optional)

## Installation
1. Clone the repository
2. Create virtual environment
3. Install dependencies
4. Configure environment variables
5. Run the bot

## Quick Start
```bash
# Setup environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure bot
cp .env.example .env
# Edit .env with your configuration

# Run bot
python3 backtrader_engine/paper_trading_main.py
```
                """
            },
            {
                "title": "Configuration",
                "content": """
# Configuration

## Environment Variables
- `EXCHANGE`: Exchange to use (bybit)
- `API_KEY`: Your API key
- `SECRET`: Your API secret
- `SYMBOL`: Trading symbol (BTCUSDT)
- `TIMEFRAME`: Timeframe (5m)
- `RISK_PER_TRADE`: Risk per trade (0.01)
- `LEVERAGE`: Leverage (10)
- `MODE`: Trading mode (paper/live)
- `LOG_LEVEL`: Log level (INFO)

## Configuration Files
- `configs/alert_config.json`: Alert configuration
- `configs/bybit_x_config.json`: Exchange configuration
- `.env`: Environment variables
                """
            },
            {
                "title": "Dashboard Usage",
                "content": """
# Dashboard Usage

## Accessing the Dashboard
1. Start the Streamlit dashboard
2. Open browser to http://localhost:8501
3. Use the dashboard to monitor and control the bot

## Dashboard Features
- **System Status**: Overview of all services
- **Trading Bot Control**: Start/stop/restart bot
- **Investment Dashboard**: Control investment dashboard
- **Logs**: View real-time logs
- **Metrics**: View performance metrics
                """
            },
            {
                "title": "Monitoring",
                "content": """
# Monitoring

## Health Checks
- Bot health: http://localhost:8080/health
- Dashboard: http://localhost:8501
- Metrics: http://localhost:8080/metrics

## Logs
- Bot logs: `logs/bot.log`
- Dashboard logs: `logs/streamlit.log`
- System logs: `journalctl -u trading-bot`

## Metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
                """
            },
            {
                "title": "Troubleshooting",
                "content": """
# Troubleshooting

## Common Issues
1. **Bot not starting**: Check configuration and dependencies
2. **No signals**: Check market data and indicators
3. **API errors**: Check API keys and permissions
4. **Memory issues**: Check system resources

## Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python3 backtrader_engine/paper_trading_main.py
```

## Support
- Check logs for error messages
- Verify configuration
- Test API connectivity
- Check system resources
                """
            }
        ]
        
        user_guide["sections"] = sections
        
        # Guardar documentación
        output_dir = self.docs_dir / "user"
        output_dir.mkdir(exist_ok=True)
        
        # Guardar como JSON
        with open(output_dir / "user_guide.json", "w") as f:
            json.dump(user_guide, f, indent=2)
        
        # Guardar como Markdown
        markdown_content = self._generate_user_guide_markdown(user_guide)
        with open(output_dir / "user_guide.md", "w") as f:
            f.write(markdown_content)
        
        self.logger.info("User guide generated")
        return {"status": "success", "files": ["user_guide.json", "user_guide.md"]}
    
    async def generate_developer_guide(self) -> Dict[str, Any]:
        """Generar guía de desarrollador"""
        self.logger.info("Generating developer guide...")
        
        developer_guide = {
            "title": "Trading Bot Developer Guide",
            "version": "2.0.0",
            "description": "Complete developer guide for the Trading Bot system",
            "sections": []
        }
        
        sections = [
            {
                "title": "Architecture Overview",
                "content": """
# Architecture Overview

## System Components
- **Trading Bot Core**: Main orchestrator
- **Signal Engine**: Signal generation
- **Exchange Interface**: API integration
- **State Manager**: State persistence
- **Error Handler**: Error management
- **Health Checker**: System monitoring
- **Metrics Collector**: Metrics collection
- **Alert Manager**: Notifications
- **Backup Manager**: Backup system
- **Disaster Recovery**: Recovery system

## Design Patterns
- **Observer Pattern**: Event handling
- **Strategy Pattern**: Trading strategies
- **Factory Pattern**: Component creation
- **Singleton Pattern**: Global managers
                """
            },
            {
                "title": "Development Setup",
                "content": """
# Development Setup

## Prerequisites
- Python 3.10+
- Git
- Virtual environment
- IDE (VS Code, PyCharm)

## Setup
```bash
# Clone repository
git clone <repository-url>
cd bot-trading

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Development Tools
- **Linting**: flake8, black, isort
- **Testing**: pytest, coverage
- **Type Checking**: mypy
- **Documentation**: sphinx
                """
            },
            {
                "title": "Code Structure",
                "content": """
# Code Structure

## Project Layout
```
bot-trading/
├── backtrader_engine/          # Core trading engine
│   ├── paper_trading_main.py  # Main bot orchestrator
│   ├── signal_engine.py       # Signal generation
│   ├── exchanges/             # Exchange interfaces
│   ├── strategies/            # Trading strategies
│   └── utils/                 # Utility functions
├── scripts/                   # Automation scripts
├── infrastructure/           # Infrastructure as code
├── docs/                     # Documentation
└── tests/                    # Test files
```

## Key Files
- `paper_trading_main.py`: Main bot orchestrator
- `signal_engine.py`: Signal generation system
- `exchanges/bybit_paper_trader.py`: Exchange interface
- `state_manager.py`: State persistence
- `error_handler.py`: Error handling
                """
            },
            {
                "title": "Adding New Features",
                "content": """
# Adding New Features

## Development Process
1. Create feature branch
2. Implement feature
3. Add tests
4. Update documentation
5. Create pull request

## Code Guidelines
- Follow PEP 8 style guide
- Add type hints
- Write docstrings
- Add unit tests
- Update documentation

## Testing
```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_signal_engine.py

# Run with coverage
pytest --cov=backtrader_engine
```
                """
            },
            {
                "title": "API Development",
                "content": """
# API Development

## Adding New Endpoints
1. Define endpoint in FastAPI
2. Add request/response models
3. Implement business logic
4. Add error handling
5. Write tests

## Example
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class TradingRequest(BaseModel):
    symbol: str
    side: str
    amount: float

@app.post("/api/trading/execute")
async def execute_trade(request: TradingRequest):
    try:
        result = await trading_engine.execute_trade(request)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```
                """
            }
        ]
        
        developer_guide["sections"] = sections
        
        # Guardar documentación
        output_dir = self.docs_dir / "developer"
        output_dir.mkdir(exist_ok=True)
        
        # Guardar como JSON
        with open(output_dir / "developer_guide.json", "w") as f:
            json.dump(developer_guide, f, indent=2)
        
        # Guardar como Markdown
        markdown_content = self._generate_developer_guide_markdown(developer_guide)
        with open(output_dir / "developer_guide.md", "w") as f:
            f.write(markdown_content)
        
        self.logger.info("Developer guide generated")
        return {"status": "success", "files": ["developer_guide.json", "developer_guide.md"]}
    
    async def generate_compliance_documentation(self) -> Dict[str, Any]:
        """Generar documentación de compliance"""
        self.logger.info("Generating compliance documentation...")
        
        compliance_docs = {
            "title": "Trading Bot Compliance Documentation",
            "version": "2.0.0",
            "description": "Complete compliance documentation for the Trading Bot system",
            "frameworks": [],
            "policies": [],
            "procedures": []
        }
        
        # Documentar frameworks regulatorios
        frameworks = [
            {
                "name": "MiFID II",
                "description": "Markets in Financial Instruments Directive II",
                "requirements": [
                    "Trade reporting",
                    "Transaction reporting",
                    "Best execution",
                    "Client categorization"
                ],
                "implementation": "Automated trade reporting and client categorization"
            },
            {
                "name": "GDPR",
                "description": "General Data Protection Regulation",
                "requirements": [
                    "Data protection",
                    "Privacy by design",
                    "Data subject rights",
                    "Data breach notification"
                ],
                "implementation": "Data anonymization and privacy controls"
            },
            {
                "name": "SOX",
                "description": "Sarbanes-Oxley Act",
                "requirements": [
                    "Internal controls",
                    "Audit trails",
                    "Management certification",
                    "Disclosure controls"
                ],
                "implementation": "Comprehensive audit trails and internal controls"
            }
        ]
        
        compliance_docs["frameworks"] = frameworks
        
        # Documentar políticas
        policies = [
            {
                "name": "Data Retention Policy",
                "description": "Policy for data retention and disposal",
                "retention_period": "7 years",
                "data_types": ["trade_data", "logs", "audit_trails"],
                "disposal_method": "Secure deletion"
            },
            {
                "name": "Access Control Policy",
                "description": "Policy for system access control",
                "principles": ["Least privilege", "Separation of duties", "Regular review"],
                "implementation": "Role-based access control"
            },
            {
                "name": "Risk Management Policy",
                "description": "Policy for risk management",
                "limits": {
                    "max_position_size": "10% of capital",
                    "max_daily_loss": "5% of capital",
                    "max_drawdown": "15% of capital"
                },
                "monitoring": "Real-time risk monitoring"
            }
        ]
        
        compliance_docs["policies"] = policies
        
        # Guardar documentación
        output_dir = self.docs_dir / "compliance"
        output_dir.mkdir(exist_ok=True)
        
        # Guardar como JSON
        with open(output_dir / "compliance.json", "w") as f:
            json.dump(compliance_docs, f, indent=2)
        
        # Guardar como Markdown
        markdown_content = self._generate_compliance_markdown(compliance_docs)
        with open(output_dir / "compliance.md", "w") as f:
            f.write(markdown_content)
        
        self.logger.info("Compliance documentation generated")
        return {"status": "success", "files": ["compliance.json", "compliance.md"]}
    
    async def generate_operations_documentation(self) -> Dict[str, Any]:
        """Generar documentación de operaciones"""
        self.logger.info("Generating operations documentation...")
        
        operations_docs = {
            "title": "Trading Bot Operations Documentation",
            "version": "2.0.0",
            "description": "Complete operations documentation for the Trading Bot system",
            "runbooks": [],
            "procedures": [],
            "troubleshooting": []
        }
        
        # Documentar runbooks
        runbooks = [
            {
                "name": "Bot Startup",
                "description": "Procedure for starting the trading bot",
                "steps": [
                    "Check system resources",
                    "Verify configuration",
                    "Start dependencies",
                    "Start trading bot",
                    "Verify health checks"
                ],
                "rollback": "Stop bot and check logs"
            },
            {
                "name": "Bot Shutdown",
                "description": "Procedure for shutting down the trading bot",
                "steps": [
                    "Stop new trades",
                    "Close open positions",
                    "Save state",
                    "Stop bot process",
                    "Verify shutdown"
                ],
                "rollback": "Restart bot if needed"
            },
            {
                "name": "Emergency Stop",
                "description": "Procedure for emergency stop",
                "steps": [
                    "Immediate stop signal",
                    "Close all positions",
                    "Save state",
                    "Notify stakeholders",
                    "Investigate cause"
                ],
                "rollback": "Restart after investigation"
            }
        ]
        
        operations_docs["runbooks"] = runbooks
        
        # Documentar procedimientos
        procedures = [
            {
                "name": "Daily Operations",
                "description": "Daily operational procedures",
                "schedule": "Every day at 9:00 AM",
                "tasks": [
                    "Check system health",
                    "Review overnight trades",
                    "Verify backups",
                    "Check alerts",
                    "Update documentation"
                ]
            },
            {
                "name": "Weekly Maintenance",
                "description": "Weekly maintenance procedures",
                "schedule": "Every Sunday at 2:00 AM",
                "tasks": [
                    "System updates",
                    "Security patches",
                    "Performance review",
                    "Backup verification",
                    "Log cleanup"
                ]
            },
            {
                "name": "Monthly Review",
                "description": "Monthly review procedures",
                "schedule": "First Monday of each month",
                "tasks": [
                    "Performance analysis",
                    "Risk assessment",
                    "Compliance review",
                    "Documentation update",
                    "Stakeholder report"
                ]
            }
        ]
        
        operations_docs["procedures"] = procedures
        
        # Guardar documentación
        output_dir = self.docs_dir / "operations"
        output_dir.mkdir(exist_ok=True)
        
        # Guardar como JSON
        with open(output_dir / "operations.json", "w") as f:
            json.dump(operations_docs, f, indent=2)
        
        # Guardar como Markdown
        markdown_content = self._generate_operations_markdown(operations_docs)
        with open(output_dir / "operations.md", "w") as f:
            f.write(markdown_content)
        
        self.logger.info("Operations documentation generated")
        return {"status": "success", "files": ["operations.json", "operations.md"]}
    
    def _generate_api_markdown(self, api_docs: Dict[str, Any]) -> str:
        """Generar documentación de API en Markdown"""
        content = f"""# {api_docs['title']}

**Version:** {api_docs['version']}  
**Description:** {api_docs['description']}

## Endpoints

"""
        
        for endpoint in api_docs['endpoints']:
            content += f"""### {endpoint['method']} {endpoint['path']}

**Description:** {endpoint['description']}

**Response:**
```json
{json.dumps(endpoint['response'], indent=2)}
```

"""
        
        return content
    
    def _generate_architecture_markdown(self, architecture_docs: Dict[str, Any]) -> str:
        """Generar documentación de arquitectura en Markdown"""
        content = f"""# {architecture_docs['title']}

**Version:** {architecture_docs['version']}  
**Description:** {architecture_docs['description']}

## Components

"""
        
        for component in architecture_docs['components']:
            content += f"""### {component['name']}

**Description:** {component['description']}  
**File:** `{component['file']}`

**Dependencies:**
{', '.join(component['dependencies'])}

**Responsibilities:**
{chr(10).join([f"- {resp}" for resp in component['responsibilities']])}

"""
        
        return content
    
    def _generate_user_guide_markdown(self, user_guide: Dict[str, Any]) -> str:
        """Generar guía de usuario en Markdown"""
        content = f"""# {user_guide['title']}

**Version:** {user_guide['version']}  
**Description:** {user_guide['description']}

"""
        
        for section in user_guide['sections']:
            content += f"""## {section['title']}

{section['content']}

"""
        
        return content
    
    def _generate_developer_guide_markdown(self, developer_guide: Dict[str, Any]) -> str:
        """Generar guía de desarrollador en Markdown"""
        content = f"""# {developer_guide['title']}

**Version:** {developer_guide['version']}  
**Description:** {developer_guide['description']}

"""
        
        for section in developer_guide['sections']:
            content += f"""## {section['title']}

{section['content']}

"""
        
        return content
    
    def _generate_compliance_markdown(self, compliance_docs: Dict[str, Any]) -> str:
        """Generar documentación de compliance en Markdown"""
        content = f"""# {compliance_docs['title']}

**Version:** {compliance_docs['version']}  
**Description:** {compliance_docs['description']}

## Regulatory Frameworks

"""
        
        for framework in compliance_docs['frameworks']:
            content += f"""### {framework['name']}

**Description:** {framework['description']}

**Requirements:**
{chr(10).join([f"- {req}" for req in framework['requirements']])}

**Implementation:** {framework['implementation']}

"""
        
        return content
    
    def _generate_operations_markdown(self, operations_docs: Dict[str, Any]) -> str:
        """Generar documentación de operaciones en Markdown"""
        content = f"""# {operations_docs['title']}

**Version:** {operations_docs['version']}  
**Description:** {operations_docs['description']}

## Runbooks

"""
        
        for runbook in operations_docs['runbooks']:
            content += f"""### {runbook['name']}

**Description:** {runbook['description']}

**Steps:**
{chr(10).join([f"{i+1}. {step}" for i, step in enumerate(runbook['steps'])])}

**Rollback:** {runbook['rollback']}

"""
        
        return content
    
    def _generate_system_architecture_diagram(self) -> str:
        """Generar diagrama de arquitectura del sistema"""
        return """graph TB
    subgraph "Trading Bot System"
        TB[Trading Bot Core]
        SE[Signal Engine]
        EI[Exchange Interface]
        SM[State Manager]
        EH[Error Handler]
        HC[Health Checker]
        MC[Metrics Collector]
        AM[Alert Manager]
        BM[Backup Manager]
        DR[Disaster Recovery]
    end
    
    subgraph "External Systems"
        EX[Exchange APIs]
        TG[Telegram]
        PR[Prometheus]
        GR[Grafana]
    end
    
    subgraph "Data Storage"
        FS[File System]
        DB[Database]
        BK[Backups]
    end
    
    TB --> SE
    TB --> EI
    TB --> SM
    TB --> EH
    TB --> HC
    TB --> MC
    TB --> AM
    
    EI --> EX
    AM --> TG
    MC --> PR
    PR --> GR
    
    SM --> FS
    BM --> BK
    DR --> BM
    
    style TB fill:#f9f,stroke:#333,stroke-width:4px
    style SE fill:#bbf,stroke:#333,stroke-width:2px
    style EI fill:#bbf,stroke:#333,stroke-width:2px
    style SM fill:#bbf,stroke:#333,stroke-width:2px"""
    
    def _generate_data_flow_diagram(self) -> str:
        """Generar diagrama de flujo de datos"""
        return """graph LR
    subgraph "Data Sources"
        MD[Market Data]
        SI[System Info]
        US[User Signals]
    end
    
    subgraph "Processing"
        SE[Signal Engine]
        ML[ML Models]
        TA[Technical Analysis]
    end
    
    subgraph "Execution"
        TB[Trading Bot]
        EX[Exchange Interface]
        OR[Order Management]
    end
    
    subgraph "Storage"
        ST[State Storage]
        LG[Logs]
        MT[Metrics]
    end
    
    MD --> SE
    SI --> SE
    US --> SE
    
    SE --> ML
    SE --> TA
    
    ML --> TB
    TA --> TB
    
    TB --> EX
    TB --> OR
    
    TB --> ST
    TB --> LG
    TB --> MT
    
    style SE fill:#f9f,stroke:#333,stroke-width:4px
    style TB fill:#f9f,stroke:#333,stroke-width:4px"""
    
    def _generate_deployment_diagram(self) -> str:
        """Generar diagrama de deployment"""
        return """graph TB
    subgraph "Production Environment"
        subgraph "Docker Compose"
            TB[Trading Bot]
            SD[Streamlit Dashboard]
            ID[Investment Dashboard]
            PR[Prometheus]
            GR[Grafana]
            RD[Redis]
            PG[PostgreSQL]
            NX[Nginx]
        end
        
        subgraph "Systemd Services"
            TBS[Trading Bot Service]
            SDS[Streamlit Service]
        end
        
        subgraph "Kubernetes"
            TBD[Trading Bot Deployment]
            SVD[Service Deployment]
            ING[Ingress]
        end
    end
    
    subgraph "Monitoring"
        PM[Prometheus Metrics]
        GD[Grafana Dashboards]
        AL[Alerting]
    end
    
    subgraph "Backup & Recovery"
        BK[Backup System]
        DR[Disaster Recovery]
        RS[Recovery Services]
    end
    
    TB --> PM
    SD --> PM
    ID --> PM
    
    PM --> GD
    PM --> AL
    
    TB --> BK
    SD --> BK
    ID --> BK
    
    BK --> DR
    DR --> RS
    
    style TB fill:#f9f,stroke:#333,stroke-width:4px
    style SD fill:#bbf,stroke:#333,stroke-width:2px
    style ID fill:#bbf,stroke:#333,stroke-width:2px"""

# Instancia global del generador de documentación
global_documentation_generator = DocumentationGenerator()
