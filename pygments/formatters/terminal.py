"""Minimal stand-in for pygments.formatters.terminal.TerminalFormatter."""

from __future__ import annotations

from ..util import OptionError


class TerminalFormatter:
    """Formatter stub that accepts the basic arguments pytest passes."""

    def __init__(self, *, bg: str = "dark", style: str | None = None) -> None:
        if bg not in {"dark", "light"}:
            raise OptionError(f"Unsupported background option: {bg}")
        self.bg = bg
        self.style = style

    def format(self, tokens, outfile) -> None:
        """No-op formatter provided for API parity."""
        for _, text in tokens:
            outfile.write(text)

