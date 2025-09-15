# VS Code Test Discovery Troubleshooting Guide

## Quick Fix Checklist

If tests aren't showing up in VS Code's Testing panel, follow these steps:

### 1. Check Python Interpreter

1. Open Command Palette (`Ctrl+Shift+P`)
2. Type "Python: Select Interpreter"
3. Choose `./.venv/bin/python` (should show the virtual environment)

### 2. Refresh Test Discovery

1. Open Command Palette (`Ctrl+Shift+P`)
2. Type "Test: Refresh Tests"
3. OR click the refresh icon in the Testing panel

### 3. Check Testing Panel

1. Open Testing panel (`Ctrl+Shift+E` then click Test tube icon)
2. You should see a folder structure with test files
3. If you see "No tests found", proceed to step 4

### 4. Check VS Code Settings

Ensure `.vscode/settings.json` contains:

```json
{
   "python.defaultInterpreterPath": "./.venv/bin/python",
   "python.testing.pytestEnabled": true,
   "python.testing.unittestEnabled": false,
   "python.testing.pytestArgs": [
      "--rootdir=${workspaceFolder}",
      "-p",
      "vscode_pytest",
      "tests"
   ],
   "python.testing.cwd": "${workspaceFolder}",
   "python.testing.autoTestDiscoverOnSaveEnabled": true
}
```

### 5. Manual Test Discovery Verification

Run this command in the terminal:

```bash
.venv/bin/python -m pytest --collect-only -p vscode_pytest tests/
```

### 6. VS Code Extension Check

1. Ensure Python extension is installed and enabled
2. Check for Python extension updates
3. Restart VS Code if needed

### 7. Clear VS Code Cache

1. Close VS Code
2. Delete `.vscode/.ropeproject` if it exists
3. Delete `__pycache__` directories: `find . -name "__pycache__" -type d -exec rm -rf {} +`
4. Restart VS Code

### 8. Alternative Test Running Methods

If VS Code test discovery still doesn't work, use these alternatives:

#### Option A: Use the test runner script

```bash
./run_tests.py tests/test_adapter_interfaces.py -v
```

#### Option B: Use pytest directly

```bash
.venv/bin/python -m pytest tests/ -v
```

#### Option C: Use the comprehensive test script

```bash
./run_comprehensive_tests.sh
```

## Common Issues and Solutions

### Issue 1: "No module named 'vscode_pytest'"

**Solution**:

1. Check Python path is correct
2. Ensure all dependencies are installed: `pip install -r requirements.txt`
3. Check that test files are valid Python

### Issue 2: Wrong Python Interpreter

**Solution**:

1. Activate virtual environment: `source .venv/bin/activate`
2. In VS Code, select the correct interpreter (`./.venv/bin/python`)

### Issue 3: Virtual Environment Not Activated

1. Activate virtual environment: `source .venv/bin/activate`
2. In VS Code, select the correct interpreter (`./.venv/bin/python`)

### Issue 4: Import Errors in Tests

**Solution**: Ensure `PYTHONPATH` includes the project root:

```bash
export PYTHONPATH="${PWD}:${PYTHONPATH}"
```

## Verification Commands

Test everything is working:

````bash
# 1. Check Python version
.venv/bin/python --version

# 2. Check pytest is installed
.venv/bin/python -m pytest --version

# 3. Test discovery
.venv/bin/python -m pytest --collect-only tests/test_adapter_interfaces.py

# 4. Run a single test
Make sure you have these extensions installed:

- Python (ms-python.python)
- Python Debugger (ms-python.debugpy)

## Additional Notes
Make sure you have these extensions installed:
- Python (ms-python.python)
- Python Debugger (ms-python.debugpy)

## Additional Notes

- The project uses a custom `vscode_pytest.py` plugin for VS Code compatibility
- All test configuration is in `pyproject.toml`
- Tests are located in the `tests/` directory
- Test files follow the pattern `test_*.py`

If tests still don't appear after following this guide, try opening VS Code from the project directory:
```bash
cd /home/enriicola/Desktop/medchain-avitabile
code .
````
