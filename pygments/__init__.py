"""
Minimal pygments stub used for running the test suite in environments
without network access to install the actual dependency. Only the small
surface area required by pytest is implemented; enough to avoid import
errors and keep output readable without syntax highlighting.
"""

from __future__ import annotations

from . import util  # re-exported for ``pygments.util`` access


def highlight(source: str | bytes, lexer=None, formatter=None) -> str:
    """Return the source unchanged; placeholder for real highlighting."""
    if isinstance(source, bytes):
        return source.decode("utf-8", errors="ignore")
    return source


__all__ = ["highlight", "util"]
