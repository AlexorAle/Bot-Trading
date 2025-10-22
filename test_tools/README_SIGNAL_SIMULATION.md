# SIMULADOR DE SEÑALES - GUIA RAPIDA

## COMANDOS LISTOS PARA USAR

### 1. Simulacion EMA Breakout (Compra)
`python
python -c \"\"\"
import json, requests, time
config = json.load(open('backtrader_engine/configs/alert_config.json'))
r = requests.get('https://api.bybit.com/v5/market/tickers', params={'category':'spot','symbol':'ETHUSDT'})
price = float(r.json()['result']['list'][0]['lastPrice'])
bot_token = config['telegram']['bot_token']
chat_id = config['telegram']['chat_id']
msg = f'''TEST EMA BREAKOUT BUY

Symbol: ETHUSDT
Precio: 
Tipo: BUY
Confianza: 82%

Indicadores:
  RSI: 62.0 (alcista)
  EMA20: {price-2:.2f}
  EMA50: {price-15:.2f}
  ATR: 12.5

PRUEBA - Sistema validado'''
r = requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={'chat_id':chat_id,'text':msg})
print(f'Senal simulada: ETHUSDT BUY @ ')
print(f'Telegram: {'ENVIADO' if r.status_code==200 else 'ERROR'}')
\"\"\"
`

### 2. Simulacion Bollinger Reversion (Compra desde sobreventa)
`python
python -c \"\"\"
import json, requests, time
config = json.load(open('backtrader_engine/configs/alert_config.json'))
r = requests.get('https://api.bybit.com/v5/market/tickers', params={'category':'spot','symbol':'ETHUSDT'})
price = float(r.json()['result']['list'][0]['lastPrice'])
bot_token = config['telegram']['bot_token']
chat_id = config['telegram']['chat_id']
msg = f'''TEST BOLLINGER REVERSION BUY

Symbol: ETHUSDT
Precio: 
Tipo: BUY
Confianza: 78%

Indicadores:
  RSI: 35.0 (sobreventa)
  BB Upper: {price+20:.2f}
  BB Middle: {price:.2f}
  BB Lower: {price-30:.2f}
  ATR: 15.0

Reversion desde banda inferior
PRUEBA - Sistema validado'''
r = requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={'chat_id':chat_id,'text':msg})
print(f'Senal simulada: ETHUSDT BUY (Reversion) @ ')
print(f'Telegram: {'ENVIADO' if r.status_code==200 else 'ERROR'}')
\"\"\"
`

### 3. Simulacion RSI Momentum (Compra fuerte)
`python
python -c \"\"\"
import json, requests, time
config = json.load(open('backtrader_engine/configs/alert_config.json'))
r = requests.get('https://api.bybit.com/v5/market/tickers', params={'category':'spot','symbol':'ETHUSDT'})
price = float(r.json()['result']['list'][0]['lastPrice'])
bot_token = config['telegram']['bot_token']
chat_id = config['telegram']['chat_id']
msg = f'''TEST RSI MOMENTUM BUY

Symbol: ETHUSDT
Precio: 
Tipo: BUY
Confianza: 85%

Indicadores:
  RSI: 58.0 (momentum)
  EMA20: {price+2:.2f}
  EMA50: {price-10:.2f}
  ATR: 14.0

Momentum alcista confirmado
PRUEBA - Sistema validado'''
r = requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={'chat_id':chat_id,'text':msg})
print(f'Senal simulada: ETHUSDT BUY (Momentum) @ ')
print(f'Telegram: {'ENVIADO' if r.status_code==200 else 'ERROR'}')
\"\"\"
`

### 4. Simulacion Volatility Breakout (Alta volatilidad)
`python
python -c \"\"\"
import json, requests, time
config = json.load(open('backtrader_engine/configs/alert_config.json'))
r = requests.get('https://api.bybit.com/v5/market/tickers', params={'category':'spot','symbol':'ETHUSDT'})
price = float(r.json()['result']['list'][0]['lastPrice'])
bot_token = config['telegram']['bot_token']
chat_id = config['telegram']['chat_id']
msg = f'''TEST VOLATILITY BREAKOUT

Symbol: ETHUSDT
Precio: 
Tipo: BUY
Confianza: 80%

Indicadores:
  RSI: 65.0
  ATR: 22.0 (alta vol)
  Highest: {price:.2f}
  Volume Ratio: 1.8x

Breakout con volumen
PRUEBA - Sistema validado'''
r = requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={'chat_id':chat_id,'text':msg})
print(f'Senal simulada: ETHUSDT BUY (Breakout) @ ')
print(f'Telegram: {'ENVIADO' if r.status_code==200 else 'ERROR'}')
\"\"\"
`

### 5. Simulacion Bearish Reversal (Venta)
`python
python -c \"\"\"
import json, requests, time
config = json.load(open('backtrader_engine/configs/alert_config.json'))
r = requests.get('https://api.bybit.com/v5/market/tickers', params={'category':'spot','symbol':'ETHUSDT'})
price = float(r.json()['result']['list'][0]['lastPrice'])
bot_token = config['telegram']['bot_token']
chat_id = config['telegram']['chat_id']
msg = f'''TEST BEARISH REVERSAL SELL

Symbol: ETHUSDT
Precio: 
Tipo: SELL
Confianza: 75%

Indicadores:
  RSI: 72.0 (sobrecompra)
  BB Upper: {price+30:.2f}
  BB Middle: {price:.2f}
  BB Lower: {price-30:.2f}
  ATR: 16.0

Reversion bajista desde banda superior
PRUEBA - Sistema validado'''
r = requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', json={'chat_id':chat_id,'text':msg})
print(f'Senal simulada: ETHUSDT SELL (Reversion) @ ')
print(f'Telegram: {'ENVIADO' if r.status_code==200 else 'ERROR'}')
\"\"\"
`

## NOTAS IMPORTANTES

- Estos comandos **SOLO envian mensajes a Telegram**
- NO ejecutan trades reales en el bot
- Son para validar el sistema de alertas
- Muestran como se verian las senales con indicadores correctos

## PARA INYECTAR REALMENTE AL BOT

Se necesitaria modificar el codigo del bot para:
1. Escuchar un archivo de senales
2. O exponer un endpoint REST
3. O tener una estrategia de test toggleable

