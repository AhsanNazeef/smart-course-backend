# SmartCourse Microservices Implementation & Learning Plan

**Target architecture:** microservices in a monorepo, with a **database per service**
(see [ADR-001](../architecture/adr-001-microservices-monorepo.md)). Each service is its own
runnable FastAPI app that owns its own database and talks to others only through **Kafka
events** (async) and **HTTP** (sync).

**Month 1 goal:** Extract the first services cleanly (User, then Course), stand up the
**event backbone** that lets them communicate, and learn distributed-systems fundamentals
by doing — one tested, explainable service at a time.

**Month 2 goal:** Add the harder services (Enrollment, Analytics, AI), a gateway with
cross-service auth, observability that spans service boundaries, per-service
containerization/CI, and reliability + performance hardening.

> **This plan supersedes the earlier monolith roadmap.** Days 1–4 bootstrapped the project
> as a modular monolith; from here we migrate to microservices **incrementally**. The old
> monolith day-plan is preserved in git history.

---

## Planning Approach: Rolling Wave

We are early (Day 4). Rather than over-specifying 60 speculative days, this plan is:

- **Detailed** for the near term (Phases 1–3 — the next ~3 weeks), day by day.
- **Themed milestones** for later phases (4–10), fleshed out just-in-time as we learn.

Expect later phases to be refined once we've felt the real shape of the first services.
That's not vagueness — it's how experienced teams plan work with genuine unknowns.

---

## How To Use This Plan

Each working session should produce four things:

1. **Implementation** — code, config, migration, test, or documentation.
2. **Explanation** — what changed, why it exists, and how it fits the architecture.
3. **Verification** — commands run, expected output, and known gaps.
4. **Learning notes** — links and short notes for the technology used that day.

Recommended daily rhythm:

- 30–45 minutes: read the small set of docs for the day.
- 2–3 hours: implement one focused slice.
- 30–45 minutes: test, review, and write notes.
- End each day with a commit or a clearly documented reason not to commit yet.

**Senior engineering rule:** prefer one complete, tested, understandable slice over five
half-finished abstractions.

---

## Microservices Ground Rules (read before every phase)

These constraints define the architecture. Breaking one silently turns the system into a
"distributed monolith" — the worst of both worlds.

1. **A service only touches its own database.** Never query another service's tables.
2. **No foreign keys across services.** An enrollment can't FK to `users` — those live in a
   different database. Store the id you need and treat it as an opaque reference.
3. **Get other services' data two ways only:** call their **API** (sync) or consume their
   **events** (async, keeping a local read copy).
4. **Events are contracts.** Once published, an event's shape is a promise. Version it;
   don't break it.
5. **Each service owns its migrations.** No shared Alembic history.
6. **`shared/` is for cross-cutting code only** — event schemas, config base, utilities.
   Never business-data models.
7. **Design for failure.** Any network/API/event call can fail or arrive twice. Make
   consumers idempotent and handle timeouts.

---

## Where We Are Now (Phase 0 — done)

Days 1–4 delivered the bootstrap (as a monolith, intentionally):

- ✅ Scaffold, Docker Compose infra, settings with friendly validation, test suite.
- ✅ Initial schema + Alembic migration with enrollment/progress unique constraints.
- ✅ User domain with `route → service → repository` layering and layer-isolated tests.

That layering is exactly what each microservice uses internally, so nothing is wasted.

---

## Phase 1 — Extract the User Service (Days 5–9)

**Phase goal:** turn the User domain into a standalone service with its own app, database,
and migrations. This is the template every later service copies.

### Day 5 — User service app + own database
**Implement**
- Add `services/user_service/main.py` — its own FastAPI app instance.
- Add a dedicated `users_db` Postgres to `docker-compose.yml` (separate from any shared DB).
- Add a per-service settings object with its own `USER_SERVICE_DATABASE_URL`.
- Run the service standalone on its own port.

**Learn:** why database-per-service; how one repo can hold many runnable apps.
**Verify:** `uvicorn services.user_service.main:app --port 8001` then hit `/health`.
**Done when:** the User service boots independently against its own database.

### Day 6 — Move the User model + own migrations
**Implement**
- Move the `User` model into `services/user_service/models/`.
- Give the service its **own Alembic** environment and generate its initial migration.
- Drop `User` from the shared models package.

**Learn:** per-service migration history; why shared models break service isolation.
**Verify:** `alembic -c services/user_service/alembic.ini upgrade head`; `\dt` in `users_db`.
**Done when:** the User service creates its own schema from its own migration.

### Day 7 — User CRUD through the layers
**Implement**
- Flesh out repository/service: `create_user`, `get_by_id`, `get_by_email`, `list`.
- Add `POST /users` (create) and keep `GET` routes.
- Password hashing (passlib/bcrypt); reject duplicate email cleanly.

**Learn:** password hashing basics; request/response schemas; clean error responses.
**Verify:** `pytest services/user_service/tests -v`; create a user, reject a duplicate.
**Done when:** users can be created and fetched via the service's own API.

