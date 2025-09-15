#!/bin/bash
# Setup script for MedChain development environment

echo "Setting up MedChain development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install pytest plugins for VS Code compatibility
echo "Installing pytest plugins..."
pip install pytest-vscode pytest-json-report

echo "Development environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "source .venv/bin/activate"
echo ""
echo "To run tests with VS Code compatibility:"
echo ".venv/bin/python -m pytest -p vscode_pytest --rootdir=$(pwd) [test_files] -v"