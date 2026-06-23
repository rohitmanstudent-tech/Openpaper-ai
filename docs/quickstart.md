# OpenPaper AI — Quickstart Guide

Get OpenPaper running in under 5 minutes.

## Prerequisites

- Docker & Docker Compose
- Git
- Node.js 18+ (for frontend dev)
- Python 3.12+ (for backend dev)

## Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/openpaper-ai/openpaper.git
cd openpaper

# Copy environment file
cp .env.example .env
# Edit .env to add your API keys (OpenAI, Anthropic, etc.)

# Start all services
docker compose up -d

# Wait for services to be healthy
docker compose ps

# Access the application
# Frontend: http://localhost:3000
# API:      http://localhost:8000
# Docs:     http://localhost:8000/docs
```

## Option 2: Development Setup

```bash
# Start infrastructure
docker compose up -d postgres redis

# Backend
cd apps/api
python -m venv .venv && source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows
pip install -e .
uvicorn app.main:app --reload --port 8000

# Frontend (in another terminal)
cd apps/web
npm install
npm run dev

# Access: http://localhost:3000
```

## Option 3: CLI Only

```bash
cd apps/cli
pip install -e .

# Authenticate
openpaper login

# Search & install
openpaper search export
openpaper install export-agent
```

## First Steps

1. **Create an account** — Register at http://localhost:3000/register
2. **Add a provider** — Go to Settings and add your OpenAI/Anthropic API key
3. **Chat with an agent** — Navigate to Chat and start a conversation
4. **Install from marketplace** — Browse /marketplace and install agents/workflows
5. **Run a workflow** — Go to /workflows and create or run a pre-built workflow

## Verification

```bash
# Check API health
curl http://localhost:8000/api/health

# Expected response:
# {"status":"healthy","version":"1.0.0","uptime_seconds":123}
```

## Next Steps

- Read the [Docker Guide](docker.md) for production deployment
- Read the [CLI Guide](cli.md) for package management
- Read the [Marketplace Guide](marketplace.md) for publishing packages
- Read the [Workflow Guide](workflow.md) for building automation
