#!/usr/bin/env python3
"""Find all files with null bytes"""
import os
from pathlib import Path

print("Searching for files with null bytes...\n")

found = False
for root, dirs, files in os.walk('.'):
    # Skip cache dirs
    dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
    
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                    if b'\x00' in content:
                        print(f"[NULLBYTES] {path}")
                        found = True
            except:
                pass

if not found:
    print("[OK] No null bytes found in any Python files")
else:
    print("\nThese files need to be recreated (deleted and recreated)")
