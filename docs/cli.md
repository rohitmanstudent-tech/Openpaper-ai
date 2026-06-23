# OpenPaper AI — CLI Guide

The `openpaper` CLI provides package registry access and management for the OpenPaper Hub.

## Installation

```bash
cd apps/cli
pip install -e .
```

Verify installation:

```bash
openpaper --version
openpaper --help
```

## Authentication

```bash
# Log in to the registry
openpaper login

# Log in with credentials
openpaper login --email user@example.com

# Create a new account
openpaper login --register --username myname

# Check current user
openpaper whoami

# Log out
openpaper logout
```

Credentials are stored securely at `~/.config/openpaper/auth.json`.

## Searching Packages

```bash
# Search all packages
openpaper search

# Search by keyword
openpaper search export
openpaper search sales
openpaper search workflow

# Filter by type
openpaper search --type agent
openpaper search --type workflow
openpaper search --type tool
openpaper search --type provider

# Sort results
openpaper search --sort downloads
openpaper search --sort rating
openpaper search --sort name

# View registry statistics
openpaper search --stats
```

## Installing Packages

```bash
# Install latest version
openpaper install export-agent
openpaper install sales-agent
openpaper install workflow-uae-buyers

# Install specific version
openpaper install export-agent@1.0.0

# Install with version constraint
openpaper install sales-agent@^1.0.0

# Preview installation (dry run)
openpaper install export-agent --dry-run

# Skip dependency installation
openpaper install export-agent --no-deps

# Save to lockfile
openpaper install export-agent --save
```

The install command:
- Resolves the package and all dependencies
- Shows permissions required
- Generates an `openpaper.lock` file (with `--save`)
- Displays signature verification status

## Publishing Packages

```bash
# Publish from current directory
openpaper publish

# Publish from specific directory
openpaper publish ./my-agent/

# Dry run (validate manifest only)
openpaper publish --dry-run

# Sign the package (requires PyNaCl)
openpaper publish --sign --key-id mykey --private-key ./key.pem

# Set visibility
openpaper publish --visibility private
```

The publish command auto-discovers:
- `openpaper.json` or `openpaper.yaml` (preferred)
- `plugin.json` or `plugin.yaml` (legacy)
- `README.md` (auto-included)
- `CHANGELOG.md` (auto-included)
- `plugin.py` (entrypoint)

### Manifest Format (openpaper.json)

```json
{
  "name": "my-export-agent",
  "version": "1.0.0",
  "description": "Export trade automation agent",
  "package_type": "agent",
  "author": "Your Name",
  "entrypoint": "plugin.py",
  "dependencies": [],
  "permissions": [
    "memory:read",
    "memory:write",
    "agent:execute"
  ],
  "tags": ["export", "trade", "automation"],
  "homepage": "https://github.com/you/my-agent",
  "readme": "# My Export Agent\n\n..."
}
```

## Unpublishing Packages

```bash
# Unpublish (with confirmation)
openpaper unpublish my-agent

# Force unpublish (skip confirmation)
openpaper unpublish my-agent --force
```

Only the original publisher can unpublish a package.

## Signing Keys

Generate a signing key pair:

```bash
pip install pynacl
python3 -c "
from nacl.signing import SigningKey
from nacl.encoding import HexEncoder
sk = SigningKey.generate()
print('Private:', sk.encode(encoder=HexEncoder).decode())
print('Public: ', sk.verify_key.encode(encoder=HexEncoder).decode())
"
```

Register your public key in the Dashboard, then use `--sign --key-id <key_id> --private-key <path>` when publishing.

## Registry Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OPENPAPER_REGISTRY` | `https://hub.openpaper.ai/api/v1` | Registry API base URL |

## Troubleshooting

```bash
# Check authentication
openpaper whoami

# Test registry connectivity
openpaper search --stats

# Verbose errors from API
OPENPAPER_DEBUG=1 openpaper install export-agent
```
