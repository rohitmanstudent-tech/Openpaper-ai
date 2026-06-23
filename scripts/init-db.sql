-- init-db.sql: runs on first PostgreSQL container start
-- Ensures extensions and initial data exist.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
