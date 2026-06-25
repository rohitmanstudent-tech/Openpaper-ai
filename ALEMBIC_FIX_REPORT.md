# Alembic Fix Report

## Root Cause
`alembic.ini` contained `sqlalchemy.url = %(DB_URL)s`. Python's `ConfigParser` treats `%(name)s` syntax as interpolation references. Since no `DB_URL` option existed in the `[alembic]` section, `ConfigParser` raised `InterpolationMissingOptionError` when Alembic tried to read the config — crashing before any migration could run.

The CI workflow set `DB_URL` as an environment variable, which `%(DB_URL)s` cannot reference — ConfigParser interpolation only works with other options in the same INI section, not with environment variables.

## Fix

### `alembic.ini`
Replaced `%(DB_URL)s` with a harmless placeholder URL:
```ini
sqlalchemy.url = driver://user:pass@localhost/dbname
```
This avoids ConfigParser interpolation entirely.

### `alembic/env.py`
Added logic to load `DATABASE_URL` from the environment and override the config before migrations run:
```python
db_url = os.environ.get("DATABASE_URL")
if db_url:
    config.set_main_option("sqlalchemy.url", db_url)
```

### `.github/workflows/ci.yml`
Changed the `alembic upgrade head` step's env var from `DB_URL` to `DATABASE_URL` for consistency — the application and tests already use `DATABASE_URL`.

## Verification
- `ConfigParser.read('alembic.ini')` no longer raises `InterpolationMissingOptionError`
- `alembic check` progresses past config parsing to the expected DB-connection failure (no local Postgres)
- Backend tests: **308 passed, 9 skipped, 0 failed**
- Ruff: 0 violations, format check passes
