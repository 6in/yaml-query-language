"""YQL (YAML Query Language) Parser and SQL Generator."""

__version__ = "0.1.0"

from .generator import Dialect, generate_sql
from .parser import parse, parse_file
from .security import SecurityConfig, SecurityError

__all__ = [
    "parse",
    "parse_file",
    "generate_sql",
    "Dialect",
    "SecurityConfig",
    "SecurityError",
    "__version__",
]

