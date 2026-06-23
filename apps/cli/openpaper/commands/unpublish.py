"""openpaper unpublish — remove a package from the remote registry."""

import sys
import click
from rich.console import Console
from rich.prompt import Confirm

from openpaper.registry import unpublish_package, get_package
from openpaper.config import get_token

console = Console()


@click.command(name="unpublish")
@click.argument("package_id", required=True)
@click.option("--force", is_flag=True, help="Skip confirmation")
@click.option("--yes", is_flag=True, help="Automatically confirm")
def unpublish(package_id: str, force: bool, yes: bool):
    """Unpublish a package from the OpenPaper Hub registry.

    \b
    Examples:
        openpaper unpublish my-agent
        openpaper unpublish my-agent --force
    """
    if not get_token():
        console.print("[red]Not authenticated. Run 'openpaper login' first.[/red]")
        sys.exit(1)

    try:
        pkg = get_package(package_id)
        name = pkg.get("name", package_id)
        ver = pkg.get("current_version", "?")
        author = pkg.get("author", "?")
    except Exception:
        name = package_id
        ver = "?"
        author = "?"

    confirmed = yes or force
    if not confirmed:
        confirmed = Confirm.ask(
            f"Unpublish [bold cyan]{name}[/bold cyan] v{ver} by {author}?"
        )

    if not confirmed:
        console.print("[yellow]Cancelled.[/yellow]")
        return

    try:
        result = unpublish_package(package_id)
    except Exception as e:
        console.print(f"[red]Failed to unpublish: {e}[/red]")
        sys.exit(1)

    if result.get("success"):
        console.print(f"[green]✓ '{name}' unpublished[/green]")
    else:
        console.print(f"[red]Failed: {result.get('message', 'unknown error')}[/red]")
        sys.exit(1)
