#!/usr/bin/env python3
"""
VS Code compatible test runner for MedChain project.
This script ensures proper execution of pytest with VS Code extensions.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run tests with VS Code compatibility."""
    # Ensure we're in the project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    # Use virtual environment python if available
    venv_python = project_root / '.venv' / 'bin' / 'python'
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable
    
    # Build pytest command
    cmd = [
        python_cmd, '-m', 'pytest',
        '-p', 'vscode_pytest',
        f'--rootdir={project_root}',
    ]
    
    # Add any additional arguments passed to this script
    cmd.extend(sys.argv[1:])
    
    # Add default verbose flag if not specified
    if '-v' not in cmd and '--verbose' not in cmd:
        cmd.append('-v')
    
    print(f"Running: {' '.join(cmd)}")
    
    # Execute pytest
    try:
        result = subprocess.run(cmd, env=env, cwd=project_root)
        sys.exit(result.returncode)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure pytest is installed: pip install pytest pytest-vscode")
        sys.exit(1)

if __name__ == '__main__':
    main()