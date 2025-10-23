#!/usr/bin/env python3
"""
Script de recuperación de estado del bot
Permite verificar y restaurar el estado del bot después de un crash
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backtrader_engine.state_manager import StateManager

def main():
    """Main recovery function"""
    print("=" * 60)
    print("🤖 BOT STATE RECOVERY TOOL")
    print("=" * 60)
    
    # Initialize state manager
    state_file = project_root / "backtrader_engine" / "logs" / "bot_state.json"
    backup_dir = project_root / "backtrader_engine" / "logs" / "state_backups"
    
    state_manager = StateManager(str(state_file), str(backup_dir))
    
    # Check if state file exists
    if not state_file.exists():
        print("❌ No state file found. Bot has never run or state was lost.")
        return False
    
    # Load current state
    state = state_manager.load_state()
    if not state:
        print("❌ Failed to load state file. File may be corrupted.")
        return False
    
    # Display state information
    print(f"📊 STATE SUMMARY:")
    print(f"   Balance: ${state.balance:.2f}")
    print(f"   Total PnL: ${state.total_pnl:.2f}")
    print(f"   Total Trades: {state.total_trades}")
    print(f"   Winning Trades: {state.winning_trades}")
    print(f"   Losing Trades: {state.losing_trades}")
    print(f"   Win Rate: {(state.winning_trades / state.total_trades * 100) if state.total_trades > 0 else 0:.1f}%")
    print(f"   Signals Generated: {state.signals_generated}")
    print(f"   Active Positions: {len(state.positions)}")
    print(f"   Pending Orders: {len(state.pending_orders)}")
    print(f"   WebSocket Connected: {state.websocket_connected}")
    print(f"   Last Update: {state.last_update}")
    
    if state.start_time:
        print(f"   Start Time: {state.start_time}")
    
    # Check for recent activity
    if state.last_update:
        last_update = datetime.fromisoformat(state.last_update.replace('Z', '+00:00'))
        time_diff = datetime.now(timezone.utc) - last_update
        print(f"   Time Since Last Update: {time_diff}")
        
        if time_diff.total_seconds() > 3600:  # 1 hour
            print("⚠️  WARNING: State is older than 1 hour. Bot may have crashed.")
    
    # Show positions
    if state.positions:
        print(f"\n📈 ACTIVE POSITIONS:")
        for symbol, pos in state.positions.items():
            print(f"   {symbol}: {pos['side']} {pos['size']} @ ${pos['entry_price']:.2f} (PnL: ${pos['unrealized_pnl']:.2f})")
    
    # Show pending orders
    if state.pending_orders:
        print(f"\n📋 PENDING ORDERS:")
        for order_id, order in state.pending_orders.items():
            print(f"   {order_id}: {order.get('side', 'N/A')} {order.get('qty', 0)} @ ${order.get('price', 0):.2f}")
    
    # Recovery options
    print(f"\n🔧 RECOVERY OPTIONS:")
    print("1. Start bot normally (will resume from current state)")
    print("2. Reset state to initial values")
    print("3. Show backup files")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        print("✅ Bot can be started normally. State will be restored automatically.")
        return True
    elif choice == "2":
        confirm = input("⚠️  This will reset ALL trading history. Continue? (yes/no): ").strip().lower()
        if confirm == "yes":
            # Reset state
            state_manager.current_state = state_manager.current_state.__class__()
            state_manager.save_state(force=True)
            print("✅ State reset to initial values.")
            return True
        else:
            print("❌ Reset cancelled.")
            return False
    elif choice == "3":
        show_backups(backup_dir)
        return True
    elif choice == "4":
        print("👋 Exiting.")
        return True
    else:
        print("❌ Invalid option.")
        return False

def show_backups(backup_dir):
    """Show available backup files"""
    print(f"\n📁 BACKUP FILES:")
    backup_files = sorted(backup_dir.glob("bot_state_backup_*.json"))
    
    if not backup_files:
        print("   No backup files found.")
        return
    
    for i, backup_file in enumerate(backup_files[-10:], 1):  # Show last 10
        stat = backup_file.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        size = stat.st_size
        print(f"   {i}. {backup_file.name} ({size} bytes, {mod_time.strftime('%Y-%m-%d %H:%M:%S')})")
    
    print(f"\n   Total backups: {len(backup_files)}")

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
