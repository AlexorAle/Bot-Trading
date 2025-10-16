#!/usr/bin/env python3
"""
Dependency Checker for Optimizer
Verifies all required dependencies are installed
"""

import sys
import subprocess

def check_dependency(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = __import__(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {package_name}: {version}")
        return True
    except ImportError:
        print(f"❌ {package_name}: NOT INSTALLED")
        return False

def install_dependency(package_name):
    """Install a package using pip"""
    print(f"📦 Installing {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installed successfully")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package_name}")
        return False

def main():
    """Check and install dependencies"""
    print("🔍 Checking Optimizer Dependencies...")
    print("=" * 50)
    
    required_packages = [
        ("optuna", "optuna"),
        ("backtrader", "backtrader"),
        ("pandas", "pandas"),
        ("numpy", "numpy")
    ]
    
    missing_packages = []
    
    for package_name, import_name in required_packages:
        if not check_dependency(package_name, import_name):
            missing_packages.append(package_name)
    
    print("=" * 50)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("\n📦 Installing missing packages...")
        
        for package in missing_packages:
            if not install_dependency(package):
                print(f"❌ Failed to install {package}")
                return False
        
        print("\n✅ All dependencies installed successfully!")
    else:
        print("✅ All dependencies are already installed!")
    
    print("\n🧪 Testing imports...")
    try:
        import optuna
        import backtrader as bt
        import pandas as pd
        import numpy as np
        print("✅ All imports successful!")
        return True
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
