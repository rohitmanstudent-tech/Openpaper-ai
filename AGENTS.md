## Goal
Build production-ready open-source enterprise AI agent management platform with multi-agent orchestration, provider-agnostic LLM routing, and premium dark UI.

## Constraints & Preferences
- **Monorepo**: `apps/web` (Next.js 15 + Shadcn UI + Zustand), `apps/api` (FastAPI async), `packages/shared` (TS types)
- **Providers**: OpenAI, Anthropic Claude, Ollama (local), OpenRouter
- **4 Specialist Agents**: CEO (delegation), Sales (lead gen), Research (market intel), Buyer Finder (export)
- **Dark theme**: black (#000) → graphite → white, muted blue accent
- **Desktop-first** with collapsible sidebar + mobile backdrop overlay

## v0.1 Milestone — Complete

### Backend (31 API routes)
- **Auth** `POST /auth/register`, `POST /auth/login`, `POST /auth/refresh`, `POST /auth/revoke`, `GET /auth/me` — JWT + bcrypt, refresh token rotation, 4 RBAC roles
- **Agents** `CRUD + POST /{id}/execute + POST /{id}/delegate` — full lifecycle with SSE streaming
- **Chat** `CRUD + POST /{id}/completions` — SSE streaming with provider routing via agent config
- **Tasks** `CRUD` — status tracking (pending→in_progress→completed/failed), priority levels, result storage
- **Providers** `GET /providers, GET /providers/models` — health checks, model listing per provider
- **Models** `GET /models` — aggregate model list across all providers

### Agents Layer
- **BaseAgent** — ABC with `process()` and `process_stream()`, provider-agnostic, uses `get_provider()`
- **CEO Agent** — strategic leader, task delegation protocol, high-level decision synthesis
- **Sales Agent** — BANT lead qualification, proposal creation, pipeline management
- **Research Agent** — TAM/SAM/SOM market analysis, competitive SWOT, trend intelligence
- **Buyer Finder Agent** — BANT+ framework (Budget, Authority, Need, Timeline, Geography, Volume, Compliance), export trade specialization, lead scoring (Hot/Warm/Cold/Nurture)
- **AgentOrchestrator** — singleton that instantiates and routes to agents by `AgentType`

### Database
- **5 tables**: `users`, `agents`, `chats`, `chat_messages`, `tasks` — all with proper FK constraints, enums, timestamps
- **Alembic migration** `001_initial.py` — full async-compatible migration chain
- **Schema**: `userrole`, `agenttype`, `agentstatus`, `messagerole`, `taskstatus`, `taskpriority` enums

### Frontend (7 pages)
- **Auth** — Login + Register with error handling
- **Dashboard** — 4 stat cards (Agents, Chats, Active Tasks, Providers), recent agents/chats/tasks, agent type breakdown
- **Agents** — Card grid + create form, inline status toggle, delete
- **Chat** — 3-panel (chat list + messages + agent context), SSE streaming with typing indicator
- **Tasks** — Full list with status toggle, priority badges, agent assignment, inline execute
- **Providers** — Health status grid with model counts
- **Settings** — Profile view + sign out

### Frontend Architecture
- **4 Zustand stores**: auth, agents, chat, providers, tasks
- **4 UI components**: button (4 variants/3 sizes), input, card, skeleton
- **Collapsible sidebar** with 6 nav items + mobile backdrop overlay
- **Shared types** in `@repo/shared` (User, Agent, Chat, ChatMessage, ProviderStatus, AuthResponse, Task)

## Security Hardening (Module 8)

### API Security
- **Rate limiting** — sliding window (in-memory fallback + Redis backend), configurable per-endpoint limits, strict routes for auth (login: 10/min, register: 5/min, refresh: 10/min)
- **IP throttling** — per-IP tracking via client host, automatic cleanup of expired windows
- **Brute-force protection** — strict rate limits on auth endpoints, `Retry-After` headers
- **JWT validation** — HS256 signing, expiry checking, `raise from None` for clean error chain
- **Refresh token rotation** — SHA-256 hashed tokens stored in `refresh_tokens` table, rotation revokes old + issues new on each `/refresh`, explicit `/revoke` endpoint, 7-day expiry

### Web Security
- **CSP headers** — production-only `Content-Security-Policy` restricting scripts, styles, connects, frames
- **HSTS** — `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- **X-Frame-Options** — `DENY` (all responses)
- **X-Content-Type-Options** — `nosniff` (all responses)
- **X-XSS-Protection** — `1; mode=block`, `Referrer-Policy`, `Permissions-Policy`
- **CORS** — configurable via `CORS_ORIGINS` env var (comma-separated)

### Input Security
- **String sanitization** — control character stripping, length limiting
- **Prompt injection protection** — 10 regex patterns detecting `ignore previous instructions`, `jailbreak`, `roleplay`, `system prompt leak` attempts
- **File upload validation** — extension whitelist (14 types), 10 MB size limit
- **XSS protection** — HTML special character escaping (`sanitize_html()`)
- **SQL injection** — prevented by SQLAlchemy ORM parameterized queries

### AI Security
- **Provider key encryption** — Fernet symmetric encryption (`cryptography` package), configurable `ENCRYPTION_KEY` env var, ephemeral key fallback
- **Secret management** — all secrets via environment variables (Pydantic settings), validator warns on defaults
- **Agent permission boundaries** — RBAC via `require_permission()` decorator (4 roles, 7 permissions)
- **Error monitoring** — Sentry (optional) with FastAPI + Logging + SQLAlchemy integrations

### Error Handling
- **16 typed exception classes** — `AppError` → `AuthError`, `TokenExpiredError`, `PermissionDeniedError`, `NotFoundError`, `ValidationError`, `ConflictError`, `DatabaseError`, `ProviderError`, `ProviderTimeoutError`, `ProviderUnavailableError`, `ProviderAuthError`, `AgentError`, `AgentNotFoundError`, `OllamaError`, `RateLimitError`
- **Structured JSON responses** — all errors return `{success, error_code, message, request_id, details}`
- **ExceptionMiddleware** — catches exceptions from route handlers AND dependencies, returns consistent format
- **Custom 404 handler** — Starlette's default `{"detail": "Not Found"}` overridden to structured JSON

### Tests (41 total — 6 health + 27 security + 8 validator)
- Encryption roundtrip, different outputs, invalid ciphertext
- String sanitization (control chars, truncation)
- 7 prompt injection patterns detected, 3 clean inputs pass
- XSS escaping, file upload validation (extension, size)
- Security headers present (XCTO, XFO, XSS-Protection)
- Rate limit triggers at threshold, returns structured error
- 404 returns structured JSON, auth errors return structured JSON

## Key Files
| Layer | Path | Purpose |
|-------|------|---------|
| App | `apps/api/app/main.py` | FastAPI lifespan, CORS, 7 routers |
| Agents | `apps/api/app/agents/orchestrator.py` | Agent routing + lifecycle |
| Agents | `apps/api/app/agents/ceo.py` | CEO system prompt + delegation |
| Agents | `apps/api/app/agents/sales.py` | Sales lead gen workflows |
| Agents | `apps/api/app/agents/research.py` | Market research capabilities |
| Agents | `apps/api/app/agents/buyer_finder.py` | Export buyer qualification |
| Models | `apps/api/app/models/task.py` | Task ORM with FK chain |
| Migrations | `apps/api/alembic/versions/001_initial.py` | Full schema DDL |
| API | `apps/api/app/api/agents.py` | Agent CRUD + execute/delegate |
| API | `apps/api/app/api/tasks.py` | Task CRUD |
| API | `apps/api/app/api/chat.py` | Chat + SSE streaming |
| Security | `apps/api/app/core/encryption.py` | Fernet provider key encryption |
| Security | `apps/api/app/core/rate_limiter.py` | Sliding window rate limiter (memory + Redis) |
| Security | `apps/api/app/core/security_middleware.py` | CSP, HSTS, XFO, XCTO headers |
| Security | `apps/api/app/core/input_sanitizer.py` | String sanitization + prompt injection detection |
| Security | `apps/api/app/core/error_middleware.py` | ExceptionMiddleware + RequestIDMiddleware + structured errors |
| Security | `apps/api/app/core/exceptions.py` | 16 typed exception classes |
| Security | `apps/api/app/core/sentry.py` | Sentry (optional) with FastAPI integration |
| Security | `apps/api/app/models/refresh_token.py` | Refresh token ORM model |
| Security | `apps/api/alembic/versions/002_refresh_tokens.py` | Refresh token migration |
| Frontend | `apps/web/src/stores/tasks.ts` | Task Zustand store |
| Frontend | `apps/web/src/app/(dashboard)/tasks/page.tsx` | Tasks UI |
| Frontend | `apps/web/src/components/layout/sidebar.tsx` | Nav with Tasks |

## Sprint 2 — Knowledge Base System — Complete

### Backend (8 new document API routes in `app/api/documents.py`)
- `POST /api/v1/documents/upload` — file upload with text extraction (PDF/DOCX/XLSX/TXT/MD), langchain chunking, embedding, Qdrant storage
- `GET /api/v1/documents` — list all documents for current user with metadata
- `GET /api/v1/documents/{id}` — single document metadata
- `DELETE /api/v1/documents/{id}` — delete document + all chunk points
- `GET /api/v1/documents/{id}/chunks` — scroll through chunk points
- `POST /api/v1/documents/search` — semantic search across documents with score threshold
- `GET /api/v1/documents/collections` — list Qdrant collections
- `POST /api/v1/documents/collections/create` — create new collection

### Frontend (3 new pages + 4 components + 3 stores)
- **Knowledge Base** (`/knowledge`) — collection management (create/delete), document upload dropzone
- **Documents** (`/documents`) — file upload (drag-and-drop), card grid with metadata, inline delete, semantic search panel
- **Document Detail** (`/documents/[id]`) — metadata panel + chunk viewer with expand/collapse
- **Memory Explorer** (`/memory`) — recall & search modes over agent memories, memory type badges, delete
- **4 components**: DropZone (drag-and-drop upload w/ progress), ChunkViewer (scrollable expandable chunks), SemanticSearch (query + relevance scores), CitationCard (quote display w/ score)
- **3 stores**: `documents.ts`, `knowledge.ts`, `memory.ts`
- **API enhancement**: added `upload()` method to `api.ts` for multipart form data

### Dependencies
- `python-docx` installed in backend for DOCX text extraction

## Sprint 3 — Workflow Builder — Complete

### Backend (9 new API routes + engine + migration)
**Model & Migrations:**
- `app/models/workflow.py` — `Workflow` (JSON nodes/edges, status, owner) and `WorkflowRun` (status, input/output, logs, error) SQLAlchemy models
- `alembic/versions/003_workflows.py` — creates `workflows` + `workflow_runs` tables with proper indexes, enums, and FKs

**Workflow Engine** (`app/core/workflow_engine.py`):
- Topological sort (Kahn's algorithm) for DAG execution order
- 8 node executors: `trigger`, `agent` (CEO/Sales/Research/BuyerFinder), `knowledge_search` (Qdrant vector search), `condition` (field comparison with 8 operators), `delay` (async sleep), `http_request` (httpx), `email_sender`, `memory_store`
- Condition branching — follows `true`/`false` edge handles, skips nodes on unsatisfied conditions
- Full execution logging with per-node status/result/error capture
- Integration with `AgentOrchestrator`, `get_memory_engine()`, `get_bus()`, and `vector_search()`

**API Routes** (`app/api/workflows.py`):
| Method | Path | Description |
|--------|------|-------------|
| GET | `/workflows` | List all workflows for user |
| POST | `/workflows` | Create workflow |
| GET | `/workflows/{id}` | Get workflow detail |
| PUT | `/workflows/{id}` | Update workflow (nodes, edges, status) |
| DELETE | `/workflows/{id}` | Delete workflow + cascade runs |
| POST | `/workflows/{id}/execute` | Execute workflow, create run |
| GET | `/workflows/{id}/runs` | List runs for a workflow |
| GET | `/workflows/runs` | List all runs across workflows |
| GET | `/workflows/runs/{id}` | Get run detail with logs |
| POST | `/workflows/runs/{id}/cancel` | Cancel a running workflow |

### Frontend (3 new pages + 3 components + 1 store)
- **Workflows** (`/workflows`) — card grid with status badges, create dialog (name + description), inline execute + delete
- **Workflow Editor** (`/workflows/[id]`) — React Flow canvas with 8 custom node types, draggable node panel, MiniMap, Controls, Save/Execute toolbar, drag-and-drop from panel to canvas
- **Workflow Runs** (`/workflows/runs`) — run history with status badges, View Logs dialog with per-node expandable JSON preview, cancel running runs
- **3 components**: `canvas.tsx` (React Flow wrapper + ReactFlowProvider), `nodes.tsx` (8 custom node components with handles + condition handles), `node-panel.tsx` (draggable node palette)
- **1 store**: `workflows.ts` — full CRUD + execute + runs + cancel
- **Dependencies**: `@xyflow/react` (React Flow v12) installed

### Node Types (8)
| Type | Icon | Handles | Description |
|------|------|---------|-------------|
| Trigger | Zap (emerald) | 1 source | Starts execution |
| Agent | Bot (accent) | 1 target, 1 source | CEO/Sales/Research/BuyerFinder |
| Knowledge Search | Search (cyan) | 1 target, 1 source | Qdrant semantic search |
| Condition | GitBranch (amber) | 1 target, 3 sources | `true`/`false` branch handles |
| Delay | Clock (purple) | 1 target, 1 source | Async wait |
| HTTP Request | Globe (blue) | 1 target, 1 source | External API call |
| Email | Mail (rose) | 1 target, 1 source | Notification |
| Memory Store | Brain (violet) | 1 target, 1 source | Store in agent memory |

## Sprint 4 — Agent Graph — Complete

### Backend (5 new endpoints in `app/api/agent_graph.py`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/agent-graph` | Full graph state (nodes, edges, events, memory count) |
| GET | `/agent-graph/agents` | Agent list with status, type, provider |
| GET | `/agent-graph/events` | Event history with optional type filter |
| GET | `/agent-graph/events/stream` | SSE endpoint for live event streaming |
| GET | `/agent-graph/delegations` | Delegation chain history |
| GET | `/agent-graph/memory-links` | Memory relationships with count |

### Frontend (2 new pages + 1 store)
- **Agent Graph** (`/agent-graph`) — React Flow visualization with agent nodes (status-colored indicators), animated edges for communication, KPI cards (Agents/Connections/Events/Memories), recent event panel, memory links display
- **Live Agent Graph** (`/agent-graph/live`) — Polling-based live event stream (3s interval), event type counter grid, timestamped event feed with source→target arrows and correlation IDs, connection status indicator
- **Store**: `agent-graph.ts` — graph state, events, delegations, memory links

### Data Sources
- **Event Bus** (`get_bus().get_history()`) — all agent events, delegations, task lifecycle
- **Agents DB** — agent metadata, status, type
- **Memory Engine** — memory counts for memory links display
- **Qdrant** — event history persistence and memory storage

## Sprint 5 — Analytics — Complete

### Backend (7 new endpoints in `app/api/analytics.py`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/analytics/providers` | 8 provider health + model counts (OpenAI, Claude, Gemini, DeepSeek, Grok, OpenRouter, Ollama, NVIDIA NIM) |
| GET | `/analytics/costs` | Cost estimates per provider/agent/workflow (daily/weekly/monthly) |
| GET | `/analytics/agents` | Agent stats: tasks completed/failed, delegations, messages, total events |
| GET | `/analytics/workflows` | Workflow runs: total/success/failed, avg duration, per-workflow breakdown |
| GET | `/analytics/memory` | Memory breakdown: total, long-term, short-term, shared, agent personal |
| GET | `/analytics/documents` | Document stats: uploads, chunks, searches, top referenced documents |
| GET | `/analytics/system` | System health: all checks from `deep_check()` + Event Bus + API |

### Frontend (5 new pages + 1 store)
- **Analytics Dashboard** (`/analytics`) — 6 KPI cards (Providers, Agents, Workflows, Total Runs, Memory, Documents) linking to detail pages, Provider Status grid, Workflow Performance panel, Memory Breakdown, Documents & Chunks section, System Health grid with 15s auto-refresh
- **Provider Analytics** (`/analytics/providers`) — 8 provider cards with color-coded status + model counts
- **Agent Analytics** (`/analytics/agents`) — Per-agent cards with task completed/failed, delegation count, message count, type-colored badges
- **Workflow Analytics** (`/analytics/workflows`) — Summary KPI bar (total runs, success, failed, success rate) + per-workflow run stats table
- **Cost Analytics** (`/analytics/costs`) — Daily/weekly/monthly estimates, provider rate card grid (input/output per 1K tokens)
- **Store**: `analytics.ts` — all 7 data categories with batch fetch

## Sprint 6 — Marketplace — Complete

### Backend (6 new endpoints in `app/api/marketplace.py`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/marketplace` | List catalog items with search, category, featured/trending/recent filters |
| GET | `/marketplace/{item_id}` | Get single marketplace item detail |
| GET | `/marketplace/installed/list` | List all installed items for current user |
| POST | `/marketplace/install` | Install an item with dependency checking + plugin registry integration |
| POST | `/marketplace/{item_id}/uninstall` | Uninstall item, remove from plugin registry |
| POST | `/marketplace/{item_id}/update` | Update item to latest version |

### Built-in Catalog (21 entries)
- **7 Agents**: Export, Sales, Research, SEO, LinkedIn, Email Outreach, Customer Support
- **4 Workflows**: Lead Generation, Export Buyer Discovery, Sales Outreach, Content Creation
- **5 Tools**: Web Scraper, CSV/Excel Exporter, PDF Generator, Slack Notifier, Data Analyzer
- **5 Providers**: DeepSeek, Grok, NVIDIA NIM, Gemini, OpenRouter

### SQL Model & Migration
- **`app/models/marketplace.py`** — `InstalledMarketplaceItem` with `item_id`, `name`, `item_type` (enum: agent/workflow/tool/provider), `version`, `status` (enum: not_installed/installing/installed/update_available/error/uninstalled), permissions, dependencies, config, user FK
- **`alembic/versions/004_marketplace.py`** — creates `marketplace_installs` table with unique constraint on (item_id, user_id), proper indexes, and both enums

### Schemas (`app/schemas/marketplace.py`)
- `MarketplaceItemResponse` — full item detail with install_status
- `MarketplaceListResponse` — paginated list with categories
- `InstallRequest` / `InstallResponse` — install/uninstall/update payloads
- `InstalledItemResponse` — persisted install record

### Frontend (6 new pages + 1 store)
- **Marketplace Home** (`/marketplace`) — 4 category cards, featured items grid (top-rated), global search, browse buttons
- **Agent Marketplace** (`/marketplace/agents`) — agent cards with search, install/uninstall/update actions, status badges
- **Workflow Marketplace** (`/marketplace/workflows`) — workflow cards with same action pattern
- **Tool Marketplace** (`/marketplace/tools`) — tool cards with same action pattern
- **Provider Marketplace** (`/marketplace/providers`) — provider cards with same action pattern
- **Marketplace Detail** (`/marketplace/[id]`) — full item view with permissions, dependencies, info panels, README display, install/uninstall/update buttons
- **Store**: `marketplace.ts` — Zustand with persist middleware for installed items + active category

### Security Integration
- Install calls `plugin_registry` to register plugin with `PluginManifest` for sandbox + permission enforcement
- Uninstall removes from plugin registry
- Dependency checking before install — fails with clear error if unmet

## Phase 7 — OpenPaper Hub — Complete

### Overview
Built a complete package registry system (npm/pip-like) with remote registry API, CLI tool, dependency resolution, version locking, signature verification, trust system, and marketplace sync.

### Remote Registry Backend (14 new endpoints in `app/api/hub_registry.py`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hub/packages` | Search registry with query, type filter, sort, pagination |
| GET | `/hub/packages/{id}` | Package detail with all versions, ratings, metadata |
| POST | `/hub/packages` | Publish new package or new version |
| DELETE | `/hub/packages/{id}` | Unpublish package (publisher only) |
| GET | `/hub/packages/{id}/resolve` | Resolve package with dependency chain for install |
| POST | `/hub/packages/{id}/ratings` | Rate package (1-5) with optional review |
| POST | `/hub/sync` | Sync remote registry packages → local marketplace |
| GET | `/hub/sync/status` | Recent sync history (last 5) |
| GET | `/hub/stats` | Registry statistics (total, by type, verified publishers) |
| POST | `/hub/keys` | Register publisher signing key |
| DELETE | `/hub/keys/{id}` | Revoke publisher signing key |

### SQL Models & Migration (`005_hub_registry.py`)
- **`RegistryPackage`** — package metadata with `package_id`, `name`, `package_type` (agent/workflow/tool/provider), `visibility` (public/private/organization), `current_version`, `downloads`, `rating_sum`/`rating_count`, `verified_publisher`, `tags`, `homepage`, `repository`, `readme`, `publisher_id` FK
- **`RegistryPackageVersion`** — per-version data with `manifest` JSON, `signature`, `signature_key_id`, `checksum_sha256`, `content_hash`, `dependencies`, `changelog`
- **`RegistryRating`** — user ratings (1-5) with optional review
- **`RegistrySyncLog`** — sync audit trail
- **`PublisherKey`** — Ed25519 public keys for signature verification

### Dependency Resolution (`app/core/hub_resolver.py`)
- **Semver parsing** — `Version` class with full comparison operators (`<`, `<=`, `==`, `!=`, `>=`, `>`, `^`, `~=`)
- **Constraint matching** — `satisfies()`, `find_best_match()` for version resolution
- **Dependency graph** — `DependencyGraph` with topological sort (Kahn's algorithm) and cycle detection
- **Lockfile** — `Lockfile`/`LockEntry` classes for version locking with JSON serialization

### Signature Verification (`app/core/hub_signer.py`)
- Ed25519 key pair generation via PyNaCl
- Canonical JSON signing with `sign_manifest()`
- `verify_signature()` for install-time verification
- SHA-256 checksums for package integrity
- Graceful fallback when PyNaCl is not installed

### CLI Tool (`apps/cli/`)

```bash
openpaper search export              # Search registry
openpaper install export-agent       # Install with dep resolution
openpaper install sales-agent@1.1.0  # Install specific version
openpaper publish ./my-agent/        # Publish from manifest
openpaper unpublish my-agent         # Remove from registry
openpaper login                      # Authenticate
openpaper logout                     # Clear auth
openpaper whoami                     # Show current user
```

**6 commands:**
- `search` — rich table output, filter by type, sort, pagination, `--stats` for registry overview
- `install` — resolves dependency chain, shows permissions, generates `openpaper.lock`, `--dry-run` preview
- `publish` — auto-discovers `openpaper.json/yaml`/`plugin.json/yaml`, validates manifest, supports `--sign` with Ed25519, `--dry-run` validation
- `unpublish` — confirms before removing, requires authentication
- `login`/`logout`/`whoami` — auth token management via `~/.config/openpaper/auth.json`

### Frontend Integration
- **Marketplace store** — added `syncWithHub()` and `getSyncStatus()` methods
- **Marketplace page** — "Sync with Hub" button and "Hub Status" info button added to header
- Backward compatible — all existing marketplace pages unchanged

### Key Files Created

| Layer | Path | Purpose |
|-------|------|---------|
| Backend | `apps/api/app/models/hub_registry.py` | 5 new SQLAlchemy models |
| Backend | `apps/api/app/schemas/hub_registry.py` | 10 Pydantic schemas |
| Backend | `apps/api/app/api/hub_registry.py` | 14 registry API endpoints |
| Backend | `apps/api/app/core/hub_resolver.py` | Semver parsing, dependency graph, lockfile |
| Backend | `apps/api/app/core/hub_signer.py` | Ed25519 signing & verification |
| Backend | `apps/api/app/core/security.py` | Added `get_current_user_optional` |
| Migration | `apps/api/alembic/versions/005_hub_registry.py` | 5 new tables |
| CLI | `apps/cli/pyproject.toml` | Entry point: `openpaper` |
| CLI | `apps/cli/openpaper/cli.py` | Main CLI group |
| CLI | `apps/cli/openpaper/commands/search.py` | Search command |
| CLI | `apps/cli/openpaper/commands/install.py` | Install + resolve + lockfile |
| CLI | `apps/cli/openpaper/commands/publish.py` | Publish with manifest discovery |
| CLI | `apps/cli/openpaper/commands/unpublish.py` | Unpublish with confirmation |
| CLI | `apps/cli/openpaper/commands/login.py` | Auth (login/logout/whoami) |
| CLI | `apps/cli/openpaper/registry.py` | HTTP client for hub API |
| CLI | `apps/cli/openpaper/hub_signer.py` | CLI-side signing |
| Frontend | `apps/web/src/stores/marketplace.ts` | Added sync methods |
| Frontend | `apps/web/src/app/(dashboard)/marketplace/page.tsx` | Added sync UI |

## Next Steps
1. Run `docker compose up -d` (postgres + redis + qdrant), then `alembic upgrade head`
2. Install CLI: `cd apps/cli && pip install -e .`
3. Start backend: `cd apps/api && uvicorn app.main:app --reload`
4. Start frontend: `cd apps/web && npm run dev`
5. Test CLI: `openpaper search`, `openpaper install export-agent`, `openpaper publish`
6. Test sync: click "Sync with Hub" on `/marketplace`
7. Module 6: Structured logging (JSON log formatter, correlation ID injection, request audit middleware)
8. Module 7: Backup & restore (pg_dump scripts, S3 upload, Redis RDB backup)
9. Module 9: Production deployment documentation (architecture diagram, scaling guide, runbook)
