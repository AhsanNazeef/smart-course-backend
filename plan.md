# SmartCourse 1-Month Implementation and Learning Plan

**Start point:** SmartCourse has project docs, a FastAPI scaffold, settings, database models, Alembic setup, Docker Compose infrastructure, and Prometheus config.

**Month 1 goal:** Build a working backend MVP foundation while learning the technologies as they are introduced. The goal is not to finish the full enterprise platform in one month. The goal is to build the first clean, tested, explainable vertical slices using senior engineering habits.

---

## How To Use This Plan

Each day should produce four things:

1. **Implementation** - code, config, migration, test, or documentation.
2. **Explanation** - what changed, why it exists, and how it fits the architecture.
3. **Verification** - commands run, expected output, and known gaps.
4. **Learning notes** - links and short notes for the technology used that day.

Recommended daily rhythm:

- 30-45 minutes: read the small set of docs for the day.
- 2-3 hours: implement one focused slice.
- 30-45 minutes: test, review, and write notes.
- End each day with a commit or a clearly documented reason not to commit yet.

Senior engineering rule: prefer one complete, tested, understandable slice over five half-finished abstractions.

---

## Month 1 Outcomes

By the end of this month, SmartCourse should have:

- A clean scaffold committed and pushed.
- Working local infrastructure through Docker Compose.
- Initial database migration for the core models.
- User, course, module, lesson, enrollment, and progress API foundations.
- Service and repository layers for core business logic.
- Authentication and basic RBAC.
- Transaction-safe enrollment behavior.
- Basic event publishing shape.
- A first background processing path.
- A first Temporal workflow for course publishing.
- A first AI/RAG prototype using Qdrant and LangGraph.
- Prometheus metrics, structured logging, and basic tracing.
- Tests around the most important paths.
- Documentation and ADR notes explaining important decisions.

---

## Week 1 - Backend Foundation, Database, and First APIs

### Day 1 - Commit the Scaffold and Run the Project

**Implement**
- Review and commit current scaffold files.
- Confirm `.env` is ignored and `.env.example` is safe.
- Run `docker compose config -q`.
- Run FastAPI locally and check `/health`, `/api/v1`, `/docs`, and `/metrics`.

**Learn**
- What FastAPI is and why it is a good API framework.
- What Docker Compose does for local development.
- Why `.env` is private but `.env.example` is committed.

**Verify**
```bash
python -m compileall -q main.py shared alembic
python -c "from main import app; print([route.path for route in app.routes])"
docker compose config -q
```

**Study**
- FastAPI: https://fastapi.tiangolo.com/
- Docker Compose: https://docs.docker.com/compose/

**Done when**
- Scaffold is committed.
- App imports successfully.
- Docker Compose validates.

### Day 2 - Settings, Application Structure, and Health Checks

**Implement**
- Add a small test suite for app startup and health endpoints.
- Make settings validation errors easy to understand.
- Document all required `SMARTCOURSE_` environment variables.

**Learn**
- Pydantic settings.
- Environment variable prefixes.
- FastAPI app lifecycle.

**Verify**
```bash
pytest tests/ -v
```

**Study**
- Pydantic settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- FastAPI lifespan events: https://fastapi.tiangolo.com/advanced/events/

**Done when**
- Tests cover `/health` and `/api/v1`.
- Missing config errors are understandable.

### Day 3 - SQLAlchemy Models and Initial Alembic Migration

**Implement**
- Review all current SQLAlchemy models.
- Add missing constraints that protect data consistency, especially enrollment uniqueness.
- Generate the initial Alembic migration.
- Review the migration before applying it.

**Learn**
- ORM models.
- Relationships and foreign keys.
- Migrations versus `create_all`.

**Verify**
```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
alembic current
```

**Study**
- SQLAlchemy asyncio: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Alembic: https://alembic.sqlalchemy.org/en/latest/
- PostgreSQL docs: https://www.postgresql.org/docs/

**Done when**
- Initial migration exists.
- Database schema can be created from migrations.

### Day 4 - Repository and Service Layer Pattern

**Implement**
- Create repository pattern for one domain first, likely users.
- Add service layer above repository.
- Keep database queries out of API route handlers.

**Learn**
- Separation of concerns.
- Dependency injection.
- Why routes should stay thin.

