# Architecture

> **OpenPaper AI** — System design, component relationships, and data flow.

## System Architecture

```mermaid
graph TB
    subgraph Client["Client Layer"]
        WEB["Next.js 15 App<br/>31 pages · Shadcn UI · Dark Theme<br/>Zustand stores · React Flow"]
        CLI["openpaper CLI<br/>16 commands · Typer · Rich"]
    end

    subgraph API["API Layer (FastAPI)"]
        direction TB
        GW["API Gateway<br/>42 endpoints · 16 routers"]
        MID["Middleware Stack<br/>CORS · Security Headers · Rate Limiting<br/>JWT Auth · Logging · Error Handler"]
        AUTH["Auth Service<br/>JWT · Refresh Rotation · RBAC"]
    end

    subgraph Core["Core Engine"]
        direction TB
        ORCH["Agent Orchestrator<br/>CEO · Sales · Research · Buyer Finder"]
        WF["Workflow Engine<br/>DAG · Kahn Topological Sort<br/>8 Node Types · Condition Branching"]
        MEM["Memory Engine<br/>Short/Long-term · Shared · Episodic"]
        BUS["Event Bus<br/>SSE Streaming · Pub/Sub"]
        PLUG["Plugin Registry<br/>Sandbox · Permission Enforcement"]
        HUB["Hub Registry<br/>Semver · Dependency Resolution<br/>Ed25519 Signatures · Lockfile"]
    end

    subgraph Data["Data Layer"]
        PG[("PostgreSQL 16<br/>8 Tables · Alembic Migrations")]
        RD[("Redis 7<br/>Cache · Sessions · Rate Limiter")]
        QD[("Qdrant<br/>Vector Store · Embeddings")]
    end

    subgraph LLM["LLM Providers"]
        OPENAI[OpenAI]
        ANTH[Anthropic Claude]
        OLLAMA[Ollama]
        OR[OpenRouter]
        DS[DeepSeek]
        GROK[Grok]
        GEM[Gemini]
        NIM[NVIDIA NIM]
    end

    subgraph Infra["Infrastructure"]
        DC["Docker Compose"]
        TF["Traefik · SSL"]
        GA["GitHub Actions"]
    end

    WEB -->|HTTP/SSE| GW
    CLI -->|HTTP| GW
    GW --> MID
    MID --> AUTH
    MID --> ORCH & WF & MEM & HUB

    ORCH --> BUS
    ORCH --> OPENAI & ANTH & OLLAMA & OR & DS & GROK & GEM & NIM
    WF --> ORCH
    WF --> MEM
    WF --> QD

    MEM --> QD
    BUS --> RD

    HUB --> PG
    PLUG --> PG
    ORCH --> PG & RD
    GW --> PG & RD

    DC --> WEB & GW & PG & RD & QD
    TF --> WEB & GW
    GA --> DC
```

## Component Architecture

### Frontend (Next.js 15)

```
src/
├── app/                          # Next.js App Router (31 pages)
│   ├── (dashboard)/              # Authenticated layout
│   │   ├── dashboard/            # KPI cards, recent activity
│   │   ├── agents/               # Agent CRUD grid
│   │   ├── chat/                 # Multi-panel chat
│   │   ├── tasks/                # Task management
│   │   ├── workflows/            # Workflow list + editor + runs
│   │   ├── agent-graph/          # Agent graph visualization
│   │   ├── analytics/            # Analytics dashboards
│   │   ├── documents/            # Document management
│   │   ├── knowledge/            # Knowledge base
│   │   ├── marketplace/          # Package marketplace
│   │   ├── providers/            # Provider status
│   │   ├── models/               # Model listing
│   │   ├── plugins/              # Plugin management
│   │   ├── memory/               # Memory explorer
│   │   └── settings/             # Profile + preferences
│   ├── login/                    # Authentication
│   └── register/                 # Registration
├── components/
│   ├── layout/                   # Sidebar, navbar, container
│   └── ui/                       # Button, Input, Card, Skeleton, etc.
└── stores/                       # 10 Zustand stores
```

### Backend (FastAPI)

```
app/
├── api/                          # 16 route modules
│   ├── auth.py                   # JWT + refresh auth
│   ├── agents.py                 # Agent CRUD + execute
│   ├── chat.py                   # Chat + SSE streaming
│   ├── tasks.py                  # Task CRUD
│   ├── workflows.py              # Workflow CRUD + engine
│   ├── documents.py              # Document upload + search
│   ├── agent_graph.py            # Graph visualization
│   ├── analytics.py              # Analytics endpoints
│   ├── marketplace.py            # Marketplace CRUD
│   ├── hub_registry.py           # Hub package registry
│   └── ... (health, bus, memory, etc.)
├── agents/                       # Agent implementations
│   ├── orchestrator.py           # Singleton agent router
│   ├── ceo.py                    # CEO delegation agent
│   ├── sales.py                  # Sales lead gen agent
│   ├── research.py               # Market research agent
│   └── buyer_finder.py           # Export buyer agent
├── core/                         # Core services
│   ├── workflow_engine.py         # DAG execution engine
│   ├── event_bus.py              # Pub/sub event system
│   ├── plugin_registry.py        # Plugin sandbox
│   ├── hub_resolver.py           # Semver dependency resolver
│   ├── hub_signer.py             # Ed25519 signatures
│   └── ... (security, encryption, etc.)
├── models/                       # SQLAlchemy models
├── schemas/                      # Pydantic schemas
└── providers/                    # LLM provider wrappers
```

