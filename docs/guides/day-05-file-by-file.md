# 📖 Day 5 - Complete File-by-File Breakdown

A beginner-friendly guide to everything done on Day 5 — the first real **microservices**
step — and **why** each piece exists.

> **Context:** Day 5 begins the migration described in
> [ADR-001](../architecture/adr-001-microservices-monorepo.md): turning the User domain
> from a module inside one big app into its **own service with its own database**.

---

## 🎯 The Big Picture First

Days 1–4 built one app talking to one database. Day 5 is the day that app stops being "one
thing." We take the User domain and give it:

- its **own application** (its own `main.py`, runnable on its own port), and
- its **own database** (a completely separate Postgres container).

The apartment-building analogy:
- **The monolith** was one big house where everyone shares the kitchen (database).
- **Microservices** is an apartment building: each tenant (service) has their **own
  private kitchen**. Nobody cooks in anyone else's kitchen. If tenant A wants something
  from tenant B, they knock on the door (an API call) or read the notice board (events) —
  they never walk into B's kitchen and open the fridge (query B's database).

Day 5 moves the User "tenant" into its own apartment with its own kitchen.

---

## What Changed on Day 5

| File | Status | Purpose |
|------|--------|---------|
| `docker-compose.yml` | ✏️ Modified | Added a **second Postgres container** just for users |
| `.env` / `.env.example` | ✏️ Modified | Added `USER_SERVICE_*` settings |
| `services/user_service/config.py` | 🆕 New | The service's own settings |
| `services/user_service/database.py` | 🆕 New | The service's own DB engine/session |
| `services/user_service/main.py` | 🆕 New | The service's own FastAPI app |
| `services/user_service/dependencies.py` | ✏️ Modified | Use the service's own DB, not the shared one |
| `services/user_service/router.py` | ✏️ Modified | Use the service's own config/prefix |
| `main.py` (monolith) | ✏️ Modified | Removed the user routes (extracted away) |
| `tests/test_user_routes.py` | ✏️ Modified | Point tests at the new service app |

---

## 🔑 Core Concept: Database-per-Service (read this first)

This is *the* defining rule of the architecture:

> **Each service owns its own database. A service may only touch its own database.**

Before (monolith):
```
        ┌──────────── one app ────────────┐
        │  users  courses  enrollments ... │
        └───────────────┬──────────────────┘
                        │  (everything queries...)
                  ┌─────▼─────┐
                  │ one DB    │  smartcourse @ 5432
                  └───────────┘
```

After Day 5 (User extracted):
```
   ┌── user service ──┐        ┌──── monolith (rest) ────┐
   │  users           │        │  courses  enrollments... │
   └────────┬─────────┘        └───────────┬──────────────┘
            │                              │
      ┌─────▼─────┐                  ┌─────▼─────┐
      │ users_db  │  @ 5433          │smartcourse│  @ 5432
      └───────────┘                  └───────────┘
      (only user service              (user service can NEVER
       touches this)                   touch this, and vice-versa)
```

**Why do this?** Because isolated databases are what make services *independent*:
- You can deploy, scale, or rewrite the User service without touching anyone else.
- A bad query in one service can't lock or corrupt another's data.
- Each service's schema can evolve on its own timeline.

**The cost** (accepted): you can no longer do a SQL `JOIN` across services. If enrollment
needs a user's name, it must **ask** the User service (API/event), not join to its table.
That trade-off is the whole point — and Day 6+ will deal with it.

---

## 1️⃣ `docker-compose.yml` - A Second Database Container

**Location:** `smartcourse/docker-compose.yml`

**What changed:** Added a brand-new Postgres container that belongs *only* to the User
service.

### The new service block:

```yaml
  # User Service Database (database-per-service: owned only by user_service)
  user-postgres:
    image: postgres:15-alpine
    container_name: smartcourse-user-postgres
    environment:
      POSTGRES_USER: user_service
      POSTGRES_PASSWORD: user_service_password
      POSTGRES_DB: users_db
    ports:
      - "5433:5432"
    volumes:
      - user_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user_service"]
      interval: 10s
      timeout: 5s
      retries: 5
```

And a new named volume:
```yaml
volumes:
  postgres_data:
  user_postgres_data:   # <-- new
  redis_data:
  ...
```

### 🔑 Key Concept: The port mapping `"5433:5432"`

This is the most important line to understand.