### Day 8 — Publish the first event: `user.created`
**Implement**
- Create `shared/events/` with a versioned event envelope (id, type, occurred_at, data).
- Publish `user.created` to Kafka after a successful create (behind an interface).
- Add a mocked test so tests don't require a live broker.

**Learn:** event envelopes; producers; why events decouple services.
**Verify:** `docker compose up -d kafka`; create a user; observe the event (or mock in test).
**Done when:** creating a user emits a well-formed `user.created` event.

### Day 9 — Phase 1 review & the service template
**Implement**
- Extract the repeatable bits (app factory, settings base, alembic layout) into a
  documented pattern other services will copy.
- Write a short "how to add a new service" note in `docs/`.

**Done when:** you can explain, and repeat, the steps to stand up a new service.

---

## Phase 2 — Event Backbone (Days 10–13)

**Phase goal:** make events reliable enough to build on, before more services depend on them.

### Day 10 — Transactional outbox in the User service
**Implement**
- Add an `outbox` table in `users_db`.
- Write events to the outbox **in the same transaction** as the data change.
- Add a poller that publishes outbox rows to Kafka and marks them sent.

**Learn:** the dual-write problem; why the outbox pattern guarantees at-least-once delivery.
**Verify:** create a user in a failing/succeeding transaction; confirm event only on commit.
**Done when:** events are never lost even if Kafka is briefly down.

### Day 11 — A consumer + idempotency
**Implement**
- Add a tiny consumer (e.g. a temporary logging consumer) for `user.created`.
- Track processed event ids so a re-delivered event is ignored.

**Learn:** consumer groups; offsets; idempotent consumers; at-least-once vs exactly-once.
**Verify:** deliver the same event twice; confirm it's processed once.
**Done when:** duplicate events cause no duplicate work.

### Day 12 — Event contracts & schema discipline
**Implement**
- Document each event's schema in `shared/events/` (and/or the schema registry).
- Add a compatibility note: how you'll evolve events without breaking consumers.

**Learn:** schemas as long-term contracts; backward/forward compatibility.
**Done when:** event shapes are documented and versioning rules are written down.

### Day 13 — Testing across a boundary
**Implement**
- Add a contract-style test: producer emits the agreed shape; a fake consumer asserts it.
- Keep unit tests fast; mark broker-dependent tests separately.

**Learn:** contract testing; the test pyramid across services.
**Done when:** a broken event shape fails a test before it reaches another service.

---

## Phase 3 — Extract the Course Service (Days 14–18)

**Phase goal:** a second service, proving the template — and the first place we must get
another service's data *without* a shared database.

- **Day 14** — Course service app + own `courses_db` (copy the Phase 1 template).
- **Day 15** — Move Course/Module/Lesson/Asset models + own migrations.
- **Day 16** — Course CRUD API; keep publishing separate from CRUD; filtering by status.
- **Day 17** — Publish `course.published` (via outbox); define the event contract.
- **Day 18** — Course service consumes `user.created` to keep a **local read copy** of the
  minimal instructor data it needs (name/id) — *no query into `users_db`*.

**Learn:** local read models; eventual consistency; why duplication beats coupling here.
**Done when:** Course service serves instructor info it learned via events, not via a join.

---

## Phase 4 — Enrollment Service (Milestone)

The hardest service: it references **both** users and courses, which now live in other
databases. This is where microservices trade-offs become concrete.

- Own app + own `enrollments_db`; move Enrollment/Progress models + migrations.
- **No FK to users or courses.** Store `student_id` / `course_id` as plain references.
- Validate enrollments by **calling** the User and Course services (or checking a local
  read copy built from their events).
- Keep the enrollment uniqueness and idempotent-progress rules (now enforced within
  `enrollments_db` only).
- Publish `enrollment.created` and `progress.updated`.

**Learn:** cross-service consistency, sagas vs local checks, handling a dependency being
down.
**Done when:** a student can enroll and progress without any cross-database access.

---

## Phase 5 — API Gateway & Cross-Service Auth (Milestone)

- Introduce an edge/gateway that routes external traffic to the right service.
- Decide where auth lives: issue JWTs centrally; each service **verifies** them locally
  (shared verification helper in `shared/`, not a shared user table).
- RBAC checks (student/instructor/admin) enforced per service.

**Learn:** gateway routing, token verification at the edge and per service, trust boundaries.

---

## Phase 6 — Analytics Service (Milestone)

- Event-driven **read models**: consume `enrollment.created`, `progress.updated`,
  `course.published` to build course/instructor/platform metrics in `analytics_db`.
- Add a reconciliation job to rebuild analytics from event history.
- Instructor and admin analytics APIs with permissions.

**Learn:** CQRS, read models, reconciliation — microservices' natural analytics pattern.

---

## Phase 7 — AI Service (Milestone)

- Own service wrapping Qdrant + LangGraph for course Q&A (RAG).
- Index course content it learns about via events (re-index on `course.published`).
- Provider abstraction (OpenAI/Groq/Anthropic); citations; streaming; cost/rate controls.
- Mocked provider tests so tests don't spend money.

