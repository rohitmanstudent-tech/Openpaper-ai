import typer
import httpx
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.prompt import Confirm

from openpaper_cli.utils.console import console
from openpaper_cli.core import ConfigManager


def plugins_cmd(
    instance: str = typer.Option("default", "--instance", "-i", help="Instance name"),
    list_mode: bool = typer.Option(False, "--list", "-l", help="List all plugins"),
    enable: str = typer.Option(None, "--enable", help="Enable a plugin by name"),
    disable: str = typer.Option(None, "--disable", help="Disable a plugin by name"),
    reload: str = typer.Option(None, "--reload", help="Reload a plugin by name"),
):
    """Manage OpenPaper AI plugins."""
    config = ConfigManager(instance)
    base_url = f"http://{config.get('api_host')}:{config.get('api_port')}/api/v1"

    if enable:
        _toggle_plugin(base_url, enable, True)
        return

    if disable:
        _toggle_plugin(base_url, disable, False)
        return

    if reload:
        _reload_plugin(base_url, reload)
        return

    if list_mode or True:
        _list_plugins(base_url)


def _list_plugins(base_url: str) -> None:
    try:
        resp = httpx.get(f"{base_url}/plugins/", timeout=10)
        resp.raise_for_status()
        plugins = resp.json()

        if not plugins:
            console.print("[dim]No plugins registered[/dim]")
            return

        table = Table(box=box.SIMPLE, show_header=True, title="Registered Plugins")
        table.add_column("Name", style="cyan bold")
        table.add_column("Version", style="dim")
        table.add_column("Description", style="dim")
        table.add_column("Hooks", style="yellow")
        table.add_column("Enabled", style="bold")

        for p in plugins:
            enabled_str = "[green]✓[/green]" if p.get("enabled") else "[red]✗[/red]"
            hooks = ", ".join(p.get("hooks", [])) or "-"
            table.add_row(
                p.get("name", "-"),
                p.get("version", "-"),
                p.get("description", "")[:60],
                hooks,
                enabled_str,
            )
        console.print(table)

    except httpx.ConnectError:
        console.print("[red]✗ Cannot connect to API. Is the backend running?[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


def _toggle_plugin(base_url: str, name: str, enable: bool) -> None:
    action = "enable" if enable else "disable"
    try:
        resp = httpx.post(f"{base_url}/plugins/{name}/{action}", timeout=10)
        resp.raise_for_status()
        result = resp.json()
        console.print(f"[green]✓ Plugin '{name}' {action}d[/green]")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]✗ Plugin '{name}' not found[/red]")
        else:
            console.print(f"[red]✗ Error: {e}[/red]")
    except httpx.ConnectError:
        console.print("[red]✗ Cannot connect to API[/red]")


def _reload_plugin(base_url: str, name: str) -> None:
    if not Confirm.ask(f"[yellow]Reload plugin '{name}'?[/yellow]"):
        return
    try:
        resp = httpx.post(f"{base_url}/plugins/{name}/reload", timeout=10)
        resp.raise_for_status()
        console.print(f"[green]✓ Plugin '{name}' reloaded[/green]")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            console.print(f"[red]✗ Plugin '{name}' not found[/red]")
        else:
            console.print(f"[red]✗ Error: {e}[/red]")
    except httpx.ConnectError:
        console.print("[red]✗ Cannot connect to API[/red]")
