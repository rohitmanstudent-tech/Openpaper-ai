import json
import os
import sys
import typer
from pathlib import Path
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt, Confirm

from openpaper_cli import __version__, __app_name__
from openpaper_cli.utils.console import console
from openpaper_cli.utils.styles import BANNER, BANNER_COLORS
from openpaper_cli.commands import (
    onboard_cmd,
    run_cmd,
    doctor_cmd,
    configure_cmd,
    agents_cmd,
    models_cmd,
    dashboard_cmd,
    update_cmd,
)
from openpaper_cli.commands.plugins import plugins_cmd as plugins_cmd
from openpaper_cli.hub_registry import (
    search_packages, get_package, resolve_package,
    publish_package, unpublish_package, login as hub_login,
    register_user, get_registry_stats,
)
from openpaper_cli.hub_config import get_auth, get_token, set_auth, clear_auth

app = typer.Typer(
    name=__app_name__,
    help="Enterprise CLI for OpenPaper AI — manage agents, models, and infrastructure",
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _show_banner():
    for i, line in enumerate(BANNER.strip().split("\n")[:4]):
        console.print(f"[{BANNER_COLORS[i % len(BANNER_COLORS)]}]{line}[/]")
    console.print(f"\n  [bold cyan]v{__version__}[/bold cyan] — [dim]Enterprise AI Agent Platform[/dim]\n")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        _show_banner()
        console.print(Panel.fit(
            "[bold cyan]OpenPaper AI CLI[/bold cyan]\n\n"
            "Use [bold]openpaper --help[/bold] to see all commands.\n"
            "Use [bold]openpaper onboard[/bold] to get started.",
            border_style="cyan",
            box=box.ROUNDED,
        ))


# ── Enterprise Commands ─────────────────────────────

app.command(name="onboard")(onboard_cmd)
app.command(name="run")(run_cmd)
app.command(name="doctor")(doctor_cmd)
app.command(name="configure", help="View and manage configuration")(configure_cmd)
app.command(name="agents", help="Manage AI agents through the API")(agents_cmd)
app.command(name="models", help="List and manage AI models")(models_cmd)
app.command(name="dashboard", help="Open the web dashboard")(dashboard_cmd)
app.command(name="update", help="Update OpenPaper AI to the latest version")(update_cmd)
app.command(name="plugins", help="Manage OpenPaper AI plugins")(plugins_cmd)

# ── Hub Commands ────────────────────────────────────

@app.command()
def search(
    query: str = typer.Argument("", help="Search query"),
    package_type: str = typer.Option(None, "-t", "--type", help="Filter by type: agent, workflow, tool, provider"),
    sort: str = typer.Option("downloads", "--sort", help="Sort by: downloads, rating, name, created, updated"),
    page: int = typer.Option(1, "--page", help="Page number"),
    limit: int = typer.Option(20, "--limit", help="Results per page"),
    stats: bool = typer.Option(False, "--stats", help="Show registry stats instead of search"),
):
    """Search the OpenPaper Hub registry for packages."""
    if stats:
        try:
            data = get_registry_stats()
            console.print("\n[bold cyan]OpenPaper Hub Registry Stats[/bold cyan]")
            console.print(f"  Total packages:     [green]{data.get('total_packages', 0)}[/green]")
            console.print(f"  Verified publishers: [green]{data.get('verified_publishers', 0)}[/green]")
            console.print(f"  Registry URL:        [blue]{data.get('registry_url', '')}[/blue]")
            type_breakdown = data.get("type_breakdown", {})
            if type_breakdown:
                console.print("\n[bold]By Type:[/bold]")
                for ptype, count in type_breakdown.items():
                    console.print(f"  {ptype.capitalize()}: {count}")
            console.print()
            return
        except Exception as e:
            console.print(f"[red]Failed to fetch stats: {e}[/red]")
            raise typer.Exit(1)

    try:
        data = search_packages(query=query, package_type=package_type, sort=sort, page=page, page_size=limit)
    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        raise typer.Exit(1)

    items = data.get("items", [])
    total = data.get("total", 0)

    if not items:
        console.print("[yellow]No packages found.[/yellow]")
        return

    table = Table(box=box.SIMPLE, header_style="bold cyan")
    table.add_column("Package ID", style="blue")
    table.add_column("Name")
    table.add_column("Type", style="magenta")
    table.add_column("Version", style="green")
    table.add_column("Rating", justify="right")
    table.add_column("Downloads", justify="right")
    table.add_column("Author")

    for item in items:
        stars = "★" * int(item.get("average_rating", 0)) if item.get("average_rating") else ""
        table.add_row(
            item.get("id", ""),
            item.get("name", ""),
            item.get("package_type", "").capitalize(),
            f"v{item.get('current_version', '')}",
            f"{item.get('average_rating', 0):.1f} {stars}",
            str(item.get("downloads", 0)),
            item.get("author", ""),
        )

    console.print(table)
    console.print(f"\n[dim]Showing {len(items)} of {total} results[/dim]")


@app.command()
def install(
    package_spec: str = typer.Argument(..., help="Package spec (e.g. export-agent, sales-agent@1.1.0)"),
    save: bool = typer.Option(False, "--save", help="Save to lockfile (openpaper.lock)"),
    no_deps: bool = typer.Option(False, "--no-deps", help="Skip dependency installation"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be installed"),
):
    """Install a package from the OpenPaper Hub registry."""
    if "@" in package_spec:
        package_id, version = package_spec.split("@", 1)
    else:
        package_id = package_spec
        version = ""

    console.print(f"Resolving [bold cyan]{package_id}[/bold cyan]...")

    try:
        data = resolve_package(package_id, version=version)
    except Exception as e:
        console.print(f"[red]Failed to resolve '{package_id}': {e}[/red]")
        raise typer.Exit(1)

    if not data.get("success"):
        console.print(f"[red]Resolution failed: {data}[/red]")
        raise typer.Exit(1)

    resolution = data.get("resolution", {})
    dep_chain = data.get("dependency_chain", [])

    if dry_run:
        console.print(f"\n[bold cyan]Would install:[/bold cyan]")
        tbl = Table(box=box.SIMPLE, header_style="bold cyan")
        tbl.add_column("Package")
        tbl.add_column("Version")
        tbl.add_column("Type")
        tbl.add_column("Permissions")

        pkg_type = resolution.get("manifest", {}).get("package_type", "?")
        perms = ", ".join(resolution.get("permissions_requested", []) or [])
        tbl.add_row(resolution.get("name", package_id), f"v{resolution.get('version', '')}", pkg_type.capitalize(), perms or "none")

        for dep in dep_chain:
            dep_type = dep.get("manifest", {}).get("package_type", "?")
            dep_perms = ", ".join(dep.get("permissions_requested", []) or [])
            tbl.add_row(dep.get("name", ""), f"v{dep.get('version', '')}", dep_type.capitalize(), dep_perms or "none")

        console.print(tbl)
        console.print()

        if resolution.get("signature"):
            console.print("[green]✓ Package is signed[/green]")
        else:
            console.print("[yellow]⚠ Package is not signed[/yellow]")

        return

    if no_deps:
        console.print(f"Would install [bold]{resolution.get('name', package_id)}[/bold] v{resolution.get('version', '')} (dependencies skipped)")
    else:
        console.print(f"Installing [bold]{resolution.get('name', package_id)}[/bold] v{resolution.get('version', '')}...")
        for dep in dep_chain:
            console.print(f"  Dependency: [blue]{dep.get('name', '')}[/blue] v{dep.get('version', '')}")
        if dep_chain:
            console.print(f"[green]✓ {len(dep_chain)} dependenc{'y' if len(dep_chain) == 1 else 'ies'} resolved[/green]")

    perms = resolution.get("permissions_requested", [])
    if perms:
        console.print(f"\n[yellow]Permissions requested:[/yellow]")
        for p in perms:
            console.print(f"  • {p}")

    checksum = resolution.get("checksum_sha256", "")
    if checksum:
        console.print(f"[dim]Checksum: {checksum[:16]}...[/dim]")

    if save:
        lock_entry = {
            "name": resolution.get("name", package_id),
            "version": version or "*",
            "resolved": resolution.get("version", ""),
            "checksum": checksum,
            "dependencies": [d.get("package_id", d.get("name", "")) for d in dep_chain],
        }
        lockfile_path = "openpaper.lock"
        existing = {}
        if os.path.exists(lockfile_path):
            try:
                existing = json.loads(open(lockfile_path).read())
            except (json.JSONDecodeError, OSError):
                pass

        packages = existing.get("packages", {})
        packages[resolution.get("package_id", package_id)] = lock_entry
        for dep in dep_chain:
            dep_id = dep.get("package_id", dep.get("name", ""))
            if dep_id:
                packages[dep_id] = {
                    "name": dep.get("name", ""),
                    "version": "*",
                    "resolved": dep.get("version", ""),
                    "checksum": dep.get("checksum_sha256", ""),
                    "dependencies": [],
                }

        lockfile = {"lockfile_version": 1, "packages": packages}
        with open(lockfile_path, "w") as f:
            json.dump(lockfile, f, indent=2)
        console.print(f"[green]✓ Lockfile written to {lockfile_path}[/green]")

    console.print(f"\n[green]✓ '{resolution.get('name', package_id)}' v{resolution.get('version', '')} resolved successfully[/green]")
    console.print("  Use the dashboard to complete the install: openpaper.ai/marketplace")


@app.command()
def publish(
    package_dir: str = typer.Argument(".", help="Directory containing the package manifest"),
    manifest_path: str = typer.Option(None, "-m", "--manifest", help="Path to manifest file"),
    visibility: str = typer.Option("public", "--visibility", help="Visibility: public, private"),
    sign: bool = typer.Option(False, "--sign", help="Sign the package (requires signing key)"),
    key_id: str = typer.Option(None, "--key-id", help="Signing key ID (required with --sign)"),
    private_key: str = typer.Option(None, "--private-key", help="Path to private key file (required with --sign)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate manifest without publishing"),
):
    """Publish a package to the OpenPaper Hub registry."""
    import yaml
    from openpaper_cli.hub_signer import sign_manifest as do_sign

    MANIFEST_FILES = ["openpaper.json", "openpaper.yaml", "openpaper.yml", "plugin.json", "plugin.yaml", "plugin.yml"]

    if not get_token():
        console.print("[red]Not authenticated. Run 'openpaper login' first.[/red]")
        raise typer.Exit(1)

    pkg_dir = Path(package_dir)
    if not pkg_dir.is_dir():
        console.print(f"[red]Directory not found: {package_dir}[/red]")
        raise typer.Exit(1)

    manifest_data = None
    if manifest_path:
        m_path = Path(manifest_path)
        if m_path.exists():
            raw = m_path.read_text(encoding="utf-8")
            if m_path.suffix in (".yaml", ".yml"):
                manifest_data = yaml.safe_load(raw)
            else:
                manifest_data = json.loads(raw)
    else:
        for filename in MANIFEST_FILES:
            manifest_path = pkg_dir / filename
            if manifest_path.exists():
                raw = manifest_path.read_text(encoding="utf-8")
                if manifest_path.suffix in (".yaml", ".yml"):
                    manifest_data = yaml.safe_load(raw)
                else:
                    manifest_data = json.loads(raw)
                break

    if not manifest_data:
        console.print(f"[red]No manifest found in '{package_dir}'.[/red]")
        console.print("  Create an openpaper.json or openpaper.yaml with: name, version, package_type, description")
        raise typer.Exit(1)

    if (pkg_dir / "plugin.py").exists() and not manifest_data.get("entrypoint"):
        manifest_data["entrypoint"] = "plugin.py"
    if (pkg_dir / "README.md").exists() and not manifest_data.get("readme"):
        manifest_data["readme"] = (pkg_dir / "README.md").read_text(encoding="utf-8")

    required = ["name", "version", "package_type"]
    missing = [r for r in required if r not in manifest_data]
    if missing:
        console.print(f"[red]Missing required fields in manifest: {', '.join(missing)}[/red]")
        raise typer.Exit(1)

    valid_types = ["agent", "workflow", "tool", "provider"]
    if manifest_data["package_type"] not in valid_types:
        console.print(f"[red]Invalid package_type. Must be one of: {', '.join(valid_types)}[/red]")
        raise typer.Exit(1)

    console.print(f"\n[bold cyan]Publishing:[/bold cyan] {manifest_data['name']} v{manifest_data['version']}")
    console.print(f"  Type:        {manifest_data['package_type'].capitalize()}")
    console.print(f"  Visibility:  {visibility}")
    console.print(f"  Description: {manifest_data.get('description', '(none)')}")
    deps = manifest_data.get("dependencies", [])
    if deps:
        console.print(f"  Dependencies: {', '.join(deps)}")
    perms = manifest_data.get("permissions", [])
    if perms:
        console.print(f"  Permissions:  {', '.join(perms)}")

    signature = ""
    sig_key_id = key_id or ""
    if sign:
        if not key_id or not private_key:
            console.print("[red]--sign requires both --key-id and --private-key[/red]")
            raise typer.Exit(1)
        try:
            key_data = Path(private_key).read_text().strip()
            signature = do_sign(manifest_data, key_data)
            console.print("[green]✓ Package signed[/green]")
        except Exception as e:
            console.print(f"[red]Failed to sign package: {e}[/red]")
            raise typer.Exit(1)

    if dry_run:
        console.print("\n[green]✓ Manifest validation passed (dry run)[/green]")
        return

    try:
        changelog = ""
        if (pkg_dir / "CHANGELOG.md").exists():
            changelog = (pkg_dir / "CHANGELOG.md").read_text(encoding="utf-8")
        result = publish_package(manifest=manifest_data, changelog=changelog, signature=signature, signature_key_id=sig_key_id, visibility=visibility)
    except Exception as e:
        console.print(f"[red]Publishing failed: {e}[/red]")
        if hasattr(e, "response") and hasattr(e.response, "text"):
            console.print(f"[dim]{e.response.text}[/dim]")
        raise typer.Exit(1)

    if result.get("success"):
        pkg_id = result.get("package_id", manifest_data["name"])
        ver = result.get("version", manifest_data["version"])
        sig_ok = result.get("signature_verified", False)
        sig_text = " [green](signature verified)[/green]" if sig_ok else " [yellow](not signed)[/yellow]"
        console.print(f"\n[green]✓ Published '{pkg_id}' v{ver}{sig_text}[/green]")
    else:
        console.print(f"[red]Publishing failed: {result.get('message', 'unknown error')}[/red]")
        raise typer.Exit(1)


@app.command()
def unpublish(
    package_id: str = typer.Argument(..., help="Package ID to unpublish"),
    force: bool = typer.Option(False, "--force", help="Skip confirmation"),
    yes: bool = typer.Option(False, "--yes", help="Automatically confirm"),
):
    """Unpublish a package from the OpenPaper Hub registry."""
    if not get_token():
        console.print("[red]Not authenticated. Run 'openpaper login' first.[/red]")
        raise typer.Exit(1)

    try:
        pkg = get_package(package_id)
        name = pkg.get("name", package_id)
        ver = pkg.get("current_version", "?")
        author = pkg.get("author", "?")
    except Exception:
        name = package_id
        ver = "?"
        author = "?"

    confirmed = yes or force
    if not confirmed:
        confirmed = Confirm.ask(f"Unpublish [bold cyan]{name}[/bold cyan] v{ver} by {author}?")

    if not confirmed:
        console.print("[yellow]Cancelled.[/yellow]")
        return

    try:
        result = unpublish_package(package_id)
    except Exception as e:
        console.print(f"[red]Failed to unpublish: {e}[/red]")
        raise typer.Exit(1)

    if result.get("success"):
        console.print(f"[green]✓ '{name}' unpublished[/green]")
    else:
        console.print(f"[red]Failed: {result.get('message', 'unknown error')}[/red]")
        raise typer.Exit(1)


@app.command()
def login(
    email: str = typer.Option(None, "-e", "--email", help="Registry email"),
    password: str = typer.Option(None, "-p", "--password", help="Registry password (omit for prompt)"),
    do_register: bool = typer.Option(False, "--register", help="Create a new account"),
    username: str = typer.Option(None, "--username", help="Username (required with --register)"),
):
    """Authenticate with the OpenPaper Hub registry."""
    if not email:
        email = Prompt.ask("Email")

    if do_register:
        if not username:
            username = Prompt.ask("Username")
        if not password:
            password = Prompt.ask("Password", password=True)
        try:
            result = register_user(email=email, password=password, username=username)
        except Exception as e:
            console.print(f"[red]Registration failed: {e}[/red]")
            raise typer.Exit(1)
        console.print("[green]✓ Account created! Logging in...[/green]")

    if not password:
        password = Prompt.ask("Password", password=True)

    try:
        result = hub_login(email=email, password=password)
    except Exception as e:
        console.print(f"[red]Login failed: {e}[/red]")
        raise typer.Exit(1)

    token = result.get("access_token", "")
    refresh = result.get("refresh_token", "")
    if not token:
        console.print("[red]No access token received[/red]")
        raise typer.Exit(1)

    set_auth(token=token, refresh_token=refresh, email=email)
    console.print(f"[green]✓ Logged in as {email}[/green]")
    console.print("[dim]Credentials stored in ~/.config/openpaper/auth.json[/dim]")


@app.command()
def logout():
    """Clear stored authentication for the Hub registry."""
    if get_token():
        clear_auth()
        console.print("[green]✓ Logged out[/green]")
    else:
        console.print("[yellow]Not logged in[/yellow]")


@app.command()
def whoami():
    """Show current authenticated Hub user."""
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

if __name__ == "__main__":
    app()
