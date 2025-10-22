"""Minimal base Lexer implementation compatible with pytest usage."""

from __future__ import annotations

from typing import Iterable, Tuple


Token = Tuple[str | None, str]


class Lexer:
    """Return the full input as a single token."""

    def get_tokens(self, text: str) -> Iterable[Token]:
        yield (None, text)

