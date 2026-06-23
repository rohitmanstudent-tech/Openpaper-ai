"""openpaper login/logout/whoami — registry authentication."""

import sys
import click
from rich.console import Console
from rich.prompt import Prompt

from openpaper.registry import login as registry_login, register_user
from openpaper.config import set_auth, clear_auth, get_auth, get_token

console = Console()


@click.command(name="login")
@click.option("-e", "--email", help="Registry email")
@click.option("-p", "--password", help="Registry password (omit for prompt)")
@click.option("--register", is_flag=True, help="Create a new account")
@click.option("--username", help="Username (required with --register)")
def login(email: str, password: str, register: bool, username: str):
    """Authenticate with the OpenPaper Hub registry.

    \b
    Examples:
        openpaper login
        openpaper login -e user@example.com
        openpaper login --register --username myname
    """
    if not email:
        email = Prompt.ask("Email")

    if register:
        if not username:
            username = Prompt.ask("Username")
        if not password:
            password = Prompt.ask("Password", password=True)

        try:
            result = register_user(email=email, password=password, username=username)
        except Exception as e:
            console.print(f"[red]Registration failed: {e}[/red]")
            sys.exit(1)

        console.print("[green]✓ Account created! Logging in...[/green]")

    if not password:
        password = Prompt.ask("Password", password=True)

    try:
        result = registry_login(email=email, password=password)
    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        sys.exit(1)

    token = result.get("access_token", "")
    refresh = result.get("refresh_token", "")
    if not token:
        console.print("[red]No access token received[/red]")
        sys.exit(1)

    set_auth(token=token, refresh_token=refresh, email=email)
    console.print(f"[green]✓ Logged in as {email}[/green]")
    console.print("[dim]Credentials stored in ~/.config/openpaper/auth.json[/dim]")


@click.command(name="logout")
def logout():
    """Clear stored authentication."""
    if get_token():
        clear_auth()
        console.print("[green]✓ Logged out[/green]")
    else:
        console.print("[yellow]Not logged in[/yellow]")


@click.command(name="whoami")
def whoami():
    """Show current authenticated user."""
    auth = get_auth()
    email = auth.get("email", "")
    token = auth.get("token", "")

    if not token:
        console.print("[yellow]Not logged in[/yellow]")
        console.print("  Run 'openpaper login' to authenticate")
        return

    masked = email or "unknown"
    token_preview = f"{token[:20]}..." if len(token) > 20 else token
    console.print(f"Logged in as [bold cyan]{masked}[/bold cyan]")
    console.print(f"Token: {token_preview}")