**Learn:** embeddings, vector search, RAG, provider abstraction, grounded generation.

---

## Phase 8 — Observability Across Services (Milestone)

- Structured logs with correlation ids **propagated across service calls and events**.
- OpenTelemetry tracing that follows one request through the gateway → services → events.
- Prometheus metrics per service; Grafana dashboards; Jaeger traces spanning boundaries.

**Learn:** distributed tracing, correlation across async hops, per-service golden signals.

---

## Phase 9 — Containerization, CI & Local Orchestration (Milestone)

- A **Dockerfile per service**; each added to `docker-compose.yml` with its own DB + healthcheck.
- One command to bring up the whole system locally.
- CI that lints, tests, and checks migrations **per service** (matrix build).
- Seed-data and reset scripts for the full multi-service stack.

**Learn:** container-per-service, service networking, per-service pipelines.

---

## Phase 10 — Reliability, Performance, Security & Demo (Milestone)

- Retries, timeouts, dead-letter handling for events/consumers; workflow compensation (Temporal).
- Per-service indexing and a performance baseline for key flows.
- Security pass: secret hygiene, CORS, rate limits, authorization negative tests per service.
- End-to-end demo across all services; `month-2-review.md`; Month 3 roadmap (frontend/deploy/scale).

**Learn:** resilience patterns, saga compensation, release-readiness across a distributed system.

---

## What To Learn By Topic

### Microservices & Distributed Systems
- Service boundaries, database-per-service, no cross-service FKs.
- Sync (HTTP) vs async (events) communication and when to use each.
- Eventual consistency, read models, sagas, idempotency.
- API gateway, service discovery basics, trust boundaries.

### Event-Driven Architecture
- Event envelopes and contracts; Kafka topics, producers, consumers, groups, offsets.
- Transactional outbox; at-least-once delivery; dead-letter handling.

### Backend Per Service
- FastAPI app-per-service, dependencies, middleware, security, testing.
- Pydantic schemas/settings; REST design and OpenAPI docs.
- PostgreSQL per service; SQLAlchemy async; per-service Alembic migrations.

### AI
- Embeddings, Qdrant, RAG, LangGraph, provider abstraction, citations, cost controls.

### Observability
- Correlation ids across services; OpenTelemetry/Jaeger tracing across boundaries;
  Prometheus/Grafana per service.

### Reliability, Security & DevEx
- Retries/timeouts/idempotency; saga compensation with Temporal.
- JWT verification per service; RBAC; secret hygiene; rate limiting.
- Dockerfile-per-service; per-service CI; repeatable multi-service local setup.

---

## Official Study Links

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- SQLAlchemy asyncio: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Alembic: https://alembic.sqlalchemy.org/en/latest/
- PostgreSQL: https://www.postgresql.org/docs/
- Docker Compose: https://docs.docker.com/compose/
- Kafka: https://kafka.apache.org/documentation/
- Transactional outbox pattern: https://microservices.io/patterns/data/transactional-outbox.html
- Database per service: https://microservices.io/patterns/data/database-per-service.html
- Saga pattern: https://microservices.io/patterns/data/saga.html
- API gateway: https://microservices.io/patterns/apigateway.html
- Temporal Python SDK: https://docs.temporal.io/develop/python
- Celery: https://docs.celeryq.dev/en/stable/
- Redis: https://redis.io/docs/latest/
- Qdrant: https://qdrant.tech/documentation/
- LangGraph: https://docs.langchain.com/oss/python/langgraph/overview
- OpenAI embeddings: https://platform.openai.com/docs/guides/embeddings
- Groq: https://console.groq.com/docs/overview
- Anthropic: https://docs.anthropic.com/en/docs/overview
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
- Jaeger: https://www.jaegertracing.io/docs/
- Prometheus: https://prometheus.io/docs/prometheus/latest/getting_started/
- Grafana: https://grafana.com/docs/grafana/latest/

---

## Definition Of Done (Microservices MVP)

The migration is on track when:

- At least User and Course run as **independent services with their own databases**.
- Services communicate via **events and HTTP only** — no cross-service DB access anywhere.
- The **outbox** guarantees events aren't lost; **consumers are idempotent**.
- Enrollment works **without** foreign keys to users/courses.
- Each service has its **own migrations, tests, and Dockerfile**.
- A request can be **traced across services**; each service exposes metrics.
- Docs (ADR, PRD, per-service READMEs) match the running system.
- You can explain database-per-service, eventual consistency, and the outbox pattern.

---

## What Still Will Not Be Fully Finished After 2 Months

Even with a strong two-month build, this is not yet a production platform. Likely remaining:

- Polished frontend and admin dashboard.
- Production cloud deployment, service mesh, and infrastructure-as-code.
- Full distributed-tracing coverage and mature alerting/on-call runbooks.
- Robust saga/compensation coverage for every multi-service operation.
- Multi-tenant model, SSO, billing, and compliance features.
- Load testing at the full 10,000+ concurrent-learner target.
- Backup/restore and disaster recovery per service.
