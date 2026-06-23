# OpenPaper AI v1.0.0-rc.1

**Release Candidate 1** — Enterprise AI Agent Management Platform

> **Date:** 2026-06-23  
> **Version:** 1.0.0-rc.1  
> **License:** MIT

---

## Features

### Multi-Agent Orchestration
4 specialist agents with configurable LLM backends, task delegation protocol, and SSE streaming execution:

| Agent | Role |
|-------|------|
| **CEO Agent** | Strategic leader, task delegation, high-level synthesis |
| **Sales Agent** | BANT lead qualification, proposal creation, pipeline management |
| **Research Agent** | TAM/SAM/SOM market analysis, competitive SWOT, trend intelligence |
| **Buyer Finder Agent** | Export trade specialization, BANT+ framework, lead scoring (Hot/Warm/Cold/Nurture) |

### Provider-Agnostic LLM Routing
8 supported providers with unified API:

OpenAI · Anthropic Claude · Ollama (local) · OpenRouter · DeepSeek · Grok · Gemini · NVIDIA NIM

### Workflow Builder (Sprint 3)
Visual DAG workflow editor with 8 node types, topological execution engine, and real-time run monitoring:

Trigger → Agent → Knowledge Search → Condition → Delay → HTTP Request → Email → Memory Store

### Knowledge Base (Sprint 2)
Document ingestion with PDF/DOCX/XLSX/TXT/MD extraction, langchain chunking, Qdrant vector storage, and semantic search.

### Agent Graph (Sprint 4)
Real-time agent communication visualization with React Flow, SSE live event streaming, and delegation chain history.

### Analytics (Sprint 5)
7 analytics endpoints with 5 dashboard pages, cost estimation per provider/agent/workflow, and 15s auto-refresh system health.

### Marketplace (Sprint 6)
21 built-in catalog items (7 agents, 4 workflows, 5 tools, 5 providers) with one-click install/update/uninstall.

### OpenPaper Hub (Phase 7)
Remote package registry with 14 API endpoints, semver dependency resolution, Ed25519 signature verification, and CLI tooling.

### Enterprise CLI
16 commands in a single `openpaper` executable:

- **System:** `onboard`, `doctor`, `run`, `update`, `configure`
- **Management:** `agents`, `models`, `dashboard`, `plugins`
- **Hub Registry:** `search`, `install`, `publish`, `unpublish`, `login`, `logout`, `whoami`

### Security
- JWT auth with refresh token rotation
- Rate limiting (sliding window, per-endpoint)
- CSP/HSTS/XFO/XCTO security headers
- Fernet encryption for provider API keys
- Prompt injection protection (10 regex patterns)
- RBAC with 4 roles and 7 permissions
- Input sanitization and XSS prevention
- 16 typed exception classes

### Operations
- Structured JSON logging with correlation ID injection
- Backup/restore scripts (PostgreSQL pg_dump, Redis RDB, Qdrant snapshot)
- Performance benchmark suite (API latency, workflow execution, memory, provider routing)
- Security audit scripts (pip-audit, npm audit, trufflehog/gitleaks, trivy)
- Docker Compose production deployment with Traefik SSL

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                              │
│              Next.js 15 + Shadcn UI + Zustand               │
│              31 pages · Dark Theme · Collapsible Sidebar    │
└──────────────────┬──────────────────────────────────────────┘
                   │ HTTP/SSE
┌──────────────────▼──────────────────────────────────────────┐
│                    FastAPI (async)                          │
│  42 API endpoints · 16 routers · JWT auth · Rate limiting  │
│  Security headers · Request validation · Error middleware   │
└───────┬──────────────┬──────────────┬───────────────────────┘
        │              │              │
┌───────▼──────┐ ┌─────▼──────┐ ┌────▼──────────────────┐
│ PostgreSQL   │ │   Redis    │ │  Qdrant Vector Store   │
│ 8 tables     │ │ Session    │ │  Document embeddings   │
│ Alembic migr │ │ Cache      │ │  Semantic search       │
└──────────────┘ └────────────┘ └────────────────────────┘
```

### Data Flow
1. **Auth:** Browser → API → JWT → PostgreSQL (users, refresh_tokens)
2. **Agents:** Browser/API → AgentOrchestrator → LLM Provider → Response stream
3. **Chat:** Browser (SSE) → Chat API → Provider Router → Token stream
4. **Tasks:** Browser → Task API → PostgreSQL (tasks)
5. **Workflows:** Editor → Workflow Engine → Topological DAG → Per-node execution
6. **Documents:** Upload → Text extraction → LangChain chunking → Qdrant indexing
7. **Marketplace:** Browser → Marketplace API → Plugin Registry → Installed items
8. **Hub:** CLI/Browser → Hub Registry API → PostgreSQL (hub models) → Sync

### Container Architecture (Docker Compose)
```
openpaper-net
  ├── postgres:16-alpine (port 5432)
  ├── redis:7-alpine (port 6379)
  ├── api: FastAPI (port 8000)
  └── web: Next.js (port 3000)
```

---

## Installation Guide

### Option 1: Docker Compose (Production)

```bash
git clone https://github.com/openpaper-ai/openpaper.git
cd openpaper

