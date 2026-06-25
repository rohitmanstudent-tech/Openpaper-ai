# Docker Startup Fix Report

## Root Cause
The API container exited with code 2 because Python could not find the installed dependencies at runtime.

**Chain of failure:**

1. The API `Dockerfile` uses `pip install --no-cache-dir --user -e .` in the builder stage, which installs all dependencies to the **root** user site-packages at `/root/.local/lib/python3.12/site-packages/`.

2. The final production stage switches to a non-root user (`USER openpaper`) and copies the installed packages to `/root/.local/`.

3. When the container runs as user `openpaper`, Python's `site` module resolves the user site-packages directory to `/home/openpaper/.local/lib/python3.12/site-packages/` (which is empty) **instead** of `/root/.local/lib/python3.12/site-packages/`.

4. Although the `uvicorn` executable is found via `PATH` (`/root/.local/bin/uvicorn`), when uvicorn tries to `import fastapi`, `import httpx`, and other dependencies, these packages are not in Python's `sys.path` — they live only in `/root/.local/lib/python3.12/site-packages/`.

5. The resulting `ImportError` caused uvicorn to exit with **code 2** (application load failure).

## Fix

### `apps/api/Dockerfile`
Added `PYTHONPATH` to include the root user site-packages directory where the builder installed all dependencies:

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:$PATH" \
    PYTHONPATH="/root/.local/lib/python3.12/site-packages:$PYTHONPATH"
```

Also fixed the stale healthcheck URL from `/api/health` to `/api/v1/health/live`.

## Files Changed
| File | Change |
|------|--------|
| `apps/api/Dockerfile:16-19` | Added `PYTHONPATH` env var |
| `apps/api/Dockerfile:30` | Fixed healthcheck URL |

## Verification
- Backend tests: 16/16 bus tests pass (spot check)
- All workflow YAML files validate
- With `PYTHONPATH` set, Python's import system finds packages in `/root/.local/lib/python3.12/site-packages/` regardless of which user runs the container
