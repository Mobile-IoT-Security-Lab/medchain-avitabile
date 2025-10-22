"""Utility exceptions mimicking the real pygments API subset used by pytest."""

class ClassNotFound(Exception):
    """Raised when a requested style cannot be located."""


class OptionError(Exception):
    """Raised when an invalid option value is supplied."""

