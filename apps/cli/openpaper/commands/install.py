"""openpaper install — install packages from the remote registry."""

import os
import json
import sys
import click
from rich.console import Console
from rich.table import Table
from rich import box

from openpaper.registry import resolve_package
from openpaper.config import get_config, set_config

console = Console()


@click.command(name="install")
@click.argument("package_spec", required=True)
@click.option("--save", is_flag=True, help="Save to lockfile (openpaper.lock)")
@click.option("--no-deps", is_flag=True, help="Skip dependency installation")
@click.option("--dry-run", is_flag=True, help="Show what would be installed")
def install(package_spec: str, save: bool, no_deps: bool, dry_run: bool):
    """Install a package from the OpenPaper Hub registry.

    \b
    Package spec formats:
        openpaper install export-agent
        openpaper install export-agent@1.0.0
        openpaper install sales-agent@^1.0.0
        openpaper install workflow-uae-buyers

    \b
    Examples:
        openpaper install export-agent
        openpaper install sales-agent
        openpaper install workflow-uae-buyers
    """
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
        sys.exit(1)

    if not data.get("success"):
        console.print(f"[red]Resolution failed: {data}[/red]")
        sys.exit(1)

    resolution = data.get("resolution", {})
    dep_chain = data.get("dependency_chain", [])

    if dry_run:
        console.print(f"\n[bold cyan]Would install:[/bold cyan]")
        table = Table(box=box.SIMPLE, header_style="bold cyan")
        table.add_column("Package")
        table.add_column("Version")
        table.add_column("Type")
        table.add_column("Permissions")

        pkg_type = resolution.get("manifest", {}).get("package_type", "?")
        perms = ", ".join(resolution.get("permissions_requested", []) or [])
        table.add_row(
            resolution.get("name", package_id),
            f"v{resolution.get('version', '')}",
            pkg_type.capitalize(),
            perms or "none",
        )

        for dep in dep_chain:
            dep_type = dep.get("manifest", {}).get("package_type", "?")
            dep_perms = ", ".join(dep.get("permissions_requested", []) or [])
            table.add_row(
                dep.get("name", ""),
                f"v{dep.get('version', '')}",
                dep_type.capitalize(),
                dep_perms or "none",
            )

        console.print(table)
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
        short = checksum[:16]
        console.print(f"[dim]Checksum: {short}...[/dim]")

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
