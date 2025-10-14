#!/usr/bin/env python3
"""
Script para descargar datos históricos de criptomonedas desde Binance usando ccxt.
Compatible con Backtrader y el portfolio_engine.py existente.

Autor: Cursor IDE + ChatGPT
Fecha: 2025-01-14
"""

import ccxt
import pandas as pd
import os
import time
from datetime import datetime, timedelta
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_crypto_data(symbol, timeframe='15m', since='2020-01-01', data_dir='backtrader_engine/data/'):
    """
    Descarga datos históricos de Binance con ccxt, los formatea para Backtrader y guarda en CSV.
    
    Args:
        symbol (str): Par de trading, ej. 'ETH/USDT' o 'SOL/USDT'
        timeframe (str): Timeframe, ej. '1m', '15m', '1h', '1d'
        since (str): Fecha de inicio en formato YYYY-MM-DD
        data_dir (str): Directorio para guardar CSVs
    
    Returns:
        str: Ruta del archivo CSV generado
    """
    logger.info(f"🚀 Iniciando descarga de {symbol} - {timeframe} desde {since}")
    
    try:
        # Inicializar exchange (no necesita API keys para datos públicos)
        exchange = ccxt.binance()
        logger.info(f"✅ Exchange Binance inicializado correctamente")
        
        # Convertir fecha a timestamp en milisegundos
        since_ms = exchange.parse8601(since + 'T00:00:00Z')
        logger.info(f"📅 Timestamp de inicio: {since_ms} ({since})")
        
        # Crear directorio si no existe
        os.makedirs(data_dir, exist_ok=True)
        
        # Nombre del archivo
        filename = f"{data_dir}{symbol.replace('/', '')}_{timeframe}.csv"
        logger.info(f"📁 Archivo destino: {filename}")
        
        # Descargar datos con paginación
        all_ohlcv = []
        chunk_count = 0
        total_bars = 0
        
        logger.info(f"📊 Iniciando descarga paginada...")
        
        while True:
            try:
                # Fetch con límite de 1000 barras por llamada
                ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=1000)
                
                if not ohlcv:
                    logger.info(f"✅ No hay más datos disponibles")
                    break
                
                all_ohlcv.extend(ohlcv)
                chunk_count += 1
                total_bars = len(all_ohlcv)
                
                # Actualizar timestamp para siguiente chunk
                since_ms = ohlcv[-1][0] + 1
                
                logger.info(f"📦 Chunk {chunk_count}: {len(ohlcv)} barras (Total: {total_bars})")
                
                # Verificar si llegamos al presente
                if since_ms >= exchange.milliseconds():
                    logger.info(f"✅ Llegamos al presente, finalizando descarga")
                    break
                
                # Rate limiting: pausa pequeña entre llamadas
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Error en chunk {chunk_count}: {e}")
                time.sleep(1)  # Pausa más larga en caso de error
                continue
        
        if not all_ohlcv:
            logger.error(f"❌ No se obtuvieron datos para {symbol}")
            return None
        
        # Convertir a DataFrame en formato Backtrader
        logger.info(f"🔄 Convirtiendo {total_bars} barras a DataFrame...")
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convertir timestamp a datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Validar datos
        logger.info(f"🔍 Validando datos...")
        logger.info(f"   - Rango de fechas: {df['timestamp'].min()} a {df['timestamp'].max()}")
        logger.info(f"   - Precio inicial: ${df['close'].iloc[0]:.2f}")
        logger.info(f"   - Precio final: ${df['close'].iloc[-1]:.2f}")
        logger.info(f"   - Volumen promedio: {df['volume'].mean():.0f}")
        
        # Verificar datos faltantes o inválidos
        null_count = df.isnull().sum().sum()
        if null_count > 0:
            logger.warning(f"⚠️  Encontrados {null_count} valores nulos")
        
        # Verificar precios no positivos
        invalid_prices = (df[['open', 'high', 'low', 'close']] <= 0).any().any()
        if invalid_prices:
            logger.warning(f"⚠️  Encontrados precios no positivos")
        
        # Guardar CSV
        logger.info(f"💾 Guardando CSV en {filename}...")
        df.to_csv(filename, index=False)
        
        # Verificar archivo guardado
        file_size = os.path.getsize(filename)
        logger.info(f"✅ Archivo guardado: {file_size:,} bytes")
        
        logger.info(f"🎉 Descarga completada: {symbol} - {total_bars} barras en {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"❌ Error crítico descargando {symbol}: {e}")
        return None

def download_multiple_symbols(symbols, timeframe='15m', since='2020-01-01', data_dir='backtrader_engine/data/'):
    """
    Descarga múltiples símbolos secuencialmente.
    
    Args:
        symbols (list): Lista de pares de trading
        timeframe (str): Timeframe
        since (str): Fecha de inicio
        data_dir (str): Directorio destino
    
    Returns:
        dict: Diccionario con resultados de cada descarga
    """
    logger.info(f"🚀 Iniciando descarga múltiple: {symbols}")
    
    results = {}
    start_time = datetime.now()
    
    for i, symbol in enumerate(symbols, 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 Descargando {symbol} ({i}/{len(symbols)})")
        logger.info(f"{'='*60}")
        
        result = download_crypto_data(symbol, timeframe, since, data_dir)
        results[symbol] = result
        
        if result:
            logger.info(f"✅ {symbol}: ÉXITO")
        else:
            logger.error(f"❌ {symbol}: FALLO")
        
        # Pausa entre descargas para evitar rate limiting
        if i < len(symbols):
            logger.info(f"⏳ Pausa de 2 segundos antes de siguiente descarga...")
            time.sleep(2)
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🏁 RESUMEN DE DESCARGA MÚLTIPLE")
    logger.info(f"{'='*60}")
    logger.info(f"⏱️  Duración total: {duration}")
    logger.info(f"📊 Símbolos procesados: {len(symbols)}")
    
    successful = sum(1 for result in results.values() if result)
    failed = len(symbols) - successful
    
    logger.info(f"✅ Exitosos: {successful}")
    logger.info(f"❌ Fallidos: {failed}")
    
    for symbol, result in results.items():
        status = "✅" if result else "❌"
        logger.info(f"   {status} {symbol}: {result or 'FALLO'}")
    
    return results

def main():
    """Función principal para descarga de ETH y SOL (6 meses)"""
    logger.info(f"🚀 INICIANDO DESCARGA DE DATOS HISTÓRICOS")
    logger.info(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Calcular fecha de inicio (6 meses atrás)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # ~6 meses
    since_str = start_date.strftime('%Y-%m-%d')
    
    logger.info(f"📅 Período: {since_str} a {end_date.strftime('%Y-%m-%d')} (~6 meses)")
    
    # Símbolos a descargar
    symbols = ['ETH/USDT', 'SOL/USDT']
    timeframe = '15m'
    data_dir = 'data/'
    
    # Ejecutar descarga múltiple
    results = download_multiple_symbols(symbols, timeframe, since_str, data_dir)
    
    # Verificar archivos generados
    logger.info(f"\n{'='*60}")
    logger.info(f"🔍 VERIFICACIÓN DE ARCHIVOS GENERADOS")
    logger.info(f"{'='*60}")
    
    for symbol in symbols:
        filename = f"{data_dir}{symbol.replace('/', '')}_{timeframe}.csv"
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            logger.info(f"✅ {filename}: {file_size:,} bytes")
            
            # Leer primeras líneas para verificar formato
            try:
                df = pd.read_csv(filename, nrows=5)
                logger.info(f"   📊 Columnas: {list(df.columns)}")
                logger.info(f"   📅 Primera fecha: {df['timestamp'].iloc[0]}")
                logger.info(f"   💰 Primer precio: ${df['close'].iloc[0]:.2f}")
            except Exception as e:
                logger.error(f"   ❌ Error leyendo archivo: {e}")
        else:
            logger.error(f"❌ {filename}: NO ENCONTRADO")
    
    logger.info(f"\n🎉 DESCARGA COMPLETADA")
    logger.info(f"📁 Archivos guardados en: {data_dir}")
    logger.info(f"📋 Log completo en: data_download.log")

if __name__ == "__main__":
    main()