**Verify**
```bash
pytest tests/ -v
```

**Study**
- FastAPI dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/
- SQLAlchemy sessions: https://docs.sqlalchemy.org/en/20/orm/session_basics.html

**Done when**
- One domain uses route -> service -> repository.
- Tests can mock or isolate the service layer.

### Day 5 - User API Foundation

**Implement**
- Add user schemas.
- Add create user and get user endpoints.
- Add password hashing but not full auth yet.
- Add validation and duplicate email handling.

**Learn**
- Pydantic request/response schemas.
- Password hashing basics.
- HTTP status codes and error responses.

**Verify**
```bash
pytest tests/ -v
curl http://localhost:8000/docs
```

**Study**
- FastAPI request body: https://fastapi.tiangolo.com/tutorial/body/
- FastAPI response models: https://fastapi.tiangolo.com/tutorial/response-model/

**Done when**
- Users can be created through API.
- Duplicate email returns a clean error.

### Day 6 - Course API Foundation

**Implement**
- Add course schemas.
- Add create/list/get/update endpoints for courses.
- Keep publishing separate from CRUD.
- Add basic filtering by status and instructor.

**Learn**
- RESTful resource design.
- Pagination and filtering basics.
- Domain modeling for course content.

**Verify**
```bash
pytest tests/ -v
```

**Study**
- FastAPI bigger applications: https://fastapi.tiangolo.com/tutorial/bigger-applications/

**Done when**
- Course CRUD works through API.
- Route structure is ready for modules and lessons.

### Day 7 - Week 1 Review and Refactor

**Implement**
- Clean up naming and module boundaries.
- Add missing tests for Week 1 code.
- Write a short ADR for service/repository structure if the pattern is adopted.

**Learn**
- How to review code like a senior engineer.
- How to spot accidental complexity.
- How to keep commits meaningful.

**Verify**
```bash
pytest tests/ -v --cov
ruff check .
```

**Done when**
- Week 1 code is clean, tested, and documented.

---

## Week 2 - Core Learning Platform Behavior

### Day 8 - Authentication and RBAC

**Implement**
- Add login endpoint.
- Issue JWT access tokens.
- Add current-user dependency.
- Add role checks for student, instructor, and admin.

**Learn**
- JWT.
- Authentication versus authorization.
- RBAC.

**Verify**
```bash
pytest tests/ -v
```

**Study**
- FastAPI security: https://fastapi.tiangolo.com/tutorial/security/

**Done when**
- Protected endpoints require a token.
- Instructor/admin-only checks work.

### Day 9 - Course Modules, Lessons, and Assets

**Implement**
- Add endpoints for modules and lessons.
- Add ordering rules.
- Add basic asset metadata endpoint.
- Prevent students from editing instructor content.

**Learn**
- Nested resources.
- Ownership checks.
- API ergonomics.

**Verify**
```bash
pytest tests/ -v
```

**Done when**
- Instructor can build a simple course outline.
- Student cannot mutate instructor-owned content.

### Day 10 - Enrollment With Strong Consistency

**Implement**
- Add enrollment endpoint.
- Use a transaction.
- Enforce one active enrollment per student/course.
- Protect `current_enrollments` from race conditions.

**Learn**
- Database transactions.
- Unique constraints.
- Race conditions and consistency.

**Verify**
```bash
pytest tests/ -v
```

**Study**
- PostgreSQL constraints: https://www.postgresql.org/docs/current/ddl-constraints.html
- SQLAlchemy transactions: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html

**Done when**
- Duplicate enrollment is prevented.
- Enrollment count stays correct.

### Day 11 - Progress Tracking

**Implement**
- Add mark lesson complete endpoint.
- Add progress percentage calculation.
- Make completion idempotent.

**Learn**
- Idempotency.
- Derived state.
- Why progress is critical data.

**Verify**
```bash
pytest tests/ -v
```

**Done when**
- Repeating the same completion request does not corrupt data.
- Progress percentage updates correctly.

### Day 12 - Error Handling, Pagination, and API Polish

**Implement**
- Add consistent error response shape.
- Add pagination to list endpoints.
- Add request IDs in logs.
- Improve OpenAPI summaries and tags.

**Learn**
- API contracts.
- Error design.
- Operability through logs.

