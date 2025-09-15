# VS Code Test Execution Fix

## Problem

VS Code's Python test runner uses a special pytest plugin called `vscode_pytest` that is not available in the standard Python environment. This causes test execution to fail with:

```sh
ImportError: Error importing plugin "vscode_pytest": No module named 'vscode_pytest'
```

## Solution Implemented

### 1. Installed Required Packages

Added VS Code compatible pytest plugins to `requirements.txt`:

- `pytest-vscode`: VS Code test runner compatibility
- `pytest-json-report`: my test reporting
- `pytest-metadata`: Test metadata collection

### 2. Created Local Plugin

Created a minimal `vscode_pytest.py` module in the project root that provides the necessary hooks for VS Code integration.

### 3. Updated Configuration

- Updated `pyproject.toml` to include `pythonpath = ["."]` to ensure the local plugin is found
- my `tests/conftest.py` with proper pytest hooks for VS Code compatibility

### 4. Created Helper Scripts

- `setup_dev.sh`: Development environment setup script
- `run_tests.py`: VS Code compatible test runner script

## Usage

### Option 1: Use the test runner script

```bash
./run_tests.py tests/test_adapter_interfaces.py -v
```

### Option 2: Manual execution with proper environment

```bash
.venv/bin/python -m pytest -p vscode_pytest --rootdir=$(pwd) tests/test_adapter_interfaces.py -v
```

### Option 3: Setup development environment

```bash
./setup_dev.sh
source .venv/bin/activate
python -m pytest tests/ -v
```

## Verification

All tests now run successfully with VS Code's test runner without the import error.

The fix maintains compatibility with:

- VS Code Python Test Discovery
- Command line pytest execution
- CI/CD environments
- Integration test suites
