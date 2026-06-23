import typer
import httpx
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Confirm

from openpaper_cli.utils.console import console
from openpaper_cli.core import ConfigManager


def agents_cmd(
    instance: str = typer.Option("default", "--instance", "-i", help="Instance name"),
    list_mode: bool = typer.Option(False, "--list", "-l", help="List all agents"),
    create: bool = typer.Option(False, "--create", "-c", help="Create a new agent"),
    delete: int = typer.Option(None, "--delete", "-d", help="Delete agent by ID"),
    name: str = typer.Option(None, "--name", "-n", help="Agent name"),
    model: str = typer.Option("llama3.1", "--model", "-m", help="Model for new agent"),
    provider: str = typer.Option("ollama", "--provider", "-p", help="Provider for new agent"),
):
    """Manage AI agents through the API."""
    config = ConfigManager(instance)
    base_url = f"http://{config.get('api_host')}:{config.get('api_port')}/api/v1"

    if create:
        if not name:
            console.print("[red]✗ --name is required for agent creation[/red]")
            raise typer.Exit(1)
        _create_agent(base_url, name, model, provider)
        return

    if delete:
        _delete_agent(base_url, delete)
        return

    if list_mode or True:
        _list_agents(base_url)


def _list_agents(base_url: str) -> None:
    try:
        resp = httpx.get(f"{base_url}/agents/", timeout=10)
        if resp.status_code == 401:
            console.print("[red]✗ Authentication required. Start the backend first.[/red]")
            return
        resp.raise_for_status()
        agents = resp.json()

        if not agents:
            console.print("[dim]No agents found. Create one with --create[/dim]")
            return

        table = Table(box=box.SIMPLE, show_header=True, title="AI Agents")
        table.add_column("ID", style="bold", width=4)
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="dim")
        table.add_column("Model", style="dim")
        table.add_column("Provider", style="bold")
        table.add_column("Status", style="bold")

        for a in agents:
            status_style = {
                "idle": "[dim]idle[/dim]",
                "working": "[green]working[/green]",
                "error": "[red]error[/red]",
            }.get(a.get("status", ""), a.get("status", ""))
            table.add_row(
                str(a["id"]),
                a["name"],
                a.get("agent_type", "-"),
                a.get("model", "-"),
                a.get("provider", "ollama"),
                status_style,
            )
        console.print(table)

    except httpx.ConnectError:
        console.print("[red]✗ Cannot connect to API. Is the backend running?[/red]")
        console.print("[dim]  Run 'openpaper run' or 'openpaper doctor'[/dim]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


def _create_agent(base_url: str, name: str, model: str, provider: str) -> None:
    import json

    payload = {
        "name": name,
        "agent_type": "research",
        "model": model,
        "provider": provider,
    }

    try:
        resp = httpx.post(
            f"{base_url}/agents/",
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"},
        )
        if resp.status_code == 401:
            console.print("[red]✗ Authentication required[/red]")
            return
        resp.raise_for_status()
        agent = resp.json()
        console.print(f"[green]✓ Agent created:[/green] {agent['name']} (ID: {agent['id']})")
        console.print(f"   Model: {agent['model']} | Provider: {agent['provider']}")

    except httpx.ConnectError:
        console.print("[red]✗ Cannot connect to API. Is the backend running?[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")


def _delete_agent(base_url: str, agent_id: int) -> None:
    if not Confirm.ask(f"[yellow]Delete agent {agent_id}? This cannot be undone.[/yellow]", default=False):
        return

    try:
        resp = httpx.delete(f"{base_url}/agents/{agent_id}", timeout=10)
        if resp.status_code == 204:
            console.print(f"[green]✓ Agent {agent_id} deleted[/green]")
        elif resp.status_code == 404:
            console.print(f"[red]✗ Agent {agent_id} not found[/red]")
        else:
            resp.raise_for_status()
    except httpx.ConnectError:
        console.print("[red]✗ Cannot connect to API[/red]")
    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