**Verify**
```bash
pytest tests/ -v
```

**Done when**
- Client errors are predictable.
- List endpoints are paginated.

### Day 13 - Integration Testing With PostgreSQL

**Implement**
- Add integration tests for user, course, and enrollment flows.
- Prefer a real database in tests when validating SQL behavior.
- Keep unit tests fast and integration tests focused.

**Learn**
- Test pyramid.
- Why database behavior must be tested against a real database.
- Fixtures and cleanup.

**Verify**
```bash
pytest tests/ -v
```

**Study**
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- Pytest docs: https://docs.pytest.org/

**Done when**
- Core flow tests pass reliably.

### Day 14 - Week 2 Review and Demo

**Implement**
- Create a demo script or API collection showing:
  - register/login
  - create course
  - add lesson
  - enroll
  - mark progress
- Write Week 2 learning notes.

**Learn**
- End-to-end thinking.
- How to explain a backend workflow clearly.

**Done when**
- A simple learner journey works.

---

## Week 3 - Events, Background Workflows, and AI Foundation

### Day 15 - Event Design and Outbox Pattern

**Implement**
- Define event envelope: event id, type, aggregate id, timestamp, correlation id, payload.
- Add an outbox table or documented outbox plan.
- Emit domain events inside database transactions.

**Learn**
- Event-driven architecture.
- At-least-once delivery.
- Why outbox prevents data loss.

**Verify**
```bash
pytest tests/ -v
```

**Done when**
- Enrollment/course events can be stored reliably.

### Day 16 - Kafka Publisher Prototype

**Implement**
- Add Kafka producer wrapper.
- Publish outbox events to Kafka.
- Add local topic naming conventions.
- Keep consumers idempotent by design.

**Learn**
- Kafka topics.
- Producers and consumers.
- Delivery semantics.

**Verify**
```bash
docker compose up -d kafka schema-registry
pytest tests/ -v
```

**Study**
- Kafka docs: https://kafka.apache.org/documentation/

**Done when**
- A local event can be published to Kafka.

### Day 17 - Celery Background Task

**Implement**
- Add Celery app configuration.
- Add one safe background task, such as analytics rollup or notification placeholder.
- Add retry policy.
- Document what belongs in Celery versus Temporal.

**Learn**
- Task queues.
- Brokers and result backends.
- Retry behavior.

**Verify**
```bash
docker compose up -d redis
pytest tests/ -v
```

**Study**
- Celery docs: https://docs.celeryq.dev/en/stable/
- Redis docs: https://redis.io/docs/latest/

**Done when**
- A task can be queued and executed locally.

### Day 18 - Temporal Course Publishing Workflow

**Implement**
- Add first Temporal workflow:
  - validate course
  - mark processing
  - prepare indexing
  - mark ready
- Add retry and timeout policies.
- Add idempotent activities.

**Learn**
- Workflow orchestration.
- Activities.
- Retries and workflow history.

**Verify**
```bash
docker compose up -d temporal temporal-ui
pytest tests/ -v
```

**Study**
- Temporal Python SDK: https://docs.temporal.io/develop/python

**Done when**
- Course publishing workflow can run locally or in a mocked test.

### Day 19 - Qdrant Vector Store Foundation

**Implement**
- Create Qdrant client wrapper.
- Define collection config.
- Add document chunk model for course content.
- Add indexing placeholder for lesson content.

**Learn**
- Embeddings.
- Vector search.
- Collections, points, vectors, payloads.

**Verify**
```bash
docker compose up -d qdrant
pytest tests/ -v
```

**Study**
- Qdrant docs: https://qdrant.tech/documentation/
- OpenAI embeddings: https://platform.openai.com/docs/guides/embeddings

**Done when**
- Course content chunks can be indexed into Qdrant in local/dev mode.

### Day 20 - LangGraph RAG Prototype

**Implement**
- Build a small LangGraph flow:
  - receive question
  - retrieve course context
  - call LLM provider
  - return answer
- Use provider abstraction for OpenAI/Groq/Anthropic.
- Add mocked tests so tests do not spend money.

**Learn**
- RAG.
- LangGraph nodes and state.
- Provider abstraction.

**Verify**
```bash
pytest tests/ -v
```

