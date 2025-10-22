
# ✅ CheckList para Pruebas Live del Trading Bot (Bybit)

Este documento define los pasos necesarios para lanzar una prueba en entorno real del bot de trading conectado directamente a Bybit. Se orienta a un agente técnico (Cursor) para ejecutar validaciones completas del sistema antes de la activación.

---

## ⚙️ Entorno: Live (Bybit)

---

## 1. 🔒 Verificación de Entorno de Ejecución

Antes de iniciar el bot:

- [ ] Ejecutar `check_bot_status.ps1` o `.sh` para asegurarse que **no está ya en ejecución**.
- [ ] Validar que no hay **instancias paralelas activas** (otros VPS o sesiones duplicadas).
- [ ] Verificar si hay puertos ocupados (`9090`, `3000`, `8501`) por versiones previas mal cerradas.

---

## 2. 🔐 Confirmación de Configuraciones Activas

- [ ] Confirmar que el archivo `bybit_x_config.json` contiene las **API Keys live** (no testnet).
- [ ] Validar que `alert_config.json` tiene habilitado Telegram correctamente.
- [ ] Comprobar si el modo actual es “Live” y **NO** está configurado como paper o test.

---

## 3. 📦 Inicialización de Servicios

- [ ] Ejecutar `start_bot.ps1` (o versión `.sh`) desde carpeta `executables/`.
- [ ] Confirmar en terminal: “🚀 Bot lanzado correctamente” + logs sin errores.
- [ ] Revisar que `docker-compose` haya levantado `prometheus` y `grafana`.

---

## 4. 🧪 Ciclo de Prueba con Tamaño Mínimo

Para evitar errores o pérdidas:

- [ ] Ejecutar la prueba con tamaño mínimo permitido por el par (ejemplo: `0.001 BTC`).
- [ ] Validar que la orden:
    - [ ] Se muestra en panel de Bybit (Órdenes abiertas)
    - [ ] Se refleje en métricas del dashboard
    - [ ] Se loggee en `system_init.log`

---

## 5. 📡 Confirmación Telegram

- [ ] Verificar que se envió mensaje de **“Bot iniciado”**.
- [ ] Confirmar que cualquier señal genera un mensaje de Telegram.
- [ ] Al detener el bot, validar que se envía **“Bot detenido manualmente”**.

---

## 6. 🛑 Finalización Controlada

- [ ] Ejecutar `stop_bot.ps1` (o `.sh`) y esperar mensaje de confirmación.
- [ ] Ejecutar `check_bot_status` para confirmar que el proceso ha finalizado.
- [ ] Revisar que Prometheus y Grafana también se hayan detenido (opcional).

---

## 📂 Archivos Clave Usados

- `executables/start_bot.ps1` — Iniciar el bot
- `executables/stop_bot.ps1` — Detener el bot
- `executables/check_bot_status.ps1` — Ver estado
- `backtrader_engine/configs/bybit_x_config.json` — Config live
- `backtrader_engine/configs/alert_config.json` — Config Telegram

---

✅ Checklist listo para ejecución técnica supervisada.
