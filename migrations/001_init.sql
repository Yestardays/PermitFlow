CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS permission_items (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    jira_project_key TEXT NOT NULL,
    issue_type TEXT NOT NULL DEFAULT 'Service Request',
    approver_group TEXT NOT NULL,
    required_fields JSONB NOT NULL DEFAULT '[]',
    prerequisites JSONB NOT NULL DEFAULT '[]',
    validity_options JSONB NOT NULL,
    aliases JSONB NOT NULL DEFAULT '[]',
    sensitive BOOLEAN NOT NULL DEFAULT FALSE,
    description TEXT NOT NULL DEFAULT '',
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS permission_items_embedding_idx
ON permission_items USING hnsw (embedding vector_cosine_ops);

CREATE TABLE IF NOT EXISTS unmatched_requests (
    id BIGSERIAL PRIMARY KEY,
    open_id TEXT NOT NULL,
    user_input TEXT NOT NULL,
    inferred_intent JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS application_events (
    id BIGSERIAL PRIMARY KEY,
    thread_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS application_sessions (
    thread_id TEXT PRIMARY KEY,
    state JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS application_sessions_expires_idx
ON application_sessions (expires_at);
