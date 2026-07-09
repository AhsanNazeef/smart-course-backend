# ADR-001: Microservices in a Monorepo, Database-per-Service

- **Status:** Accepted
- **Date:** 2026-07-09
- **Deciders:** Engineering lead, project developer
- **Supersedes:** the initial modular-monolith approach used on Days 1–4

---

## Context

SmartCourse began as a **modular monolith**: one FastAPI application with internal service
modules (User, Course, Enrollment, Analytics, AI) all sharing a single PostgreSQL database
and communicating through in-process function calls. Days 1–4 built this foundation
(scaffold, tests, initial migration, and the User domain's `route → service → repository`
layering).

The engineering lead has directed a switch to a **microservices architecture** so the
project exercises the distributed-systems skills it is meant to teach (independent
deployment, event-driven communication, service isolation) and matches the
microservices-oriented infrastructure already provisioned (Kafka, Temporal, RabbitMQ).

We considered three shapes:

1. **Full microservices** — separate repos/pipelines per service. Highest fidelity,
   highest operational cost for a solo developer.
2. **Monorepo, database-per-service** — one repository; each service is its own runnable
   app with its own database; communication via events/HTTP. *(chosen)*
3. **Split apps, shared database first** — separate apps but one shared DB. Rejected: a
   shared database couples services and is not true microservices.

## Decision

Adopt **Option 2: microservices in a monorepo with a database per service.**

Concretely:

- **One git repository** holds all services under `services/<name>_service/`.
- **Each service is its own FastAPI app** with its own `main.py`, runnable independently.
- **Each service owns its own database.** No shared business-data models across services.
- **Services communicate only via Kafka events (async) and HTTP (sync).** A service never
  reads or writes another service's database.
- **Each service owns its own migrations** (its own Alembic environment/history).
- **Internal layering stays** `route → service → repository` inside each service.
- **`shared/` is restricted** to genuinely cross-cutting code — event contracts, config,
  utilities — and must **not** contain business-data models.
- **Docker Compose** runs every service plus its own database for local development.

### The defining rule

> **A service may only touch its own database.** Any data another service needs is obtained
> by calling that service's API or consuming its events — never by querying its tables.

This single constraint is what makes services independently deployable. If it is ever
violated, the architecture silently degrades back into a distributed monolith (the worst of
both worlds).

## Consequences

### Positive
- Services can be developed, tested, deployed, and scaled independently.
- Clear ownership boundaries; a change in one service cannot silently break another's data.
- Real practice with event-driven design, Kafka, and service contracts.
- The existing per-domain layering carries over directly into each service.

### Negative / costs (accepted)
- **More moving parts:** multiple apps and databases to run and debug locally.
- **No cross-service DB joins:** data that used to be a SQL `JOIN` now requires an API call
  or an event-maintained local copy (read model). Example: Enrollment can no longer join to
  the `users` table; it must call the User service or cache what it needs.
- **Eventual consistency:** data propagated by events is not instantly consistent.
- **Distributed transactions:** multi-service operations need sagas/workflows (Temporal),
  not a single DB transaction.
- **Duplicated boilerplate:** each service repeats app setup, config, and migration wiring.

### Neutral
- The `shared/models/` package from the monolith phase will be **dissolved**; each service
  takes ownership of the models it needs.

## Migration plan (incremental, one service at a time)

The switch is **not** a big-bang rewrite. We migrate service by service so the app keeps
working throughout.

1. **User service first.** Give it its own app (`services/user_service/main.py`), its own
   database, and its own Alembic migrations. Move the `User` model into it.
2. **Introduce event contracts** in `shared/events/` (e.g. `user.created`).
3. **Extract the next service** (Course), repeating the pattern; replace any cross-service
   DB access with API calls or events.
4. **Continue** for Enrollment, Analytics, AI.
5. **Retire monolith remnants** (top-level `main.py`, shared `alembic/`, `shared/models/`)
   once every service owns its data.

Until a service is extracted, it may still run in the original app. Each extraction is its
own reviewable, testable step.

## Notes

- This ADR documents an architectural decision and plan. It is **not** a claim that the
  migration is complete — see the migration status in each affected document
  (`README.md`, `docs/product/prd.md`, `AGENTS.md`).
- Roadmap days written for the monolith remain useful for the concepts they teach; their
  "single app / single database" assumptions are superseded by this ADR.
