import typer
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.syntax import Syntax

from openpaper_cli.utils.console import console
from openpaper_cli.core import ConfigManager
from openpaper_cli.core.secrets import SecretsManager


def configure_cmd(
    instance: str = typer.Option("default", "--instance", "-i", help="Instance name"),
    key: str = typer.Option(None, "--key", "-k", help="Config key to set"),
    value: str = typer.Option(None, "--value", "-v", help="Config value to set"),
    show_secrets: bool = typer.Option(False, "--show-secrets", help="Reveal secret values"),
    export: bool = typer.Option(False, "--export", help="Export config as env vars"),
):
    """View and manage OpenPaper AI configuration."""
    config = ConfigManager(instance)
    secrets = SecretsManager(instance)

    if key and value is not None:
        config.set(key, value)
        config.save()
        console.print(f"[green]✓[/green] Set [bold]{key}[/bold] = {value}")
        return

    if key:
        val = config.get(key)
        if val is None:
            val = secrets.get(key)
            if val is None:
                console.print(f"[red]✗ Key '{key}' not found[/red]")
                raise typer.Exit(1)
            if not show_secrets:
                val = "••••••••"
        console.print(f"[bold]{key}[/bold] = {val}")
        return

    console.print(f"\n[bold cyan]Configuration[/bold cyan] [dim](instance: {instance})[/dim]\n")

    all_config = config.get_all()
    cfg_table = Table(box=box.SIMPLE, show_header=True)
    cfg_table.add_column("Key", style="bold cyan")
    cfg_table.add_column("Value", style="dim")
    cfg_table.add_column("Actions", style="bold", width=12)

    for k, v in sorted(all_config.items()):
        is_secret = any(kw in k.lower() for kw in ["key", "secret", "password", "token"])
        if is_secret and v and not show_secrets:
            display = "••••••••"
        elif v is None or v == "":
            display = "[dim](empty)[/dim]"
        else:
            display = str(v)
        cfg_table.add_row(k, display, "[dim]edit[/dim]")

    console.print(cfg_table)

    secret_keys = secrets.list_keys()
    if secret_keys:
        console.print(f"\n[bold]Encrypted Secrets ({len(secret_keys)} stored)[/bold]")
        sec_table = Table(box=box.SIMPLE, show_header=True)
        sec_table.add_column("Key", style="bold cyan")
        sec_table.add_column("Value", style="dim")
        for sk in secret_keys:
            sv = secrets.get(sk)
            display = "••••••••" if sv and not show_secrets else (sv or "[dim](empty)[/dim]")
            sec_table.add_row(sk, display)
        console.print(sec_table)

    if export:
        console.print("\n[bold]Environment Variables[/bold]")
        lines = []
        for k, v in config.get_compose_env().items():
            lines.append(f"export {k}={v}")
        env_text = "\n".join(lines)
        console.print(Syntax(env_text, "bash", theme="monokai"))

    config.save()