```
"5433:5432"
   │    │
   │    └── port INSIDE the container (Postgres always listens on 5432)
   └─────── port on YOUR machine (the host)
```

- The monolith's Postgres already uses host port **5432**.
- Two programs can't share the same host port, so this new container maps to host port
  **5433**.
- Inside its container it's still 5432 (that never changes), but from your laptop you reach
  it at `localhost:5433`.

So now you have **two separate Postgres servers** running side by side:
- `localhost:5432` → the monolith's `smartcourse` database
- `localhost:5433` → the user service's `users_db` database

### 🔑 Key Concept: Separate credentials & volume

- **Different user/password** (`user_service` / `user_service_password`): the User service
  has its own login. The monolith's credentials can't open this database.
- **Its own volume** (`user_postgres_data`): its data is stored separately on disk. Deleting
  one database's data doesn't touch the other.

### 🎯 Why this matters:
This is where "database-per-service" stops being a diagram and becomes real infrastructure.
Two containers, two ports, two credential sets, two volumes — genuinely isolated.

---

## 2️⃣ `.env` / `.env.example` - The Service's Settings

**Location:** `smartcourse/.env` and `smartcourse/.env.example`

**What changed:** Added a `USER_SERVICE_*` block.

```bash
# ---------------------------------------------------------------------------
# User Service (microservices migration - owns its own database)
# ---------------------------------------------------------------------------
USER_SERVICE_APP_NAME=SmartCourse User Service
USER_SERVICE_DEBUG=True
USER_SERVICE_PORT=8001
USER_SERVICE_DATABASE_URL=postgresql+asyncpg://user_service:user_service_password@localhost:5433/users_db
```

### 🔑 Key Concept: A new prefix `USER_SERVICE_`

The monolith uses the `SMARTCOURSE_` prefix. The User service uses its own `USER_SERVICE_`
prefix. This keeps each service's configuration clearly separated — you can tell at a glance
which setting belongs to which service, and they can never collide.

### Decode the database URL:
```
postgresql+asyncpg://user_service:user_service_password@localhost:5433/users_db
└────┬─────┘ └──┬──┘  └─────┬────┘ └────────┬────────┘  └───┬───┘ └──┬─┘ └───┬──┘
 postgres    async     username        password         host    port   database
             driver
```

Notice **`5433`** and **`users_db`** — this URL points at the *new* container, not the
monolith's database. That single line is what wires the service to its own kitchen.

### 🎯 Why this matters:
Configuration is how a service knows *which* database is "its own." Getting this URL right
is what enforces the isolation at runtime.

---

## 3️⃣ `services/user_service/config.py` - The Service's Own Settings

**Location:** `smartcourse/services/user_service/config.py`

**What it does:** Loads the `USER_SERVICE_*` settings into a typed object — the service's
private configuration, completely separate from the monolith's `settings`.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class UserServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="USER_SERVICE_",   # <-- reads USER_SERVICE_* only
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "SmartCourse User Service"
    DEBUG: bool = True
    PORT: int = 8001
    API_PREFIX: str = "/api/v1"

    DATABASE_URL: str                 # required - the service's own DB
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 5
```

### 🔑 Key Concept: Why not reuse the monolith's settings?

A microservice must be **self-contained**. If the User service imported the monolith's
`SMARTCOURSE_` settings, it would depend on the monolith to exist — which defeats the whole
point of being independent. So it gets its own settings class reading its own prefix.

This is the same Pydantic Settings pattern from Day 2, just scoped to one service. It even
reuses the **friendly config error** idea (from Day 2): if `USER_SERVICE_DATABASE_URL` is
missing, it prints a clear message and exits instead of dumping a raw traceback.

### 🎯 Why this matters:
Each service owning its own config is a small thing that has a big consequence: the service
can be lifted out and run anywhere, because it doesn't reach into shared global state.

---

## 4️⃣ `services/user_service/database.py` - The Service's Own Engine

**Location:** `smartcourse/services/user_service/database.py`

**What it does:** Creates the database engine and session that connect **only** to
`users_db`. This is the service's private door to its private kitchen.

```python
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from services.user_service.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,          # <-- the users_db URL, nothing else
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False, ...)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def check_connection() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
```

### 🔑 Key Concept: This mirrors the monolith's `shared/utils/database.py` — on purpose

It's almost identical to the Day 1 database setup, but pointed at a **different URL**. That
duplication is *intentional* in microservices: each service owns its own copy so it has no
shared dependency. A little repeated boilerplate is the price of independence.

### 🔑 Key Concept: `check_connection()` and `SELECT 1`

```python
async def check_connection() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
```

`SELECT 1` is the simplest possible query — it asks the database to return the number 1. It
touches **no tables**, so it works even before any tables exist (which is the case on Day 5,
before Day 6's migration). It's a pure "are you there and can I talk to you?" probe. The
app runs this at startup to prove it can reach its own database.

### 🎯 Why this matters:
This file is the runtime enforcement of "own database only." The engine physically cannot
connect anywhere except the URL it was given.

---

## 5️⃣ `services/user_service/main.py` - The Service's Own App

**Location:** `smartcourse/services/user_service/main.py`

**What it does:** A complete, standalone FastAPI application for just the User service —
runnable on its own, independent of the monolith.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from services.user_service.config import settings
from services.user_service.database import check_connection, engine
from services.user_service.router import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME}...")
    try:
        await check_connection()
        logger.info("User service database connection OK")
    except Exception as exc:
        logger.warning(f"User service database not reachable at startup: {exc}")
    yield
    await engine.dispose()


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME, "version": "0.1.0"}


app.include_router(user_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("services.user_service.main:app", host="0.0.0.0", port=settings.PORT, ...)
```

