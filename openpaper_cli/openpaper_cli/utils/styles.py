from rich.console import Console
from rich.theme import Theme
from rich.style import Style

BANNER = r"""
   ___                   ___               _    ___
  / _ \ _ __   ___ _ __ | _ \__ _ ___ _ __| |_ / _ \__ _ ___ ___
 | | | | '_ \ / _ \ '_ \|  _/ _` / _ \ '_ \ ' \ | | / _` / __/ __|
 | |_| | |_) |  __/ |_) | | | (_|  __/ | | | | | |_| \ (_| \__ \__ \
  \___/| .__/ \___| .__/|_|  \__,_\___|_| |_|_|  \___/\__,_|___/___/
       |_|        |_|
"""

BANNER_COLORS = ["cyan", "blue", "magenta", "green", "yellow", "cyan"]

STYLES = {
    "header": "bold cyan",
    "subheader": "bold blue",
    "success": "bold green",
    "error": "bold red",
    "warning": "yellow",
    "info": "cyan",
    "dim": "dim white",
    "highlight": "bold magenta",
    "path": "underline blue",
}