**Study**
- LangGraph docs: https://docs.langchain.com/oss/python/langgraph/overview
- OpenAI text generation: https://platform.openai.com/docs/guides/text
- Groq docs: https://console.groq.com/docs/overview
- Anthropic docs: https://docs.anthropic.com/en/docs/overview

**Done when**
- AI question flow works with mocked provider responses.

### Day 21 - Streaming AI Endpoint and Week 3 Review

**Implement**
- Add streaming response endpoint for AI Q&A.
- Add rate-limit placeholder or config.
- Document cost and latency risks.

**Learn**
- Streaming responses.
- AI cost controls.
- Safe fallback design.

**Verify**
```bash
pytest tests/ -v
```

**Done when**
- A user can ask a course question and receive a streamed response in dev mode.

---

## Week 4 - Observability, Reliability, Security, and Production Readiness

### Day 22 - Structured Logging and Request IDs

**Implement**
- Add structured logs.
- Add correlation/request ID middleware.
- Include request ID in errors and logs.

**Learn**
- Why logs are part of system design.
- Correlation IDs.

**Verify**
```bash
pytest tests/ -v
```

**Done when**
- Logs can connect a request to downstream work.

### Day 23 - OpenTelemetry and Jaeger Tracing

**Implement**
- Add OpenTelemetry FastAPI instrumentation.
- Export traces to Jaeger locally.
- Trace one API request and one background/workflow path.

**Learn**
- Traces, spans, attributes.
- Why tracing helps distributed systems.

**Verify**
```bash
docker compose up -d jaeger
```

Open Jaeger at `http://localhost:16686`.

**Study**
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
- Jaeger docs: https://www.jaegertracing.io/docs/

**Done when**
- A local request appears in Jaeger.

### Day 24 - Prometheus Metrics and Grafana Dashboard

**Implement**
- Improve `/metrics`.
- Add API latency and error counters.
- Add basic Grafana dashboard notes or provisioning.

**Learn**
- Metrics versus logs versus traces.
- Counters, histograms, labels.

**Verify**
```bash
docker compose up -d prometheus grafana
```

Open:
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

**Study**
- Prometheus getting started: https://prometheus.io/docs/prometheus/latest/getting_started/
- Grafana docs: https://grafana.com/docs/grafana/latest/

**Done when**
- API metrics are visible locally.

### Day 25 - Reliability: Retries, Idempotency, and Dead Letters

**Implement**
- Review all background paths.
- Add idempotency keys where needed.
- Add retry policies.
- Add dead-letter handling plan or implementation for failed events/tasks.

**Learn**
- Retry storms.
- Dead letter queues.
- At-least-once processing.

**Verify**
```bash
pytest tests/ -v
```

**Study**
- RabbitMQ tutorials: https://www.rabbitmq.com/tutorials

**Done when**
- Failure behavior is documented and partially implemented.

### Day 26 - Docker Images and Service Startup

**Implement**
- Add Dockerfile for the API.
- Add API service to Docker Compose.
- Add healthcheck.
- Keep local dev workflow simple.

**Learn**
- Docker images.
- Build context.
- Container healthchecks.

**Verify**
```bash
docker compose build
docker compose up -d
```

**Study**
- Dockerfile reference: https://docs.docker.com/reference/dockerfile/

**Done when**
- API can run inside Docker locally.

### Day 27 - Security Pass

**Implement**
- Review secrets handling.
- Confirm no real secrets are committed.
- Add basic rate limiting plan or implementation.
- Add CORS review.
- Add authorization tests for protected endpoints.

**Learn**
- Defense in depth.
- Secret management.
- API security basics.

**Verify**
```bash
rg -n "ghp_|github_pat_|SECRET_KEY|API_KEY|PASSWORD|TOKEN" .
pytest tests/ -v
```

**Done when**
- No real secrets are staged.
- Protected endpoints have negative tests.

### Day 28 - Performance Baseline

**Implement**
- Add simple load test script or documented command.
- Measure current API latency for health, list courses, enroll, progress update.
- Identify obvious database indexes.

**Learn**
- P95 latency.
- Connection pools.
- Indexes.

**Verify**
```bash
pytest tests/ -v
```

**Done when**
- Baseline numbers are written down.
- Follow-up performance risks are known.

