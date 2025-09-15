#!/usr/bin/env python3
"""
VS Code Test Discovery Debug Script
This script helps debug why VS Code isn't discovering tests.
"""

import sys
import os
import subprocess
from pathlib import Path

def main():
    """Debug VS Code test discovery issues."""
    print("VS Code Test Discovery Debug")
    print("=" * 40)
    
    # Check current directory
    print(f"Current directory: {os.getcwd()}")
    
    # Check Python interpreter
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    
    # Check if we're in virtual environment
    print(f"Virtual env: {sys.prefix}")
    
    # Check if pytest is installed
    try:
        import pytest
        print(f"pytest version: {pytest.__version__}")
    except ImportError:
        print("ERROR: pytest not installed!")
        return
    
    # Check if tests directory exists
    tests_dir = Path("tests")
    if tests_dir.exists():
        print(f"Tests directory exists: {tests_dir.absolute()}")
        test_files = list(tests_dir.glob("test_*.py"))
        print(f"Found {len(test_files)} test files")
        for f in test_files[:5]:  # Show first 5
            print(f"  - {f}")
    else:
        print("ERROR: tests directory not found!")
        return
    
    # Try pytest discovery
    print("\nTesting pytest discovery...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "--collect-only", "tests/test_adapter_interfaces.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            collected_line = [l for l in lines if 'collected' in l and 'items' in l]
            if collected_line:
                print(f"✓ {collected_line[0]}")
            else:
                print("✓ Tests discovered successfully")
        else:
            print(f"✗ pytest failed: {result.stderr}")
    except Exception as e:
        print(f"✗ Error running pytest: {e}")
    
    print("\nVS Code Recommendations:")
    print("1. Ensure Python interpreter is set to ./.venv/bin/python")
    print("2. Open Command Palette (Ctrl+Shift+P) -> 'Test: Refresh Tests'")
    print("3. Check Testing panel (Test tube icon in sidebar)")
    print("4. If still not working, restart VS Code")

if __name__ == "__main__":
    main()