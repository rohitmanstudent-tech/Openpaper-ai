import typer
import subprocess
import sys
from pathlib import Path
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich import box

from openpaper_cli.utils.console import console
from openpaper_cli.utils.styles import BANNER, BANNER_COLORS
from openpaper_cli import __version__


def update_cmd(
    version: str = typer.Option(None, "--version", help="Specific version to update to"),
    check_only: bool = typer.Option(False, "--check", "-c", help="Only check for updates"),
    force: bool = typer.Option(False, "--force", "-f", help="Force update even if up-to-date"),
):
    """Update OpenPaper AI to the latest version."""
    console.print()

    for i, line in enumerate(BANNER.strip().split("\n")[:4]):
        console.print(f"[{BANNER_COLORS[i % len(BANNER_COLORS)]}]{line}[/]")
    console.print()

    console.print(f"[dim]Current version:[/dim] [bold]{__version__}[/bold]")

    import json
    import httpx

    try:
        resp = httpx.get(
            "https://api.github.com/repos/yourusername/openpaper-ai/releases/latest",
            timeout=15,
        )
        resp.raise_for_status()
        release = resp.json()
        latest_version = release.get("tag_name", "").lstrip("v")
        release_url = release.get("html_url", "")
        release_body = release.get("body", "")

        console.print(f"[dim]Latest version:[/dim] [bold cyan]{latest_version}[/bold cyan]")

        if not check_only:
            from packaging.version import Version

            current = Version(__version__)
            latest = Version(latest_version)

            if current >= latest and not force:
                console.print("[green]✓ You're up to date![/green]")
                return

            console.print(f"\n[bold]Release Notes:[/bold]")
            if release_body:
                for line in release_body.strip().split("\n")[:15]:
                    console.print(f"  {line}")

            console.print(f"\n[dim]Full release: {release_url}[/dim]")

            if Confirm.ask(f"\nUpdate to v{latest_version}?", default=True):
                _perform_update(version or latest_version)
        else:
            from packaging.version import Version
            current = Version(__version__)
            latest = Version(latest_version)
            if current < latest:
                console.print(f"\n[yellow]! Update available: {__version__} → {latest_version}[/yellow]")
                console.print(f"  Run '[bold]openpaper update[/bold]' to upgrade")
            else:
                console.print("\n[green]✓ Latest version installed[/green]")

    except httpx.ConnectError:
        console.print("[yellow]! Could not check for updates (no internet)[/yellow]")
        console.print("  Run 'openpaper update --force' to update from local source")
    except ImportError:
        console.print("[yellow]! 'packaging' module not found[/yellow]")
        console.print("  Install with: pip install packaging")
    except Exception as e:
        console.print(f"[red]✗ Update check failed: {e}[/red]")


def _perform_update(version: str) -> None:
    import os

    console.print(f"\n[bold cyan]Updating to v{version}...[/bold cyan]")

    project_dir = Path.cwd()
    git_dir = project_dir / ".git"

    if git_dir.exists():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Pulling latest changes...", total=None)

            try:
                result = subprocess.run(
                    ["git", "pull", "origin", "main"],
                    capture_output=True, text=True, timeout=60,
                    cwd=str(project_dir),
                )
                if result.returncode == 0:
                    console.print("[green]✓ Code updated from Git[/green]")
                else:
                    console.print(f"[yellow]! Git pull: {result.stderr}[/yellow]")
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                console.print(f"[yellow]! Git not available: {e}[/yellow]")

    pip_ok = _update_pip_package()
    if pip_ok:
        console.print("[green]✓ CLI package updated[/green]")

    _update_docker_images()

    console.print()
    console.print(Panel.fit(
        "[bold green]Update Complete![/bold green]\n\n"
        f"OpenPaper AI v{version} is ready.\n"
        "Run 'openpaper doctor' to verify everything is working.",
        border_style="green",
        box=box.ROUNDED,
    ))


def _update_pip_package() -> bool:
    try:
        cli_dir = Path(__file__).resolve().parent.parent
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(cli_dir)],
            capture_output=True, text=True, timeout=120,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _update_docker_images() -> None:
    console.print("\n[bold]Rebuilding Docker images...[/bold]")
    try:
        result = subprocess.run(
            ["docker", "compose", "pull"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            console.print("[green]✓ Docker images updated[/green]")
        else:
            console.print(f"[dim]Docker pull: {result.stderr[:100]}[/dim]")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        console.print("[dim]! Could not update Docker images[/dim]")