# Configure secrets
export SECRET_KEY=$(openssl rand -hex 32)
export ENCRYPTION_KEY=$(openssl rand -hex 32)

# Start all services
docker compose up -d

# Verify
curl http://localhost:8000/api/health
```

### Option 2: Development Setup

**Backend:**
```bash
cd apps/api
pip install -e ".[dev]"
cp .env.example .env  # configure your API keys
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd apps/web
npm install
npm run dev
```

**CLI:**
```bash
cd openpaper_cli
pip install -e .
openpaper --help
```

### Option 3: CLI-Only

```bash
pip install openpaper-cli
openpaper doctor
openpaper models --list
openpaper search --stats
```

### Quick Start

```bash
# Run diagnostics
openpaper doctor

# Run the interactive onboarding wizard
openpaper onboard

# Start services
openpaper run

# Open the web dashboard
openpaper dashboard --open
```

---

## Screenshots References

| Page | Description |
|------|-------------|
| `/dashboard` | 4 KPI cards, recent agents/chats/tasks, agent type breakdown |
| `/agents` | Card grid with create form, inline status toggle, delete |
| `/chat` | 3-panel layout (chat list + messages + agent context), SSE streaming |
| `/tasks` | Full list with status toggle, priority badges, agent assignment |
| `/workflows` | Card grid with status badges, create dialog, inline execute |
| `/workflows/[id]` | React Flow canvas with 8 custom node types, MiniMap, Controls |
| `/workflows/runs` | Run history with status badges, expandable JSON log viewer |
| `/agent-graph` | React Flow agent visualization, KPI cards, event panel |
| `/agent-graph/live` | Polling-based live event stream with type counter grid |
| `/knowledge` | Collection management, document upload dropzone |
| `/documents` | Drag-and-drop upload, card grid, semantic search panel |
| `/marketplace` | Category cards, featured items grid, global search |
| `/marketplace/[id]` | Full item detail with permissions, dependencies, README |
| `/analytics` | 6 KPI cards, provider status grid, system health with 15s refresh |
| `/providers` | Health status grid with model counts |
| `/settings` | Profile view + sign out |

---

## Known Limitations

### Release Candidate
1. **Docker required for full deployment** — local development requires Docker for PostgreSQL/Redis/Qdrant
2. **Qdrant required for vector features** — Knowledge Base and semantic search depend on Qdrant
3. **Ollama recommended for local LLM** — cloud providers (OpenAI, Anthropic) require API keys
4. **Windows Docker limitation** — Docker Compose integration test requires Linux/macOS or Windows Docker Desktop
5. **Ruff lint warnings** — 295 cosmetic lint warnings remain (B008 function-call-default, E501 line-too-long, ARG unused-args)
6. **No production auth UI** — login/register pages are functional but minimal
7. **Single-region deployment** — no multi-region or HA configuration included
8. **No database migration rollback** — Alembic downgrade not tested for all migration paths

### Backlog
- Multi-tenancy
- OAuth/SSO integration
- Webhook triggers for workflows
- Mobile responsive layout
- Internationalization (i18n)
- Audit log export (CSV/JSON)
- Plugin SDK documentation

---

## Upgrade Notes

### From v0.1.0 to v1.0.0-rc.1

This is the first release candidate — there is no direct upgrade path from v0.1.0. A fresh deployment is required.

### Breaking Changes
- None — this is the first RC. Future RCs and the stable release will document migration paths.

### Pre-release Checklist
- [ ] Set `SECRET_KEY` and `ENCRYPTION_KEY` environment variables (required)
- [ ] Configure `CORS_ORIGINS` for your deployment domain
- [ ] Set LLM provider API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
- [ ] Ensure PostgreSQL 16+, Redis 7+, and Qdrant 1.9+ are available
- [ ] Run `alembic upgrade head` to initialize/migrate the database

---

## Test Report

| Suite | Status | Details |
|-------|--------|---------|
| Backend tests | ✅ 308 passed | 9 skipped (external services), 0 failures |
| Frontend build | ✅ 31/31 pages | Static generation, 103 kB shared bundle |
| CLI `--help` | ✅ 16 commands | All commands documented |
| CLI `doctor` | ✅ Full diagnostics | OS, Python, Ollama, GPU, ports |
| Docker build | ✅ API + Web | Multi-stage builds with health checks |
| Ruff lint | ⚠️ 295 remaining | Cosmetic (B008, E501, ARG) — non-blocking |

---

## Resources

- **Documentation:** [docs/](docs/) directory
- **Architecture:** [docs/architecture.md](docs/architecture.md)
- **Quickstart:** [docs/quickstart.md](docs/quickstart.md)
- **Docker Deployment:** [docs/docker.md](docs/docker.md)
- **CLI Reference:** [docs/cli.md](docs/cli.md)
- **Marketplace Guide:** [docs/marketplace.md](docs/marketplace.md)
- **Workflow Guide:** [docs/workflow.md](docs/workflow.md)
- **Changelog:** [CHANGELOG.md](CHANGELOG.md)
- **Security:** [SECURITY.md](SECURITY.md)
- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)

---

*OpenPaper AI — Enterprise AI Agent Management Platform*  
*MIT License · Built with Next.js, FastAPI, and ❤️*
