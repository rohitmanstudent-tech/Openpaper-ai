"""openpaper publish — publish packages to the remote registry."""

import os
import json
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console

from openpaper.registry import publish_package
from openpaper.config import get_token

console = Console()

MANIFEST_FILES = ["openpaper.json", "openpaper.yaml", "openpaper.yml", "plugin.json", "plugin.yaml", "plugin.yml"]


def _load_manifest(package_dir: str) -> dict | None:
    path = Path(package_dir)
    for filename in MANIFEST_FILES:
        manifest_path = path / filename
        if manifest_path.exists():
            raw = manifest_path.read_text(encoding="utf-8")
            if manifest_path.suffix in (".yaml", ".yml"):
                return yaml.safe_load(raw)
            else:
                return json.loads(raw)
    return None


def _discover_manifest_fields(package_dir: str) -> dict:
    fields = {}
    path = Path(package_dir)

    if (path / "plugin.py").exists():
        fields["entrypoint"] = "plugin.py"

    if (path / "README.md").exists():
        fields["readme"] = (path / "README.md").read_text(encoding="utf-8")

    if (path / "CHANGELOG.md").exists():
        fields["changelog"] = (path / "CHANGELOG.md").read_text(encoding="utf-8")

    return fields


@click.command(name="publish")
@click.argument("package_dir", required=False, default=".")
@click.option("-m", "--manifest", help="Path to manifest file (auto-discovered if in package_dir)")
@click.option("--visibility", default="public", help="Visibility: public, private")
@click.option("--sign", is_flag=True, help="Sign the package (requires signing key)")
@click.option("--key-id", help="Signing key ID (required with --sign)")
@click.option("--private-key", help="Path to private key file (required with --sign)")
@click.option("--dry-run", is_flag=True, help="Validate manifest without publishing")
def publish(package_dir: str, manifest: str, visibility: str, sign: bool, key_id: str, private_key: str, dry_run: bool):
    """Publish a package to the OpenPaper Hub registry.

    \b
    Examples:
        openpaper publish ./my-agent/
        openpaper publish --dry-run
        openpaper publish --sign --key-id mykey --private-key ./key.pem
    """
    if not get_token():
        console.print("[red]Not authenticated. Run 'openpaper login' first.[/red]")
        sys.exit(1)

    pkg_dir = Path(package_dir)
    if not pkg_dir.is_dir():
        console.print(f"[red]Directory not found: {package_dir}[/red]")
        sys.exit(1)

    manifest_data = None
    if manifest:
        m_path = Path(manifest)
        if m_path.exists():
            raw = m_path.read_text(encoding="utf-8")
            if m_path.suffix in (".yaml", ".yml"):
                manifest_data = yaml.safe_load(raw)
            else:
                manifest_data = json.loads(raw)
    else:
        manifest_data = _load_manifest(str(pkg_dir))

    if not manifest_data:
        console.print(f"[red]No manifest found in '{package_dir}'.[/red]")
        console.print("  Create an openpaper.json or openpaper.yaml with these fields:")
        console.print('  {"name": "my-agent", "version": "1.0.0", "package_type": "agent", "description": "..."}')
        sys.exit(1)

    discovered = _discover_manifest_fields(str(pkg_dir))
    if discovered.get("entrypoint") and not manifest_data.get("entrypoint"):
        manifest_data["entrypoint"] = discovered["entrypoint"]
    if discovered.get("readme") and not manifest_data.get("readme"):
        manifest_data["readme"] = discovered["readme"]

    required = ["name", "version", "package_type"]
    missing = [r for r in required if r not in manifest_data]
    if missing:
        console.print(f"[red]Missing required fields in manifest: {', '.join(missing)}[/red]")
        sys.exit(1)

    valid_types = ["agent", "workflow", "tool", "provider"]
    if manifest_data["package_type"] not in valid_types:
        console.print(f"[red]Invalid package_type '{manifest_data['package_type']}'. Must be one of: {', '.join(valid_types)}[/red]")
        sys.exit(1)

    console.print(f"\n[bold cyan]Publishing:[/bold cyan] {manifest_data['name']} v{manifest_data['version']}")
    console.print(f"  Type:        {manifest_data['package_type'].capitalize()}")
    console.print(f"  Visibility:  {visibility}")
    console.print(f"  Description: {manifest_data.get('description', '(none)')}")
    console.print(f"  Author:      {manifest_data.get('author', '(not set)')}")
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
            sys.exit(1)
        try:
            key_path = Path(private_key)
            key_data = key_path.read_text().strip()
            from openpaper.hub_signer import sign_manifest
            signature = sign_manifest(manifest_data, key_data)
            console.print("[green]✓ Package signed[/green]")
        except Exception as e:
            console.print(f"[red]Failed to sign package: {e}[/red]")
            console.print("  Install pynacl: pip install pynacl")
            sys.exit(1)

    if dry_run:
        console.print("\n[green]✓ Manifest validation passed (dry run)[/green]")
        return

    try:
        changelog = discovered.get("changelog", "")
        result = publish_package(
            manifest=manifest_data,
            changelog=changelog,
            signature=signature,
            signature_key_id=sig_key_id,
            visibility=visibility,
        )
    except Exception as e:
        console.print(f"[red]Publishing failed: {e}[/red]")
        if hasattr(e, "response") and hasattr(e.response, "text"):
            console.print(f"[dim]{e.response.text}[/dim]")
        sys.exit(1)

    if result.get("success"):
        pkg_id = result.get("package_id", manifest_data["name"])
        ver = result.get("version", manifest_data["version"])
        sig_ok = result.get("signature_verified", False)
        sig_text = " [green](signature verified)[/green]" if sig_ok else " [yellow](not signed)[/yellow]"
        console.print(f"\n[green]✓ Published '{pkg_id}' v{ver}{sig_text}[/green]")
    else:
        console.print(f"[red]Publishing failed: {result.get('message', 'unknown error')}[/red]")
        sys.exit(1)
