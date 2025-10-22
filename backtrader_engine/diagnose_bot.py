#!/usr/bin/env python3
"""
Diagnostic script to identify bot issues
"""

import os
import sys
import json

print("\n" + "="*80)
print("BOT DIAGNOSTIC REPORT")
print("="*80 + "\n")

# 1. Check if running
print("[1] CHECKING PYTHON ENVIRONMENT")
print(f"    Python: {sys.version}")
print(f"    Executable: {sys.executable}")
print()

# 2. Check directories
print("[2] CHECKING DIRECTORIES")
dirs_to_check = [
    'configs',
    'logs',
    'monitoring',
    'strategies',
    'exchanges'
]

for d in dirs_to_check:
    exists = os.path.exists(d)
    status = "✅" if exists else "❌"
    print(f"    {status} {d}")
print()

# 3. Check configuration files
print("[3] CHECKING CONFIGURATION FILES")
configs = [
    'configs/bybit_x_config.json',
    'configs/alert_config.json',
    'configs/risk_config.json'
]

for cfg in configs:
    if os.path.exists(cfg):
        try:
            with open(cfg, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"    ✅ {cfg} - OK")
        except Exception as e:
            print(f"    ❌ {cfg} - ERROR: {e}")
    else:
        print(f"    ❌ {cfg} - NOT FOUND")
print()

# 4. Check Telegram configuration
print("[4] CHECKING TELEGRAM CONFIGURATION")
try:
    with open('configs/alert_config.json', 'r', encoding='utf-8') as f:
        alert_config = json.load(f)
    
    telegram = alert_config.get('telegram', {})
    print(f"    Telegram Enabled: {telegram.get('enabled')}")
    print(f"    Bot Token: {str(telegram.get('bot_token', 'NOT SET'))[:20]}...")
    print(f"    Chat ID: {telegram.get('chat_id')}")
    
    if not telegram.get('enabled'):
        print("    ⚠️  TELEGRAM IS DISABLED!")
    if not telegram.get('bot_token'):
        print("    ⚠️  TELEGRAM BOT TOKEN NOT SET!")
    if not telegram.get('chat_id'):
        print("    ⚠️  TELEGRAM CHAT ID NOT SET!")
        
except Exception as e:
    print(f"    ❌ ERROR: {e}")
print()

# 5. Check for null bytes in Python files
print("[5] CHECKING FOR NULL BYTES IN PYTHON FILES")
found_issues = False
for root, dirs, files in os.walk('.'):
    # Skip pycache and other dirs
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'backups', 'reports']]
    
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                    if b'\x00' in content:
                        print(f"    ❌ NULL BYTES FOUND: {path}")
                        found_issues = True
            except Exception as e:
                print(f"    ⚠️  Could not read {path}: {e}")

if not found_issues:
    print("    ✅ No null bytes found")
print()

# 6. Try to import main components
print("[6] ATTEMPTING COMPONENT IMPORTS")
components = [
    ('signal_engine', 'signal_engine'),
    ('risk_manager', 'risk_manager'),
    ('alert_manager', 'alert_manager'),
    ('telegram_notifier', 'telegram_notifier'),
]

for comp_name, module_name in components:
    try:
        __import__(module_name)
        print(f"    ✅ {comp_name}")
    except Exception as e:
        print(f"    ❌ {comp_name}: {type(e).__name__}")
print()

# 7. Check monitoring directory
print("[7] CHECKING MONITORING SYSTEM")
if os.path.exists('monitoring'):
    files = os.listdir('monitoring')
    print(f"    Files in monitoring/: {files}")
    
    for f in files:
        if f.endswith('.py'):
            path = os.path.join('monitoring', f)
            try:
                with open(path, 'rb') as file:
                    content = file.read()
                    if b'\x00' in content:
                        print(f"    ❌ {f} - HAS NULL BYTES!")
            except:
                pass
else:
    print("    ❌ monitoring directory not found")
print()

# 8. Check main.py
print("[8] CHECKING main.py")
try:
    with open('main.py', 'rb') as f:
        content = f.read()
        if b'\x00' in content:
            print("    ❌ main.py HAS NULL BYTES!")
        else:
            print("    ✅ main.py - No null bytes")
except Exception as e:
    print(f"    ❌ Error: {e}")
print()

# 9. Testnet status
print("[9] BYBIT CONFIGURATION")
try:
    with open('configs/bybit_x_config.json', 'r', encoding='utf-8') as f:
        bybit_config = json.load(f)
    
    exchange = bybit_config.get('exchange', {})
    print(f"    Testnet Enabled: {exchange.get('testnet')}")
    print(f"    API Key: {str(exchange.get('api_key', 'NOT SET'))[:15]}...")
    print(f"    Paper Trading Removed: {'paper_trading' not in bybit_config}")
except Exception as e:
    print(f"    ❌ Error: {e}")
print()

print("="*80)
print("RECOMMENDATIONS:")
print("="*80)
print("""
If Telegram alerts are not working:
1. Verify telegram.enabled = true in alert_config.json
2. Verify bot_token is set correctly
3. Verify chat_id is set correctly
4. Test with: python -c "from telegram_notifier import TelegramNotifier"

If bot won't start:
1. Check for null bytes in Python files
2. Try: python main.py
3. Check logs in backtrader_engine/logs/

Next steps:
- If null bytes found: Rebuild the file
- If Telegram down: Check configuration
- If main.py fails: Post full error output
""")
print("="*80 + "\n")
