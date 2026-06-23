# OpenPaper AI — Docker Guide

## Production Deployment

### Prerequisites
- Docker & Docker Compose
- Domain names for API and frontend
- SSL/TLS certificates (auto via Let's Encrypt with Traefik)

### Quick Production Deploy

```bash
# Clone and configure
git clone https://github.com/openpaper-ai/openpaper.git
cd openpaper

# Configure environment
cp .env.example .env
# Edit .env with your provider API keys and SECRET_KEY

# Deploy with Traefik (SSL)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | — | JWT signing secret (generate: `openssl rand -hex 32`) |
| `POSTGRES_PASSWORD` | No | `openpaper_secret` | Database password |
| `OPENAI_API_KEY` | No | — | OpenAI provider key |
| `ANTHROPIC_API_KEY` | No | — | Anthropic provider key |
| `OLLAMA_BASE_URL` | No | `http://host.docker.internal:11434` | Ollama endpoint |
| `OPENROUTER_API_KEY` | No | — | OpenRouter provider key |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Allowed origins (comma-separated) |
| `LOG_LEVEL` | No | `info` | Log level: debug, info, warning, error |
| `SENTRY_DSN` | No | — | Sentry error tracking DSN |
| `ENCRYPTION_KEY` | No | — | Fernet key for provider secrets (generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) |

### Production Docker Compose

The production overlay (`docker-compose.prod.yml`) adds:
- **Traefik** reverse proxy with automatic Let's Encrypt SSL
- **2 replicas** each for API and web services
- **Host networking** for production ports

### Service Resource Limits

| Service | Memory Limit | CPU Reservation |
|---------|-------------|-----------------|
| postgres | 512 MB | 0.25 |
| redis | 256 MB | 0.25 |
| api | 1 GB | 0.5 |
| web | 512 MB | 0.5 |

### Health Checks

All services have health checks with start periods to ensure proper sequencing:
- Postgres → Redis → API → Web

### Backup

```bash
# Full backup (Postgres + Redis + Qdrant)
./scripts/backup.sh

# Restore
./scripts/restore.sh ./backups/openpaper_backup_20260101_120000.tar.gz
```

### Troubleshooting

```bash
# Check service logs
docker compose logs api
docker compose logs web

# Restart a service
docker compose restart api

# Full reset (preserves volumes)
docker compose down

# Full reset (destroys volumes)
docker compose down -v

# Run database migrations manually
docker compose exec api alembic upgrade head
```
