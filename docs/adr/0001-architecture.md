# ADR 0001: Agent and tool architecture

Status: Accepted

PermitFlow uses Python, FastAPI, LangGraph, PostgreSQL with pgvector, and explicit integration
clients. The graph coordinates intent extraction, retrieval, missing-field collection,
confirmation, and Jira submission. External clients are injected so core behavior can be tested.

