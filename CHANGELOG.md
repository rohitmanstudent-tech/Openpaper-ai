# Changelog

All notable changes to OpenPaper AI are documented here.

## v1.0.0-rc.1 (2026-06-23)

### Added
- **Marketplace** — discover, install, update agents/workflows/tools/providers from built-in catalog (21 items)
- **OpenPaper Hub** — remote package registry with search, publish, unpublish, version management
- **CLI Tool** — `openpaper` with 16 commands (onboard, run, doctor, configure, agents, models, dashboard, update, plugins, search, install, publish, unpublish, login, logout, whoami)
- **Registry API** — 14 endpoints for package management, dependency resolution, signature verification
- **Dependency Resolution** — semver constraint parsing, topological sort, lockfile generation
- **Signature Verification** — Ed25519 signing for package authenticity
- **Hub Sync** — one-click sync between remote registry and local marketplace
- **Structured Logging** — JSON log formatter, correlation ID injection, request tracing
- **Backup & Restore** — scripts for PostgreSQL, Redis, Qdrant with one-click restore
- **Performance Benchmarks** — API latency, workflow execution, provider routing scripts
- **Security Audit** — dependency scan, secret scan, API security review documentation
- **Docker Integration CI** — GitHub Actions workflow validating compose up, health checks, API, frontend

### Analytics (Sprint 5)
- 7 analytics endpoints (providers, costs, agents, workflows, memory, documents, system health)
- 5 dashboard pages with 15s auto-refresh system health

### Agent Graph (Sprint 4)
- 6 endpoints including SSE streaming for live agent events
- 2 frontend pages with React Flow visualization

### Workflow Builder (Sprint 3)
- 10 API routes, DAG execution engine with 8 node types
- React Flow editor with drag-and-drop workflow design

### Knowledge Base (Sprint 2)
- 8 document API endpoints with PDF/DOCX/XLSX extraction
- Qdrant vector storage with semantic search

### Core Platform (Sprint 1)
- Multi-agent orchestration (CEO, Sales, Research, Buyer Finder)
- Provider-agnostic LLM routing (OpenAI, Anthropic, Ollama, OpenRouter, DeepSeek, Grok, Gemini, NVIDIA NIM)
- JWT auth with refresh token rotation
- Rate limiting, CSP/HSTS/XFO security headers
- 16 typed exception classes with structured JSON error responses
- 15 shadcn UI components, 10 Zustand stores
- 31 frontend pages with dark theme

### Security
- Fernet encryption for provider API keys
- Prompt injection protection (10 regex patterns)
- RBAC with 4 roles and 7 permissions
- Input sanitization and XSS prevention
- Container security with non-root user in Docker

### Packaging & Build
- Backend pip-installable with proper pyproject.toml (setuptools, 15 dependencies, dev extras)
- Wheel and source distribution builds
- 308 passing tests (9 skipped, 0 failures)
- Missing package __init__.py files created (app, api, core)
- CLI packages merged into single `openpaper` command (enterprise + hub commands)
- Frontend builds with 31/31 static pages, 103 kB shared bundle
- Ruff lint: 389 auto-fixable errors resolved (295 cosmetic remain)

## v0.1.0 (2026-05-01)

### Added
- Initial project structure with monorepo (Next.js 15 + FastAPI + shared types)
- Agent system with 4 specialist agents
- Provider integrations (OpenAI, Anthropic, Ollama, OpenRouter)
- JWT authentication with refresh tokens
- Chat with SSE streaming
- Task management with priority levels
- Health check endpoints
