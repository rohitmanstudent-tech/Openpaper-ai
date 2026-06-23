import typer
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Confirm
from rich.live import Live

from openpaper_cli.utils.console import console
from openpaper_cli.core import ConfigManager
from openpaper_cli.core.docker import DockerManager


def run_cmd(
    instance: str = typer.Option("default", "--instance", "-i", help="Instance name"),
    services: list[str] = typer.Option(None, "--service", "-s", help="Specific services to start"),
    detach: bool = typer.Option(True, "--detach/--attach", help="Run in background"),
    build: bool = typer.Option(False, "--build", "-b", help="Rebuild images"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs after start"),
):
    """Start OpenPaper AI services using Docker Compose."""
    config = ConfigManager(instance)
    docker = DockerManager(instance)

    if not docker.has_compose_file():
        console.print("[red]✗ docker-compose.yml not found[/red]")
        console.print("[dim]Run this command from your OpenPaper AI project directory[/dim]")
        raise typer.Exit(1)

    if docker.is_running():
        console.print("[yellow]! Services are already running[/yellow]")
        if not Confirm.ask("Restart services?", default=False):
            if follow:
                _follow_logs(docker, services)
            return

    console.print(f"[bold cyan]Starting OpenPaper AI[/bold cyan] [dim](instance: {instance})[/dim]")
    services_to_start = services or None

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task("Building and starting containers...", total=None)
        ok, msg = docker.up(services=services_to_start, detach=detach)

    if ok:
        console.print("[green]✓ Services started successfully[/green]")
        _show_service_status(docker)
    else:
        console.print(f"[red]✗ {msg}[/red]")
        raise typer.Exit(1)

    if follow:
        _follow_logs(docker, services)


def _show_service_status(docker: DockerManager) -> None:
    statuses = docker.get_status()
    if statuses:
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Service", style="bold cyan")
        table.add_column("Status", style="bold")
        table.add_column("Ports", style="dim")

        for svc in statuses:
            status_style = "[green]running" if svc["status"] == "running" else "[red]stopped"
            table.add_row(
                svc["name"],
                status_style,
                svc.get("ports", "") or "-",
            )

        console.print(table)

        console.print("\n[bold]Access points:[/bold]")
        console.print(f"  Frontend:  [cyan]http://localhost:{config.get('frontend_port', 3000)}[/cyan]")
        console.print(f"  API:       [cyan]http://localhost:{config.get('api_port', 8000)}[/cyan]")
        console.print(f"  API Docs:  [cyan]http://localhost:{config.get('api_port', 8000)}/docs[/cyan]")


def _follow_logs(docker: DockerManager, services: list[str] | None) -> None:
    import time
    service = services[0] if services else None
    try:
        docker.logs(service=service, follow=True)
    except KeyboardInterrupt:
        pass
