import typer
from rich.panel import Panel
from rich.table import Table
from rich import box
from openpaper_cli.utils.console import console
from openpaper_cli.utils.styles import BANNER
from openpaper_cli.core.detector import SystemDetector
from openpaper_cli.core.docker import DockerManager
from openpaper_cli.core import ConfigManager


def doctor_cmd(
    instance: str = typer.Option("default", "--instance", "-i", help="Instance name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed info"),
):
    """Run comprehensive system diagnostics for OpenPaper AI."""
    detector = SystemDetector()
    docker = DockerManager(instance)
    config = ConfigManager(instance)

    console.print(f"\n[bold cyan]OpenPaper AI — System Diagnostics[/bold cyan] [dim](instance: {instance})[/dim]\n")

    sys_info = detector.get_system_info()
    info_table = Table(box=box.SIMPLE, show_header=False)
    info_table.add_column("Property", style="bold")
    info_table.add_column("Value", style="dim")
    for key, value in sys_info.items():
        info_table.add_row(key.replace("_", " ").title(), value)
    console.print(Panel(info_table, title="[bold]System Information[/bold]", border_style="cyan", box=box.ROUNDED))

    console.print("\n[bold]Dependency Checks[/bold]")
    dep_table = Table(box=box.SIMPLE, show_header=True)
    dep_table.add_column("Component", style="bold")
    dep_table.add_column("Status", style="bold")
    dep_table.add_column("Detail", style="dim")

    checks = [
        ("Docker Engine", *detector.check_docker()),
        ("Docker Compose", *detector.check_docker_compose()),
        ("Python 3.11+", *detector.check_python_version()),
    ]
    for name, ok, detail in checks:
        status = "[green]✓[/green]" if ok else "[red]✗[/red]"
        dep_table.add_row(name, status, detail)

    ollama_ok, ollama_ver = detector.check_ollama()
    dep_table.add_row(
        "Ollama",
        "[green]✓[/green]" if ollama_ok else "[yellow]![/yellow]",
        ollama_ver if ollama_ok else "Not installed (optional)",
    )

    gpu_ok, gpu_info = detector.check_nvidia_gpu()
    dep_table.add_row(
        "NVIDIA GPU",
        "[green]✓[/green]" if gpu_ok else "[dim]–[/dim]",
        gpu_info,
    )

    console.print(dep_table)

    console.print("\n[bold]Installed Models[/bold]")
    models = detector.get_installed_models()
    if models:
        model_table = Table(box=box.SIMPLE, show_header=True)
        model_table.add_column("Model", style="cyan")
        model_table.add_column("Source", style="dim")
        for m in models:
            model_table.add_row(m["name"], m.get("source", "unknown"))
        console.print(model_table)
    else:
        console.print("[dim]  No AI models detected. Run 'openpaper run' then 'ollama pull llama3.1'[/dim]")

    console.print("\n[bold]Service Status[/bold]")
    if docker.has_compose_file():
        if docker.is_running():
            statuses = docker.get_status()
            svc_table = Table(box=box.SIMPLE, show_header=True)
            svc_table.add_column("Service", style="bold")
            svc_table.add_column("Status", style="bold")
            svc_table.add_column("Ports", style="dim")
            for svc in statuses:
                st = "[green]running[/green]" if svc["status"] == "running" else "[red]stopped[/red]"
                svc_table.add_row(svc["name"], st, svc.get("ports", "") or "-")
            console.print(svc_table)
        else:
            console.print("[yellow]  ! Services are not running[/yellow]")
            console.print("[dim]  Run 'openpaper run' to start[/dim]")
    else:
        console.print("[dim]  No docker-compose.yml found in current directory[/dim]")

    console.print("\n[bold]Port Checks[/bold]")
    ports = [
        config.get("api_port", 8000),
        config.get("frontend_port", 3000),
        config.get("postgres_port", 5432),
        config.get("redis_port", 6379),
        config.get("qdrant_port", 6333),
        config.get("ollama_port", 11434),
    ]
    port_results = detector.check_ports(ports)
    port_table = Table(box=box.SIMPLE, show_header=True)
    port_table.add_column("Port", style="bold")
    port_table.add_column("Status", style="bold")
    port_table.add_column("Service", style="dim")

    port_map = {8000: "API", 3000: "Frontend", 5432: "PostgreSQL", 6379: "Redis", 6333: "Qdrant", 11434: "Ollama"}
    for p in port_results:
        in_use = p["in_use"]
        service_name = port_map.get(p["port"], "Unknown")
        if in_use:
            port_table.add_row(str(p["port"]), "[yellow]in use[/yellow]", service_name)
        else:
            port_table.add_row(str(p["port"]), "[green]available[/green]", service_name)
    console.print(port_table)

    if verbose:
        console.print("\n[bold]Configuration[/bold]")
        cfg_table = Table(box=box.SIMPLE, show_header=True)
        cfg_table.add_column("Key", style="bold")
        cfg_table.add_column("Value", style="dim")
        for k, v in config.get_all().items():
            if "key" in k.lower() or "secret" in k.lower() or "password" in k.lower():
                v = "••••••••" if v else "(empty)"
            cfg_table.add_row(k, str(v))
        console.print(cfg_table)

    console.print("\n[bold green]Diagnostics complete.[/bold green]")
