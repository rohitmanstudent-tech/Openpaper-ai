# OpenPaper AI — Marketplace Guide

The OpenPaper Marketplace is a built-in catalog of agents, workflows, tools, and
providers. The Hub sync feature extends this with remote package discovery.

## Browsing the Marketplace

Navigate to `/marketplace` in the dashboard:

1. **Home** — Category cards (Agents, Workflows, Tools, Providers) + Featured items
2. **Agents** — AI agents for specialized tasks
3. **Workflows** — Pre-built automation pipelines
4. **Tools** — Utility integrations (Slack, PDF, etc.)
5. **Providers** — AI model providers (DeepSeek, Grok, etc.)

## Installing Items

From any listing page or detail page:

1. Click **Install** on a card or item detail
2. Review permissions requested
3. Confirm installation

The item is registered in the Plugin Registry for sandbox and permission enforcement.

## Syncing with Hub

The Hub is a remote package registry (npm/pip-like) for community packages.

1. Go to `/marketplace`
2. Click **Sync with Hub**
3. Remote packages are imported into your local marketplace

## Publishing to Hub (CLI)

```bash
# Authenticate
openpaper login

# Publish your package
openpaper publish ./my-agent/

# Verify it appears in search
openpaper search my-agent
```

See the [CLI Guide](cli.md) for detailed publish instructions.

## Trust System

- **Verified publishers** — identity-verified accounts (shown with badge)
- **Downloads** — package popularity indicator
- **Ratings** — 1–5 star rating with reviews
- **Signature verification** — Ed25519 signed packages show verified badge

## Built-in Catalog (21 Items)

### Agents
| Package | Description |
|---------|-------------|
| Export Agent | Export trade operations & buyer discovery |
| Sales Agent | Lead qualification & pipeline management |
| Research Agent | Market research & competitive intelligence |
| SEO Agent | Search optimization & keyword research |
| LinkedIn Agent | Profile optimization & lead generation |
| Email Outreach Agent | Campaign management & personalization |
| Customer Support Agent | Ticket triage & response generation |

### Workflows
| Package | Description |
|---------|-------------|
| Lead Generation | Research → Buyer Finder → Sales Outreach → CRM |
| Export Buyer Discovery | Market Analysis → Buyer Finder → Qualification |
| Sales Outreach | Lead Qualification → Email Campaign → Follow-up |
| Content Creation | Research → Outline → Draft → Review → Publish |

### Tools
| Package | Description |
|---------|-------------|
| Web Scraper | Extract data with CSS selectors |
| CSV/Excel Exporter | Export to CSV/Excel/JSON |
| PDF Generator | Generate PDF reports from templates |
| Slack Notifier | Send notifications to Slack |
| Data Analyzer | Statistical analysis & anomaly detection |

### Providers
| Package | Description |
|---------|-------------|
| DeepSeek | DeepSeek AI chat & embedding models |
| Grok | xAI Grok chat completions |
| NVIDIA NIM | Accelerated GPU inference |
| Gemini | Google multimodal AI |
| OpenRouter | Unified 100+ model access |
