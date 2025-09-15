"""
Dummy vscode_pytest plugin to make VS Code pytest execution work.
This is a minimal implementation to prevent import errors.
"""

def pytest_configure(config):
    """Configure pytest for VS Code integration."""
    pass

def pytest_collection_modifyitems(config, items):
    """Modify test items for VS Code."""
    pass