### Day 29 - Documentation, ADRs, and Cleanup

**Implement**
- Update README with current run/test instructions.
- Add ADRs for:
  - service/repository pattern
  - event/outbox strategy
  - Temporal versus Celery usage
  - AI provider abstraction
- Clean TODOs and known gaps.

**Learn**
- Architecture decision records.
- How docs help future maintainers.

**Done when**
- A new engineer could run the project and understand the major decisions.

### Day 30 - Month 1 Demo and Month 2 Roadmap

**Implement**
- Create a demo flow:
  - start services
  - run migrations
  - create user
  - create course
  - add lesson
  - enroll student
  - mark progress
  - run publish workflow
  - ask AI question
  - inspect metrics/traces
- Write `month-1-review.md`.
- Draft Month 2 plan.

**Learn**
- How to present engineering work clearly.
- How to turn known gaps into a roadmap.

**Done when**
- Month 1 demo works.
- Month 2 priorities are clear.

---

## What To Learn By Topic

### Backend API
- FastAPI routes, dependencies, middleware, security, testing.
- Pydantic schemas and settings.
- REST API design and OpenAPI docs.

### Database
- PostgreSQL tables, constraints, indexes, transactions.
- SQLAlchemy async sessions and ORM relationships.
- Alembic migrations and schema review.

### Distributed Systems
- Events and event envelopes.
- Kafka topics and consumers.
- RabbitMQ queues and dead letters.
- Celery for background jobs.
- Temporal for long-running reliable workflows.

### AI
- Embeddings and vector search.
- Qdrant collections, vectors, and payloads.
- RAG flow: retrieve context, generate answer, stream result.
- LangGraph for multi-step AI workflows.
- Provider abstraction for OpenAI, Groq, and Anthropic.

### Observability
- Logs for events.
- Metrics for system health.
- Traces for request flow.
- Prometheus, Grafana, OpenTelemetry, and Jaeger.

### Security and Reliability
- JWT auth and RBAC.
- Secret hygiene.
- CORS.
- Rate limiting.
- Idempotency and retries.
- Dead letter queues.

---

## Official Study Links

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
- SQLAlchemy asyncio: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Alembic: https://alembic.sqlalchemy.org/en/latest/
- PostgreSQL: https://www.postgresql.org/docs/
- Docker Compose: https://docs.docker.com/compose/
- Celery: https://docs.celeryq.dev/en/stable/
- Redis: https://redis.io/docs/latest/
- Kafka: https://kafka.apache.org/documentation/
- RabbitMQ tutorials: https://www.rabbitmq.com/tutorials
- Temporal Python SDK: https://docs.temporal.io/develop/python
- Qdrant: https://qdrant.tech/documentation/
- LangGraph: https://docs.langchain.com/oss/python/langgraph/overview
- OpenAI text generation: https://platform.openai.com/docs/guides/text
- OpenAI embeddings: https://platform.openai.com/docs/guides/embeddings
- Groq docs: https://console.groq.com/docs/overview
- Anthropic docs: https://docs.anthropic.com/en/docs/overview
- Prometheus: https://prometheus.io/docs/prometheus/latest/getting_started/
- Grafana: https://grafana.com/docs/grafana/latest/
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
- Jaeger: https://www.jaegertracing.io/docs/

---

## Commit Strategy

Use small commits that tell the story:

```bash
git commit -m "Add initial database migration"
git commit -m "Add user service and API"
git commit -m "Add course service and API"
git commit -m "Add transactional enrollment flow"
git commit -m "Add course publishing workflow"
git commit -m "Add AI question answering prototype"
git commit -m "Add observability instrumentation"
```

Avoid one giant month-end commit. The project should be easy to review one slice at a time.

---

## Definition Of Done For Month 1

Month 1 is successful if:

- A developer can clone the repo and run the app locally.
- The database schema is managed by Alembic migrations.
- Core learner journey works through APIs.
- Critical enrollment logic is transaction-safe and tested.
- Background processing has at least one working path.
- Course publishing has a Temporal workflow foundation.
- AI Q&A has a local/dev prototype with mocked tests.
- Metrics and traces are visible locally.
- README and ADRs explain the key architecture choices.
- You can explain every major technology in the stack at a beginner-to-intermediate level.
