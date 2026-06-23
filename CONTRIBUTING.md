# Contributing to OpenPaper AI

> First off, thank you for considering contributing! We welcome contributions from everyone.

## Code of Conduct

This project adheres to the [Contributor Covenant](CODE_OF_CONDUCT.md) v2.1. By participating, you are expected to uphold this code. Please report unacceptable behavior to [security@openpaper.ai](mailto:security@openpaper.ai).

## How to Contribute

### Reporting Bugs

1. **Search existing issues** — Check if the bug has already been reported
2. **Use the bug report template** — [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md)
3. **Include details** — Steps to reproduce, expected behavior, actual behavior, environment, logs, and correlation ID if available

### Suggesting Features

1. **Check the roadmap** — Your feature might already be planned
2. **Use the feature request template** — [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md)
3. **Explain the problem** — What problem does this solve? Who benefits?
4. **Describe alternatives** — What other approaches have you considered?

### Pull Requests

1. **Fork the repository** and create a feature branch from `develop`
2. **Install dependencies:**

```bash
# Backend
cd apps/api
pip install -e ".[dev]"

# Frontend
cd apps/web
npm install

# CLI
cd openpaper_cli
pip install -e .
```

3. **Make your changes**, following the coding conventions
4. **Run tests:**

```bash
# Backend tests
cd apps/api
pytest tests/ -v

# Frontend lint & build
cd apps/web
npm run lint
npm run build

# CLI
openpaper --help
```

5. **Commit with a descriptive message** using conventional commit format:

```
feat(agents): add LinkedIn scraping agent
fix(workflows): resolve DAG cycle detection
docs(api): update authentication flow
chore(deps): bump fastapi to 0.111.0
```

6. **Push to your fork** and open a pull request against `develop`
7. **Complete the PR template** checklist

### Development Workflow

```
develop  ←  feature/your-feature  (submit PR)
     ↓
main     ←  squash merge after review
     ↓
v*.*.*   ←  tag on release
```

## Project Structure

```
openpaper/
├── apps/
│   ├── api/              # FastAPI backend (Python 3.12)
│   │   ├── app/
│   │   │   ├── api/      # Route handlers
│   │   │   ├── agents/   # Agent implementations
│   │   │   ├── core/     # Business logic
│   │   │   ├── models/   # SQLAlchemy ORM
│   │   │   └── schemas/  # Pydantic schemas
│   │   ├── tests/        # pytest test suite
│   │   └── alembic/      # Database migrations
│   ├── web/              # Next.js 15 frontend
│   │   └── src/
│   │       ├── app/      # App Router pages
│   │       ├── components/  # UI components
│   │       └── stores/   # Zustand state
│   └── cli/              # Legacy CLI (merged into openpaper_cli)
├── openpaper_cli/        # Main CLI (16 commands)
├── packages/
│   └── shared/           # Shared TypeScript types
├── docs/                 # Documentation
├── scripts/              # Backup, restore, benchmark scripts
├── screenshots/          # Screenshots and demos
└── .github/              # CI/CD, issue templates
```

## Coding Conventions

### Python
- **Target:** Python 3.12+
- **Style:** PEP 8 — enforced via Ruff (`ruff check .`)
- **Formatting:** Ruff formatter (120 char line length, double quotes)
- **Types:** Full type annotations on all functions
- **Async:** Use `async/await` for all I/O-bound operations

### TypeScript
- **Target:** ES2022, strict mode
- **Style:** ESLint + Prettier
- **Framework:** React 19 with Next.js 15 App Router
- **State:** Zustand stores with TypeScript generics
- **Components:** Shadcn UI primitives with Tailwind CSS

### Commit Convention

```
<type>(<scope>): <description>

Types: feat, fix, docs, style, refactor, perf, test, chore, ci
Scope: api, web, cli, hub, docs, scripts, deps, release
```

## Testing

- **Backend:** pytest with async support (`asyncio_mode = auto`)
- **Frontend:** Next.js build verification (`npm run build`)
- **CLI:** Manual verification of all 16 commands (`openpaper --help`)
- **Docker:** Full integration test via CI workflow

Run the full backend suite:

```bash
cd apps/api
pytest tests/ -v --tb=short
```

## Release Process

1. All tests pass (308+ backend, frontend build, CLI commands)
2. CHANGELOG.md updated
3. Version bumped in `pyproject.toml`, `package.json`, `openpaper_cli/__init__.py`
4. Tag created: `git tag v{major}.{minor}.{patch}[-rc.{n}]`
5. GitHub Release created with release notes
6. CD workflow builds and pushes Docker images

## Questions?

- Open a [Discussion](https://github.com/openpaper-ai/openpaper/discussions)
- Join our community (link coming soon)
- Read the [docs](docs/)
