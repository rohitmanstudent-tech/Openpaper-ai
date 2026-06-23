"""openpaper search — search the remote registry."""

import click
from rich.console import Console
from rich.table import Table
from rich import box

from openpaper.registry import search_packages, get_registry_stats

console = Console()


@click.command(name="search")
@click.argument("query", required=False, default="")
@click.option("-t", "--type", "package_type", help="Filter by type: agent, workflow, tool, provider")
@click.option("--sort", default="downloads", help="Sort by: downloads, rating, name, created, updated")
@click.option("--page", default=1, type=int, help="Page number")
@click.option("--limit", default=20, type=int, help="Results per page")
@click.option("--stats", is_flag=True, help="Show registry stats instead of search")
def search(query: str, package_type: str, sort: str, page: int, limit: int, stats: bool):
    """Search the OpenPaper Hub registry for packages.

    \b
    Examples:
        openpaper search
        openpaper search export
        openpaper search sales --type agent
        openpaper search --stats
    """
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
            return

    try:
        data = search_packages(
            query=query,
            package_type=package_type,
            sort=sort,
            page=page,
            page_size=limit,
        )
    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")
        return

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
