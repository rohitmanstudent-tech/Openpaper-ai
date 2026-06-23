import typer
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich import box

from openpaper_cli.utils.console import console
from openpaper_cli.utils.styles import BANNER, BANNER_COLORS
from openpaper_cli.core import ConfigManager
from openpaper_cli.core.secrets import SecretsManager
from openpaper_cli.core.detector import SystemDetector
from openpaper_cli.core.docker import DockerManager


def onboard_cmd(
    instance: str = typer.Option("default", "--instance", "-i", help="Instance name"),
    force: bool = typer.Option(False, "--force", "-f", help="Force re-onboard"),
):
    """Interactive first-time setup wizard for OpenPaper AI."""

    config = ConfigManager(instance)
    secrets = SecretsManager(instance)
    detector = SystemDetector()

    if config.get("onboarded") and not force:
        console.print("[warning]Already onboarded. Use --force to re-run.[/warning]")
        return

    console.print()
    for i, line in enumerate(BANNER.strip().split("\n")):
        console.print(f"[{BANNER_COLORS[i % len(BANNER_COLORS)]}]{line}[/]")
    console.print()
    console.print(Panel.fit(
        "[bold cyan]OpenPaper AI[/] [dim]v1.0.0[/]\n"
        "[dim]Enterprise AI Agent Management Platform[/]\n\n"
        "This wizard will guide you through:\n"
        "  • System dependency checks\n"
        "  • Configuration setup\n"
        "  • Docker environment initialization\n"
        "  • Secret key generation\n"
        "  • Model installation",
        border_style="cyan",
        box=box.ROUNDED,
    ))

    if not Confirm.ask("\n[bold]Continue with setup?[/]", default=True):
        console.print("[warning]Setup cancelled.[/warning]")
        raise typer.Exit()

    console.print("\n[bold cyan]Step 1: System Requirements[/bold cyan]")

    checks = [
        ("Docker", detector.check_docker()),
        ("Docker Compose", detector.check_docker_compose()),
        ("Python 3.11+", detector.check_python_version()),
        ("Git", detector.check_git()),
    ]

    table = Table(box=box.SIMPLE, show_header=False)
    table.add_column("Check", style="bold")
    table.add_column("Status", style="bold")
    table.add_column("Detail", style="dim")

    all_pass = True
    for name, (ok, detail) in checks:
        status = "[green]✓ Pass[/green]" if ok else "[red]✗ Fail[/red]"
        table.add_row(name, status, detail)
        if not ok:
            all_pass = False

    console.print(table)

    ollama_ok, ollama_ver = detector.check_ollama()
    if ollama_ok:
        console.print(f"[green]✓ Ollama detected:[/green] {ollama_ver}")
    else:
        console.print("[yellow]! Ollama not detected (optional, local AI)[/yellow]")

    gpu_ok, gpu_info = detector.check_nvidia_gpu()
    if gpu_ok:
        console.print(f"[green]✓ NVIDIA GPU:[/green] {gpu_info}")
    else:
        console.print("[dim]! No NVIDIA GPU detected[/dim]")

    if not all_pass:
        if not Confirm.ask("\n[yellow]Some requirements are missing. Continue anyway?[/yellow]", default=False):
            console.print("[warning]Setup cancelled. Install missing dependencies.[/warning]")
            raise typer.Exit()

    console.print("\n[bold cyan]Step 2: Configuration[/bold cyan]")

    config.set("instance", instance)
    config.set("api_host", Prompt.ask("API Host", default=config.get("api_host", "localhost")))
    config.set("api_port", int(Prompt.ask("API Port", default=str(config.get("api_port", 8000)))))

    if not config.get("postgres_password"):
        import secrets as sec
        config.set("postgres_password", sec.token_hex(16))

    if not config.get("secret_key"):
        config.set("secret_key", ConfigManager.generate_secret_key())

    console.print("\n[bold cyan]Step 3: API Keys (optional)[/bold cyan]")
    console.print("[dim]Press Enter to skip any provider[/dim]")

    api_keys = [
        ("openai_api_key", "OpenAI"),
        ("anthropic_api_key", "Anthropic Claude"),
        ("google_api_key", "Google Gemini"),
        ("xai_api_key", "xAI Grok"),
        ("deepseek_api_key", "DeepSeek"),
        ("openrouter_api_key", "OpenRouter"),
        ("nvidia_api_key", "NVIDIA NIM"),
    ]

    for key, label in api_keys:
        value = Prompt.ask(f"  {label} API Key", default="", password=True)
        if value:
            secrets.set(key, value)
            console.print(f"  [green]✓[/green] {label} key stored securely")

    config.set("local_first", Confirm.ask(
        "\nEnable Local-First mode? (Ollama before cloud)", default=False
    ))

    config.set("auto_start", Confirm.ask(
        "Auto-start services on 'openpaper run'?", default=True
    ))

    config.save()
    console.print("\n[green]✓ Configuration saved[/green]")

    console.print("\n[bold cyan]Step 4: Initialize Environment[/bold cyan]")

    docker = DockerManager(instance)
    if docker.has_compose_file():
        console.print(f"[dim]Found docker-compose.yml at: {docker.compose_file}[/dim]")
        if Confirm.ask("Start Docker services now?", default=True):
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
    else:
        console.print("[yellow]! docker-compose.yml not found in current directory[/yellow]")
        console.print("[dim]  You can run 'openpaper run' later from the project directory[/dim]")

    console.print("\n[bold cyan]Step 5: Pull AI Model[/bold cyan]")
    if Confirm.ask("Pull default model (llama3.1)?", default=True):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Pulling llama3.1...", total=None)
            docker = DockerManager(instance)
            ok, msg = docker.pull_model("llama3.1")
        if ok:
            console.print(f"[green]✓ {msg}[/green]")
        else:
            console.print(f"[yellow]! {msg}[/yellow]")

    console.print()
    console.print(Panel.fit(
        "[bold green]Setup Complete![/bold green]\n\n"
        "What's next?\n"
        "  • [bold]openpaper dashboard[/bold]  — Open web interface\n"
        "  • [bold]openpaper run[/bold]        — Start all services\n"
        "  • [bold]openpaper doctor[/bold]     — Check system health\n"
        "  • [bold]openpaper agents[/bold]     — List your AI agents",
        border_style="green",
        box=box.ROUNDED,
    ))
    console.print()
