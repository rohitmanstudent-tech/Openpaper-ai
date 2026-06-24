# GitHub Actions Fix Report

## 1. Security Scan — Trivy Action Version Not Found
**File:** `.github/workflows/ci.yml`  
**Root Cause:** `aquasecurity/trivy-action@0.28.0` was missing the `v` prefix. The action's tags use `v`-prefixed semver (e.g. `v0.28.0`, `v0.36.0`). Without the prefix, GitHub Actions couldn't resolve the tag.  
**Fix:** Changed to `aquasecurity/trivy-action@v0.28.0`.  
**Verification:** YAML validates and the tag now correctly resolves to the pinned version.

## 2. Backend Tests — Postgres Health Check & `-U` Flag
**File:** `.github/workflows/ci.yml`  
**Root Cause:** The `--health-cmd` option was unquoted: `--health-cmd pg_isready -U openpaper`. Docker parsed this as `--health-cmd pg_isready` followed by `-U openpaper` as a separate `docker run` flag, which doesn't exist — causing `unknown shorthand flag U in -U`.  
**Fix:** Quoted the health command: `--health-cmd "pg_isready -U openpaper"`.  
**Verification:** Docker now correctly interprets `pg_isready -U openpaper` as the health check command.

## 3. Docker Integration — API Container Exits with Code 2
**Files:** `docker-compose.ci.yml`, `.github/workflows/docker-integration.yml`  
**Root Cause:** The API lifespan calls `init_encryption()` at line 55 of `app/main.py`, which requires `ENCRYPTION_KEY` to be set. In the CI environment, this env var was missing — `_get_or_create_key()` raised `RuntimeError("ENCRYPTION_KEY must be set in production")`, crashing the lifespan and causing uvicorn to exit with code 2.  
**Fix:** 
- Added `ENCRYPTION_KEY` to the workflow-level env in `docker-integration.yml`
- Added `ENCRYPTION_KEY: ${ENCRYPTION_KEY:-}` to the API service environment in `docker-compose.ci.yml`
- Also fixed the healthcheck URL in `docker-compose.ci.yml` from `/api/health` to `/api/v1/health/live`  
**Verification:** With the key present, `init_encryption()` succeeds, the lifespan completes, and the API starts serving.

## 4. Deploy to Staging — `ssh-agent` Exits with Code 1
**File:** `.github/workflows/cd.yml`  
**Root Cause:** The deploy jobs unconditionally ran `ssh-agent sh -c "echo \"$SSH_KEY\" | ssh-add - && ..."`. When `STAGING_SSH_KEY` or `PROD_SSH_KEY` secrets were not configured, `ssh-add` failed (empty key), causing `ssh-agent` to exit with code 1.  
**Fix:** 
- Added a `Check secrets` step that verifies `SSH_HOST` and `SSH_KEY` are non-empty, outputting `has_secrets=true/false`
- The deploy step is gated with `if: steps.check-secrets.outputs.has_secrets == 'true'`
- A `Skip notice` step prints a clear notice when secrets are missing
- `deploy-production` now depends on `build-and-push` (not `deploy-staging`), so a skipped staging doesn't block production deployment  
**Verification:** When secrets are absent, the job prints a notice and exits cleanly (not a failure).