### 🔑 Key Concept: One repo, many apps

This is the second `main.py` in the project (the monolith has one too). That's the essence
of **monorepo microservices**: one git repository, but multiple independent applications
inside it. You run this one with:
```bash
uvicorn services.user_service.main:app --port 8001
```
The monolith runs separately on port 8000. Two apps, two ports, two databases.

### 🔑 Key Concept: The lifespan DB probe (graceful)

```python
try:
    await check_connection()
    logger.info("User service database connection OK")
except Exception as exc:
    logger.warning(f"... not reachable at startup: {exc}")
```

At startup the app tries to reach its database and logs the result. Note it **catches** the
error and only warns — it doesn't crash. Why? So the app (and its `/health`) still boots
even if the database is temporarily down. This is a small resilience habit: don't let a
dependency being briefly unavailable take your whole service down at boot.

### 🎯 Why this matters:
This file is the "apartment" — a self-sufficient app that has everything it needs (config,
database, routes) and depends on no other service to start.

---

## 6️⃣ `services/user_service/dependencies.py` - Wire to the Service's Own DB

**Location:** `smartcourse/services/user_service/dependencies.py`

**What changed:** One import line — but a meaningful one.

```python
# Before (Day 4): used the monolith's shared database
from shared.utils.database import get_db

# After (Day 5): uses the service's OWN database
from services.user_service.database import get_db
```

### 🔑 Key Concept: The seam paid off

Remember Day 4's dependency injection? Because the repository received its session through
`get_db` (rather than creating it), switching the service to its own database was a
**one-line change**. Nothing else in the repository or service had to change. That's the
reward for the layered design: swapping the database out was trivial.

### 🎯 Why this matters:
It shows that good structure isn't academic — it made a real architectural migration a
one-line edit instead of a rewrite.

---

## 7️⃣ `services/user_service/router.py` - Use the Service's Own Config

**Location:** `smartcourse/services/user_service/router.py`

**What changed:** The router now reads its prefix from the *service's* config, not the
monolith's.

```python
# Before: depended on the monolith's shared settings
from shared.config.settings import settings
router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/users", ...)

# After: depends only on the service's own config
from services.user_service.config import settings
router = APIRouter(prefix=f"{settings.API_PREFIX}/users", ...)
```

### 🔑 Key Concept: Cutting the last cord to the monolith

Previously the router imported `shared.config.settings` — which means it (and therefore the
whole service) needed the monolith's `SMARTCOURSE_` environment to even import. Switching to
the service's own config **cuts that dependency**. Now the User service imports nothing that
requires the monolith to exist.

### 🎯 Why this matters:
Independence is death-by-a-thousand-imports: every shared import is a hidden coupling.
Removing this one brings the service closer to truly standing alone.

---

## 8️⃣ `main.py` (monolith) - Remove the Extracted Routes

**Location:** `smartcourse/main.py`

**What changed:** The user router was removed — the monolith no longer serves users.

```python
# Removed the import:
# from services.user_service.router import router as user_router

# Replaced the include with a note:
app.mount("/metrics", make_asgi_app())

# NOTE: The user domain has been extracted into its own service
# (services/user_service). It is no longer served by this app; run it with:
#   uvicorn services.user_service.main:app --port 8001
# Remaining domains will be extracted the same way (see ADR-001).
```

