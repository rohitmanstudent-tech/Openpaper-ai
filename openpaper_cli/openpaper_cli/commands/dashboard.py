import typer
import webbrowser
import time
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from openpaper_cli.utils.console import console
from openpaper_cli.utils.styles import BANNER, BANNER_COLORS
from openpaper_cli.core import ConfigManager
from openpaper_cli.core.docker import DockerManager


def dashboard_cmd(
    instance: str = typer.Option("default", "--instance", "-i", help="Instance name"),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open browser automatically"),
    port: int = typer.Option(None, "--port", help="Local port to access dashboard"),
):
    """Open the OpenPaper AI web dashboard."""
    config = ConfigManager(instance)
    docker = DockerManager(instance)

    dashboard_port = port or config.get("frontend_port", 3000)
    dashboard_url = f"http://localhost:{dashboard_port}"

    for i, line in enumerate(BANNER.strip().split("\n")[:4]):
        console.print(f"[{BANNER_COLORS[i % len(BANNER_COLORS)]}]{line}[/]")
    console.print()

    console.print(Panel.fit(
        "[bold cyan]OpenPaper AI Dashboard[/bold cyan]\n\n"
        f"Instance: [bold]{instance}[/bold]\n"
        f"URL:      [underline cyan]{dashboard_url}[/underline cyan]\n"
        f"API:      [underline cyan]http://localhost:{config.get('api_port', 8000)}[/underline cyan]\n"
        f"Docs:     [underline cyan]http://localhost:{config.get('api_port', 8000)}/docs[/underline cyan]",
        border_style="cyan",
        box=box.ROUNDED,
    ))

    if not docker.is_running():
        console.print("[yellow]! Services are not running[/yellow]")
        from rich.prompt import Confirm
        if Confirm.ask("Start services now?", default=True):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task("Starting services...", total=None)
                ok, msg = docker.up()
            if ok:
                console.print("[green]✓ Services started[/green]")
            else:
                console.print(f"[red]✗ {msg}[/red]")
                raise typer.Exit(1)
        else:
            console.print("[dim]Run 'openpaper run' to start services manually[/dim]")

    console.print(f"\n[bold]Opening {dashboard_url} ...[/bold]")
    if open_browser:
        try:
            webbrowser.open(dashboard_url)
            console.print("[green]✓ Browser opened[/green]")
        except Exception as e:
            console.print(f"[yellow]! Could not open browser: {e}[/yellow]")
            console.print(f"   Open manually: {dashboard_url}")
