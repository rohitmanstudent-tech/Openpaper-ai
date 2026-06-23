import typer
import httpx
from rich.table import Table
from rich import box
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from openpaper_cli.utils.console import console
from openpaper_cli.core import ConfigManager
from openpaper_cli.core.detector import SystemDetector
from openpaper_cli.core.docker import DockerManager


def models_cmd(
    instance: str = typer.Option("default", "--instance", "-i", help="Instance name"),
    list_mode: bool = typer.Option(False, "--list", "-l", help="List available models"),
    pull: str = typer.Option(None, "--pull", "-p", help="Pull a model (e.g., llama3.1)"),
    remote: bool = typer.Option(False, "--remote", "-r", help="Show cloud models from API"),
    provider: str = typer.Option(None, "--provider", help="Filter models by provider"),
):
    """List and manage AI models."""
    config = ConfigManager(instance)
    detector = SystemDetector()

    if pull:
        _pull_model(pull, instance)
        return

    if remote:
        _list_remote_models(config, provider)
        return

    _list_local_models(detector)


def _list_local_models(detector: SystemDetector) -> None:
    console.print("[bold cyan]Local Models[/bold cyan]")
    models = detector.get_installed_models()

    if models:
        table = Table(box=box.SIMPLE, show_header=True)
        table.add_column("Model", style="cyan")
        table.add_column("Source", style="dim")
        table.add_column("Provider", style="dim")

        for m in models:
            table.add_row(m["name"], m.get("source", "ollama"), m.get("provider", "ollama"))
        console.print(table)
    else:
        console.print("[dim]  No local models detected[/dim]")
        console.print("[dim]  Run 'openpaper models --pull llama3.1' to install[/dim]")

    _, ollama_ok = detector.check_ollama()
    gpu_ok, gpu_info = detector.check_nvidia_gpu()
    console.print(f"\n  Ollama: [green]available[/green]" if detector.check_ollama() else "\n  Ollama: [dim]not detected[/dim]")
    console.print(f"  GPU:    [green]{gpu_info.split('(')[0].strip()}[/green]" if gpu_ok else "  GPU:    [dim]not detected[/dim]")


def _list_remote_models(config: ConfigManager, provider_filter: str | None) -> None:
    base_url = f"http://{config.get('api_host')}:{config.get('api_port')}/api/v1"
    try:
        url = f"{base_url}/models/"
        if provider_filter:
            url += f"?provider={provider_filter}"
        resp = httpx.get(url, timeout=15)
        resp.raise_for_status()
        models = resp.json()

        if not models:
            console.print("[dim]No models returned from API[/dim]")
            return

        table = Table(box=box.SIMPLE, show_header=True, title="Available Models")
        table.add_column("Model ID", style="cyan")
        table.add_column("Provider", style="bold")
        table.add_column("Context", style="dim")
        table.add_column("Input $/1K", style="dim")
        table.add_column("Output $/1K", style="dim")
        table.add_column("Available", style="bold")

        for m in models[:50]:
            avail = "[green]✓[/green]" if m.get("available") else "[red]✗[/red]"
            table.add_row(
                m.get("id", "-"),
                m.get("provider", "-"),
                str(m.get("context_length", "-")),
                f"${m.get('pricing_input_per_1k', 0):.4f}",
                f"${m.get('pricing_output_per_1k', 0):.4f}",
                avail,
            )
        console.print(table)
        if len(models) > 50:
            console.print(f"[dim]  ... and {len(models) - 50} more[/dim]")

    except httpx.ConnectError:
        console.print("[red]✗ Cannot connect to API. Start the backend first.[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


def _pull_model(model: str, instance: str) -> None:
    docker = DockerManager(instance)

    if not docker.is_running():
        console.print("[yellow]! Docker services are not running[/yellow]")
        if not Confirm.ask("Start services first?", default=True):
            return
        ok, msg = docker.up()
        if not ok:
            console.print(f"[red]✗ {msg}[/red]")
            return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=False,
    ) as progress:
        task_id = progress.add_task(f"Pulling model '{model}'...", total=None)
        ok, msg = docker.pull_model(model)
        progress.remove_task(task_id)

    if ok:
        console.print(f"[green]✓ {msg}[/green]")
    else:
        console.print(f"[yellow]! {msg}[/yellow]")
        console.print("[dim]  You can also run: ollama pull " + model + "[/dim]")