## Data Flow

### Agent Execution

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant O as AgentOrchestrator
    participant AG as Agent
    participant P as LLM Provider
    participant D as Database

    U->>A: POST /agents/{id}/execute
    A->>D: Load agent config
    A->>O: Route to orchestrator
    O->>AG: process(prompt)
    AG->>P: LLM completion
    P-->>AG: Token stream
    AG-->>U: SSE events
    AG->>D: Store result
```

### Workflow Execution

```mermaid
sequenceDiagram
    participant U as User
    participant A as API
    participant WE as Workflow Engine
    participant N as Node Executor
    participant S as Services

    U->>A: POST /workflows/{id}/execute
    A->>WE: Execute DAG
    WE->>WE: Topological sort
    loop For each node
        WE->>N: Execute(node)
        N->>S: Agent/Knowledge/HTTP...
        S-->>N: Result
        N-->>WE: Output
        WE->>WE: Evaluate conditions
    end
    WE-->>A: Final output
    A-->>U: Run result
```

### Package Registry (Hub)

```mermaid
sequenceDiagram
    participant C as CLI
    participant H as Hub API
    participant R as Dependency Resolver
    participant D as Database
    participant K as Signing Key

    C->>H: Publish manifest
    H->>H: Validate manifest
    H->>K: Verify signature
    H->>R: Resolve deps
    R->>D: Query packages
    D-->>R: Version data
    R->>R: Topological sort
    R-->>H: Dependency chain
    H->>D: Store package
    H-->>C: Published OK

    C->>H: Install package
    H->>R: Resolve with deps
    R-->>H: Dep chain
    H-->>C: Resolution
    C->>C: Generate lockfile
```

## Security Architecture

```mermaid
graph LR
    subgraph Inbound
        RL[Rate Limiter<br/>10/min auth]
        SH[Security Headers<br/>CSP · HSTS · XFO]
        CORS[CORS<br/>Configurable origins]
    end
    subgraph Auth
        JWT[JWT Validation<br/>HS256 · Expiry]
        RBAC[RBAC<br/>4 Roles · 7 Permissions]
        REF[Refresh Rotation<br/>SHA-256 · 7-day]
    end
    subgraph Input
        SAN[Sanitizer<br/>Control chars · Length]
        PI[Prompt Injection<br/>10 regex patterns]
        XSS[XSS Escape<br/>HTML sanitize]
        FILE[File Validation<br/>14 types · 10 MB]
    end
    subgraph Storage
        ENC[Fernet Encryption<br/>Provider keys]
        SQL[SQLAlchemy ORM<br/>Parameterized queries]
    end

    Request --> RL
    RL --> SH
    SH --> CORS
    CORS --> JWT
    JWT --> RBAC
    RBAC --> SAN
    SAN --> PI
    PI --> XSS
    XSS --> FILE
    FILE --> ENC & SQL
```

## Database Schema

```mermaid
erDiagram
    users ||--o{ agents : owns
    users ||--o{ chats : owns
    users ||--o{ tasks : owns
    users ||--o{ workflows : owns
    users ||--o{ refresh_tokens : has
    users ||--o{ marketplace_installs : has
    users ||--o{ registry_packages : publishes
    users ||--o{ publisher_keys : manages

    agents ||--o{ chat_messages : generates
    chats ||--o{ chat_messages : contains

    workflows ||--o{ workflow_runs : has

    registry_packages ||--o{ registry_package_versions : has
    registry_packages ||--o{ registry_ratings : receives

    registry_package_versions ||--o{ registry_sync_logs : tracks
```

## Container Architecture

```yaml
services:
  postgres:16-alpine       # Port 5432 - Primary database
  redis:7-alpine            # Port 6379 - Cache & pub/sub
  qdrant:latest             # Port 6333 - Vector store
  api:                      # Port 8000 - FastAPI (healthcheck)
    depends_on: [postgres, redis]
    build: apps/api/Dockerfile
  web:                      # Port 3000 - Next.js (healthcheck)
    depends_on: [api]
    build: apps/web/Dockerfile
  traefik:                  # Port 443 - Reverse proxy + SSL
    optional: production only
```

All services share the `openpaper-net` bridge network and use JSON-file logging with 10 MB max size and 3-file rotation. Resource limits: API (1 GB), Web (512 MB), Postgres (512 MB), Redis (256 MB).

## Component Dependency Graph

| Component | Depends On | Used By |
|---|---|---|
| AgentOrchestrator | LLM Providers, Memory Engine | API, Workflow Engine |
| Workflow Engine | AgentOrchestrator, Knowledge Base, Memory Engine | API |
| Event Bus | Redis | AgentOrchestrator, API |
| Plugin Registry | PostgreSQL | API, Marketplace |
| Hub Registry | PostgreSQL, Dependency Resolver | API, CLI |
| Memory Engine | Qdrant | AgentOrchestrator, Workflow Engine |
| Dependency Resolver | — | Hub Registry |
| Rate Limiter | Redis (optional, in-memory fallback) | API Middleware |
