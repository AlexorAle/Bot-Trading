#!/usr/bin/env python3
"""
Script to clean the strategy file by removing template code
"""

def clean_strategy_file():
    with open('user_data/strategies/LiquidationHunterFreq.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    skip = False
    
    for i, line in enumerate(lines):
        # Start skipping when we find the template minimal_roi definition
        if 'Minimal ROI designed for the strategy' in line:
            skip = True
            continue
        
        # Stop skipping when we find the template stoploss definition
        if skip and line.strip() == 'stoploss = -0.10':
            skip = False
            continue
        
        # Add line if we're not skipping
        if not skip:
            new_lines.append(line)
    
    # Write the cleaned file
    with open('user_data/strategies/LiquidationHunterFreq.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"File cleaned successfully. Removed {len(lines) - len(new_lines)} lines.")
    print(f"Original: {len(lines)} lines, New: {len(new_lines)} lines")

if __name__ == "__main__":
    clean_strategy_file()

