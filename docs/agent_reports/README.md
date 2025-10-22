# 📁 Agent Reports - Punto de Intercambio de Documentación

Esta carpeta es el **punto central de comunicación** entre agentes que trabajan en el proyecto del Trading Bot.

## 🎯 Propósito

Permitir que diferentes agentes (QA, desarrollo, optimización) **compartan información, hallazgos y recomendaciones** de manera estructurada y asíncrona.

## 📋 Reportes Disponibles

### QA Reports
- `QA_AGENT_REPORT_Signal_Injection_Testing_2025-10-18.md` - Pruebas de inyección de señales y ejecución de órdenes

### Development Reports
- (Pendiente) - Añadir reportes de desarrollo aquí

### Optimization Reports
- (Pendiente) - Añadir reportes de optimización de estrategias aquí

## 📝 Convenciones

### Nombres de Archivos
```
[TIPO]_AGENT_REPORT_[Descripción]_[YYYY-MM-DD].md
```

Ejemplos:
- `QA_AGENT_REPORT_Signal_Injection_Testing_2025-10-18.md`
- `DEV_AGENT_REPORT_Bug_Fix_SELL_Orders_2025-10-19.md`
- `OPT_AGENT_REPORT_Strategy_Calibration_2025-10-20.md`

### Formato del Reporte

Cada reporte debe incluir:

1. **Encabezado:**
   - Fecha y hora
   - Agente que genera el reporte
   - Objetivo/Propósito
   - Estado final

2. **Resumen Ejecutivo:**
   - Qué se hizo
   - Resultados principales
   - Issues encontrados

3. **Detalles Técnicos:**
   - Metodología
   - Comandos/Scripts usados
   - Archivos modificados

4. **Resultados:**
   - Métricas
   - Evidencias (logs, screenshots)
   - Bugs/Observaciones

5. **Recomendaciones:**
   - Para el siguiente agente
   - Prioridades
   - Preguntas abiertas

6. **Referencias:**
   - Links a otros reportes
   - Comandos para reproducir
   - Archivos relacionados

## 🔄 Flujo de Trabajo

1. **Agente completa su trabajo** → Genera reporte en esta carpeta
2. **Siguiente agente lee el reporte** → Entiende contexto y pendientes
3. **Agente implementa cambios** → Genera nuevo reporte con resultados
4. **Ciclo se repite** → Documentación continua y trazabilidad

## 🚨 Issues Críticos Actuales

### 🔴 URGENTE
- **Bug SELL ETHUSDT:** Error en `risk_manager.py` - `'PaperPosition' object has no attribute 'get'`
  - Reporte: `QA_AGENT_REPORT_Signal_Injection_Testing_2025-10-18.md`
  - Prioridad: CRÍTICA
  - Asignado a: Development Agent

### 🟡 IMPORTANTE
- **Estrategias con baja confianza:** Señales generadas con confidence < 0.7
  - Reporte: `QA_AGENT_REPORT_Signal_Injection_Testing_2025-10-18.md`
  - Prioridad: ALTA
  - Asignado a: Optimization Agent

## 📞 Comunicación Entre Agentes

### Para dejar un mensaje al siguiente agente:

Crea un archivo de "handoff" con el formato:
```
HANDOFF_[TU_AGENTE]_to_[SIGUIENTE_AGENTE]_[FECHA].md
```

Ejemplo:
```markdown
# HANDOFF: QA Agent → Development Agent

**Fecha:** 2025-10-18
**De:** QA Automation Agent
**Para:** Development Agent

## Contexto Rápido
El bot está funcionando al 66.67%. Bug crítico en SELL de ETHUSDT.

## Acción Requerida
Fix el bug en risk_manager.py línea XX

## Archivos Relevantes
- backtrader_engine/risk_manager.py
- QA_AGENT_REPORT_Signal_Injection_Testing_2025-10-18.md

## Testing Después del Fix
Ejecutar: python temp_test_sell_signals.py
```

## 🛠️ Herramientas

### Ver reportes recientes
```powershell
dir docs\agent_reports | Sort-Object LastWriteTime -Descending
```

### Buscar en reportes
```powershell
Get-Content docs\agent_reports\*.md | Select-String "palabra_clave"
```

### Crear nuevo reporte
```python
from datetime import datetime
template = f"""
# [TIPO]_AGENT_REPORT_[Descripción]_{datetime.now().strftime('%Y-%m-%d')}.md

**Fecha:** {datetime.now().isoformat()}
**Agente:** [Tu Nombre]
**Objetivo:** [Describir objetivo]

## Resumen Ejecutivo
[Tu resumen aquí]

## Detalles
[Detalles técnicos]

## Resultados
[Resultados y evidencias]

## Recomendaciones
[Para el siguiente agente]
"""
```

## 📊 Estado del Proyecto

**Última actualización:** 2025-10-18 15:30:00 UTC

### Componentes
- ✅ Bot Principal: OPERACIONAL
- ✅ WebSocket Bybit: CONECTADO
- ✅ Risk Manager: FUNCIONANDO (con 1 bug)
- ✅ Alert Manager: OPERATIVO
- ⚠️ Estrategias: NECESITAN CALIBRACIÓN

### Métricas Actuales
- Tasa de éxito: 66.67%
- Uptime: 25+ minutos
- Órdenes ejecutadas: 4/6

### Próximos Pasos
1. Fix bug SELL ETHUSDT
2. Calibrar estrategias
3. Agregar tests unitarios

---

**Nota:** Este directorio es monitoreado por todos los agentes. Mantén la documentación actualizada y clara.
