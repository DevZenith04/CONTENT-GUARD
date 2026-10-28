# ADR 0002: SQLite for Event & Review Persistence

## Context
ContentGuard requires persistent tracking of audit events, decision logs, and human-in-the-loop review queues. For single-node deployments and developer self-hosting, operational simplicity and zero external service dependencies are critical.

## Decision
We utilize embedded **SQLite** with asynchronous IO (`aiosqlite`). Schema initialization and non-blocking queries are handled during FastAPI application startup.

## Alternatives Considered
- **PostgreSQL / MySQL**: Better for horizontally scaled multi-worker clusters with high concurrent write loads, but adds containerization and infrastructure overhead.
- **In-Memory Store (Dict/RAM)**: Fails durability requirements across server restarts.

## Consequences
- **Positive**: Single-file storage, zero external database setup, portable across dev and production.
- **Negative / Scaling Boundary**: SQLite handles a single writer at a time. If multi-replica horizontal clustering is deployed, the store layer must migrate to PostgreSQL.