### 🔑 Key Concept: Extraction means *removing*, not copying

A migration isn't done when the new thing exists — it's done when the old thing is **gone**.
Leaving the user routes in both places would mean two apps serving users against two
databases: confusing and wrong. Removing them from the monolith makes the User service the
single source of truth for users.

### 🎯 Why this matters:
This is the moment the monolith shrinks. Over the coming days it keeps shrinking as each
domain leaves, until eventually it disappears entirely.

---

## 9️⃣ `tests/test_user_routes.py` - Point Tests at the New App

**Location:** `smartcourse/tests/test_user_routes.py`

**What changed:** The tests now import the User service's app and build their own client.

```python
# Before: tested via the monolith
from main import app

# After: test via the User service's own app
from fastapi.testclient import TestClient
from services.user_service.main import app

@pytest.fixture
def client():
    """Test client for the User service app (overrides the monolith client)."""
    with TestClient(app) as test_client:
        yield test_client
```

### 🔑 Key Concept: Tests follow the code

When code moves, its tests move with it. The user routes now live in the User service app,
so the route tests target *that* app. A local `client` fixture (defined in this file)
overrides the monolith `client` from `conftest.py`.

### 🔑 Key Concept: Still no database needed

These tests still override `get_user_service` with a fake, so they never touch `users_db`.
The `with TestClient(app)` triggers the service's lifespan (the DB probe), but that's
wrapped in try/except — so even the startup probe can't make the tests depend on a running
database. Fast, isolated tests survive the migration intact.

### 🎯 Why this matters:
The safety net moves with the code, so you keep the same confidence after the migration that
you had before it.

---

## 🗺️ How Day 5 Fits Together

```
   Run the monolith            Run the user service
   (port 8000)                 (port 8001)
        │                            │
   main.py (monolith)          services/user_service/main.py
   - health, /api/v1           - health
   - NO user routes            - user router (/api/v1/users)
        │                            │
        ▼                            ▼  (config.py -> database.py)
  ┌───────────┐                ┌───────────┐
  │smartcourse│ @5432          │ users_db  │ @5433
  └───────────┘                └───────────┘
       ▲                             ▲
       │  (two SEPARATE Postgres containers — neither can see the other)
```

The verified boot sequence for the User service:
```
Starting SmartCourse User Service...
User service database connection OK      ← SELECT 1 against users_db (5433) succeeded
GET /health -> 200
```

---

## 🧠 Concepts You Learned Today

| Concept | What it means | Where you saw it |
|---------|---------------|------------------|
| **Database-per-service** | Each service owns its own DB | the whole day |
| **Port mapping** | `host:container` (5433:5432) | docker-compose |
| **Service isolation** | Separate creds, volume, port | docker-compose |
| **Per-service config** | Own settings, own env prefix | config.py |
| **Self-contained service** | Depends on no other service to run | config/router changes |
| **One repo, many apps** | Monorepo microservices | second main.py |
| **Graceful startup probe** | Check DB but don't crash on failure | main.py lifespan |
| **`SELECT 1`** | Tableless "are you there?" query | database.py |
| **Extraction = removal** | The old copy must go | monolith main.py |
| **Tests follow the code** | Move tests with what they test | test_user_routes.py |
| **The DI payoff** | Swapping the DB was one line | dependencies.py |

---

## ✅ Day 5 Definition of Done — Achieved

- ✅ A dedicated `user-postgres` container runs on port 5433 (Up, healthy)
- ✅ The User service is its own app with its own config and database engine
- ✅ It boots independently and connects to **its own** database (`SELECT 1` OK)
- ✅ `/health` returns 200
- ✅ User routes removed from the monolith (truly extracted)
- ✅ 15/15 tests pass — the migration broke nothing

---

## 🔭 What Day 6 Builds on This

The `users_db` database exists but is **empty** — no tables yet. Day 6 moves the `User`
model *into* the service, gives the service its **own Alembic migrations**, and creates the
`users` table inside `users_db`. After that, the real DB-backed `/users` endpoints work
end-to-end against the service's own database — and the `User` model leaves `shared/models`
for good, since sharing data models across services breaks isolation.

---

**Questions? Ask me to go deeper on database-per-service, port mapping, or why each service
needs its own everything!**
