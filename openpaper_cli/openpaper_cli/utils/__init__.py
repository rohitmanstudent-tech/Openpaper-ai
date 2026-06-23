import io
import os
import sys
from rich.console import Console
from rich.theme import Theme

theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "highlight": "bold magenta",
    "dim": "dim white",
    "title": "bold cyan",
    "path": "underline blue",
})


def _get_console() -> Console:
    kwargs = {
        "theme": theme,
        "highlight": False,
        "legacy_windows": False,
    }
    try:
        if not sys.stdout.isatty():
            kwargs["force_terminal"] = True
    except (AttributeError, ValueError):
        kwargs["force_terminal"] = True
    try:
        test = "\u2713".encode(sys.stdout.encoding, errors="strict")
    except (UnicodeEncodeError, AttributeError):
        kwargs["file"] = io.TextIOWrapper(
            sys.stdout.buffer,
            encoding="utf-8",
            errors="replace",
            line_buffering=True,
        )
    return Console(**kwargs)


console = _get_console()

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
