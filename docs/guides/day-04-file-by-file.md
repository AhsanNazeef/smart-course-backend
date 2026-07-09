# 📖 Day 4 - Complete File-by-File Breakdown

A beginner-friendly guide to everything built on Day 4, and **why** each piece exists.

> **📌 Architecture note (added 2026-07-09):** After Day 4, the project switched to a
> **microservices** architecture (monorepo, database-per-service — see
> [ADR-001](../architecture/adr-001-microservices-monorepo.md)). This guide documents the
> User domain *as originally built inside the monolith*. The good news: the
> `route → service → repository` layering below is **exactly** what each microservice uses
> internally, so everything here still applies — it just now lives inside the User
> service's own app and database instead of one shared app.

---

## 🎯 The Big Picture First

On Day 3 you got real database tables. But *who* is allowed to read and write them, and *where* does that code live? If you put database queries directly inside your API endpoints, you get a mess: business rules, SQL, and HTTP handling all tangled together in one function.

Day 4 introduces the **layered architecture** that professional backends use. You split responsibilities into three clean layers.

The restaurant analogy:
- **Router** = the **waiter**. Takes your order, brings your food. Doesn't cook. Doesn't grow vegetables.
- **Service** = the **chef**. Decides how the dish is made, enforces the recipe rules. Doesn't grow vegetables either.
- **Repository** = the **pantry/farm**. The only place that actually fetches ingredients (data).

A waiter who also farms is chaos. Each role does one job and hands off to the next. That's **separation of concerns**.

---

## What Was Built on Day 4

| File | Layer | Responsibility |
|------|-------|----------------|
| `shared/schemas/user.py` | Contract | Define what a user looks like *to the outside world* |
| `services/user_service/repository.py` | Data | The only code that runs SQL for users |
| `services/user_service/service.py` | Business logic | Domain rules (e.g. "missing user = error") |
| `services/user_service/dependencies.py` | Wiring | Connect the layers via dependency injection |
| `services/user_service/router.py` | HTTP | Turn HTTP requests into service calls |
| `main.py` | App | Register the new router |
| `tests/test_user_service.py` | Test | Test the service alone (fake repository) |
| `tests/test_user_routes.py` | Test | Test the routes alone (fake service) |

Plus empty `__init__.py` files to make the new folders into Python packages.

---

## 🔑 Core Concept: The Three Layers (read this first)

```
   HTTP request
        │
        ▼
  ┌───────────┐   "A user asked for /api/v1/users/5"
  │  ROUTER   │   Translates HTTP <-> Python. Maps errors to status codes.
  └─────┬─────┘   Knows nothing about SQL.
        │ calls
        ▼
  ┌───────────┐   "Get user 5. If they don't exist, that's an error."
  │  SERVICE  │   Business rules live here.
  └─────┬─────┘   Knows nothing about SQL or HTTP.
        │ calls
        ▼
  ┌───────────┐   "SELECT * FROM users WHERE id = 5"
  │REPOSITORY │   The ONLY place that talks to the database.
  └─────┬─────┘   Knows nothing about HTTP or business rules.
        │
        ▼
   PostgreSQL
```

### Why bother? Why not just query the DB in the route?

Imagine you wrote everything in one route function. Later you need to:
- Reuse "get user" logic from a background job (not an HTTP request) → **can't**, it's tangled with HTTP
- Test the business rule without a database → **can't**, the SQL is baked in
- Swap PostgreSQL for something else → **must** rewrite every route
- Understand what a route does → **must** read SQL + rules + HTTP all at once

Layering fixes all of this. Each layer is **independently reusable and testable**.

---

## 1️⃣ `shared/schemas/user.py` - The API Contract

**Location:** `smartcourse/shared/schemas/user.py`

**What it does:** Defines the shape of a user *as the outside world sees it*. This is different from the database model.

### Content:

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from shared.models.user import UserRole


class UserRead(BaseModel):
    """What the API returns for a user. Never includes the password hash."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    full_name: str
    role: UserRole
    is_active: bool
    avatar_url: str | None = None
    bio: str | None = None
    created_at: datetime
    updated_at: datetime
```

### 🔑 Key Concept: Model vs Schema

You now have TWO representations of a user. This is intentional:

| | **Model** (`shared/models/user.py`) | **Schema** (`shared/schemas/user.py`) |
|---|---|---|
| Tool | SQLAlchemy | Pydantic |
| Represents | A row in the database | The JSON sent to/from clients |
| Includes `hashed_password`? | ✅ Yes (needed internally) | ❌ **No** (never expose it) |
| Job | Persistence | Validation + serialization |

**Why separate them?** The most important reason is on that last row: the database model has `hashed_password`, but `UserRead` deliberately **omits it**. If you returned the raw model, you'd leak password hashes in every API response. The schema is a *safe public view*.

### 🔑 Key Concept: `from_attributes=True`

```python
model_config = ConfigDict(from_attributes=True)
```

By default, Pydantic builds itself from a dictionary. `from_attributes=True` tells it: "you can also build yourself by reading attributes off an object" — like a SQLAlchemy model.

So this works:
```python
user = User(id=5, email="a@b.com", ...)   # a SQLAlchemy object
UserRead.model_validate(user)              # reads user.id, user.email, ...
```

FastAPI does this automatically when you set `response_model=UserRead`. It takes the ORM object your service returns and converts it to the safe schema — dropping `hashed_password` in the process.

### 🔑 Key Concept: `str | None = None`

```python
avatar_url: str | None = None
```
- `str | None` means "a string OR nothing" (optional)
- `= None` is the default if not provided
- Matches the database columns that are `nullable=True`

### 🎯 Why this file matters:
It's the **contract** between your API and its clients. It guarantees responses are consistent and never leak sensitive fields.

---

## 2️⃣ `services/user_service/repository.py` - The Data Layer

**Location:** `smartcourse/services/user_service/repository.py`

**What it does:** The **only** place in the user domain that talks to the database. It speaks SQLAlchemy and returns ORM objects. No business rules, no HTTP.

### Content:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from shared.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def list(self, limit: int = 50, offset: int = 0) -> list[User]:
        result = await self._session.execute(
            select(User).order_by(User.id).limit(limit).offset(offset)
        )
        return list(result.scalars().all())
```

### Line-by-line:

```python
def __init__(self, session: AsyncSession):
    self._session = session
```
- The repository is *given* a database session when created (it doesn't create its own)
- This is **dependency injection** — the session comes from outside, which makes testing easy (you can pass a fake)
- `self._session` — the leading underscore is a Python convention meaning "private, don't touch from outside"

```python
async def get_by_id(self, user_id: int) -> User | None:
    result = await self._session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
```
- `async def` + `await` — this is async code (non-blocking; the server can handle other requests while waiting for the DB)
- `select(User).where(User.id == user_id)` — SQLAlchemy 2.0's way of writing `SELECT * FROM users WHERE id = ?`
- `await self._session.execute(...)` — actually run the query
- `.scalar_one_or_none()` — "give me exactly one User, or `None` if there isn't one"
- Return type `User | None` — honest about the fact it might not find anything

```python
async def list(self, limit: int = 50, offset: int = 0) -> list[User]:
    ... .order_by(User.id).limit(limit).offset(offset)
    return list(result.scalars().all())
```
- `limit` / `offset` — basic **pagination**. `limit=50` means "at most 50 rows"; `offset=10` means "skip the first 10". This prevents accidentally loading a million rows
- `.scalars().all()` — get all matching User objects as a list

### 🔑 Key Concept: Why isolate all SQL here?

Because if SQL only lives in the repository:
- You can find *every* user query in one file
- If a query is slow, you know exactly where to optimize
- Changing the database (or adding caching) touches only this layer
- The service and routes never need to know SQL exists

### 🎯 Why repository.py matters:
It's the single, well-defined boundary between your app and the database. Everything above it is database-agnostic.

---

## 3️⃣ `services/user_service/service.py` - The Business Logic Layer

**Location:** `smartcourse/services/user_service/service.py`

**What it does:** Holds the domain rules. It uses the repository to fetch data, then applies logic (like "a missing user is an error"). It never writes SQL.

### Content:

```python
from shared.models.user import User
from services.user_service.repository import UserRepository


class UserNotFoundError(Exception):
    """Raised when a requested user does not exist."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")


class UserService:
    def __init__(self, repository: UserRepository):
        self._repository = repository

    async def get_user(self, user_id: int) -> User:
        user = await self._repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    async def list_users(self, limit: int = 50, offset: int = 0) -> list[User]:
        return await self._repository.list(limit=limit, offset=offset)
```

### 🔑 Key Concept: Custom exceptions

```python
class UserNotFoundError(Exception):
    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")
```

- This is a **custom exception** — your own error type
- Why not just return `None`? Because the service wants to *signal a rule*: "you asked for something that doesn't exist, and that's exceptional."
- **Crucially, this is an HTTP-agnostic error.** The service doesn't know about "404" — that's an HTTP concept. It just says "not found." The *router* decides that "not found" maps to HTTP 404. This keeps the service reusable outside of HTTP (e.g. from a background job).

### 🔑 Key Concept: The service depends on the repository (not the database)

```python
def __init__(self, repository: UserRepository):
    self._repository = repository
```

The service holds a *repository*, not a database session. It says "give me something that can fetch users" — it doesn't care *how*. In tests, you hand it a **fake repository** that returns canned data, and the service works exactly the same. That's the whole point of the design.

### 🔑 Key Concept: Where do rules go?

```python
async def get_user(self, user_id: int) -> User:
    user = await self._repository.get_by_id(user_id)
    if user is None:
        raise UserNotFoundError(user_id)   # <-- the rule
    return user
```

The repository just returns `None` when nothing's found (a neutral fact). The **service** turns that fact into a decision: "None means error." Rules like this — validation, permissions, "you can't enroll twice" — all live in the service. Day 5 adds more here (duplicate-email checks, password hashing).

### 🎯 Why service.py matters:
It's the brain of the domain. Routes stay dumb, the database stays dumb, and all the interesting decisions live in one testable place.

---

## 4️⃣ `services/user_service/dependencies.py` - The Wiring

**Location:** `smartcourse/services/user_service/dependencies.py`

**What it does:** Connects the layers together using FastAPI's dependency injection, so each request gets a fully-wired `service → repository → session` chain.

### Content:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from shared.utils.database import get_db
from services.user_service.repository import UserRepository
from services.user_service.service import UserService


def get_user_repository(
    session: AsyncSession = Depends(get_db),
) -> UserRepository:
    return UserRepository(session)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(repository)
```

### 🔑 Key Concept: Dependency Injection (DI)

**Dependency injection** means: instead of a function *creating* the things it needs, those things are *handed to it*.

Look at the chain of `Depends(...)`:

```
get_db()                 ─► gives a database Session
   │ (injected into)
get_user_repository()    ─► wraps the session in a UserRepository
   │ (injected into)
get_user_service()       ─► wraps the repository in a UserService
   │ (injected into)
your route               ─► receives a ready-to-use UserService
```

FastAPI resolves this whole chain automatically for every request. Your route just says "I need a `UserService`" and FastAPI builds the entire stack behind it.

### 🔑 Key Concept: Why this makes testing trivial

Because the service is provided by `get_user_service`, a test can say:

```python
app.dependency_overrides[get_user_service] = lambda: FakeUserService(...)
```

"For this test, whenever a route asks for a user service, give it my fake instead." No database needed. This is *the* reason DI is worth it — you saw it in action in `test_user_routes.py`.

### 🎯 Why dependencies.py matters:
It's the assembly line that builds the layered stack per request, and the seam that lets tests swap any layer for a fake.

---

## 5️⃣ `services/user_service/router.py` - The HTTP Layer

**Location:** `smartcourse/services/user_service/router.py`

**What it does:** Exposes the user endpoints. Routes stay **thin**: translate HTTP, call the service, map errors to status codes. Nothing else.

### Content:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from shared.config.settings import settings
from shared.schemas.user import UserRead
from services.user_service.dependencies import get_user_service
from services.user_service.service import UserService, UserNotFoundError

router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/users", tags=["users"])


@router.get("", response_model=list[UserRead])
async def list_users(
    limit: int = 50,
    offset: int = 0,
    service: UserService = Depends(get_user_service),
):
    return await service.list_users(limit=limit, offset=offset)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    try:
        return await service.get_user(user_id)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
```

### 🔑 Key Concept: `APIRouter`

```python
router = APIRouter(prefix=f"{settings.API_V1_PREFIX}/users", tags=["users"])
```
- An `APIRouter` is a *mini-app* holding a group of related routes
- `prefix=".../users"` — every route here starts with `/api/v1/users`, so you don't repeat it
- `tags=["users"]` — groups these under a "users" heading in the `/docs` page
- Using `settings.API_V1_PREFIX` (not hardcoding `/api/v1`) means the prefix is configurable in one place

### 🔑 Key Concept: `response_model`

```python
@router.get("/{user_id}", response_model=UserRead)
```
- `response_model=UserRead` tells FastAPI: "whatever this function returns, run it through `UserRead` before sending"
- The function returns a full `User` ORM object (with `hashed_password`!), but `UserRead` **filters it down** to the safe fields
- This is your safety net against leaking sensitive data — it's enforced at the framework level

### 🔑 Key Concept: Mapping domain errors to HTTP

```python
try:
    return await service.get_user(user_id)
except UserNotFoundError:
    raise HTTPException(status_code=404, detail=f"User {user_id} not found")
```

This is the **translation** job of the router:
- The service speaks the domain language: it raises `UserNotFoundError`
- The router speaks HTTP: it catches that and raises `HTTPException(404)`
- The service stays clean (no HTTP knowledge); the router stays thin (no business logic)

This is exactly the boundary that keeps layers separate.

### 🎯 Why router.py matters:
It's the front door. Because it's thin, you can read all your endpoints at a glance and know they contain no hidden logic.

---

## 6️⃣ `main.py` - Registering the Router

**Location:** `smartcourse/main.py`

**What changed:** Two small additions to plug the user router into the app.

```python
# near the top, with the other imports
from services.user_service.router import router as user_router

# after mounting metrics
app.mount("/metrics", make_asgi_app())

# Domain routers
app.include_router(user_router)
```

### 🔑 Key Concept: `include_router`

`app.include_router(user_router)` takes all the routes defined in that mini-app and attaches them to the main application. Now `/api/v1/users` and `/api/v1/users/{user_id}` are live.

As you add more domains (courses, enrollments...), each gets its own router, and `main.py` just includes them one by one. `main.py` stays a clean table of contents instead of a 2,000-line file.

### 🎯 Why this matters:
It keeps the app modular. Each domain owns its routes; `main.py` just assembles them.

---

## 7️⃣ `tests/test_user_service.py` - Testing the Service Alone

**Location:** `smartcourse/tests/test_user_service.py`

**What it does:** Tests the service's business logic **without a database**, by passing it a fake repository.

### The fake repository:

```python
class FakeUserRepository:
    """Stand-in for UserRepository that stores users in a dict."""

    def __init__(self, users: dict | None = None):
        self._users = users or {}

    async def get_by_id(self, user_id: int):
        return self._users.get(user_id)

    async def list(self, limit: int = 50, offset: int = 0):
        rows = list(self._users.values())
        return rows[offset: offset + limit]
```

### 🔑 Key Concept: A "fake" (test double)

The real `UserRepository` talks to PostgreSQL. This fake stores users in a plain Python dict. But it has the **same method names** (`get_by_id`, `list`), so the service can't tell the difference.

This works because of **duck typing**: "if it walks like a duck and quacks like a duck, it's a duck." The service just needs *something* with a `get_by_id` method — it doesn't check the exact class.

### The tests:

```python
async def test_get_user_returns_user_when_found():
    service = UserService(FakeUserRepository({1: "alice"}))
    assert await service.get_user(1) == "alice"


async def test_get_user_raises_when_missing():
    service = UserService(FakeUserRepository())
    with pytest.raises(UserNotFoundError):
        await service.get_user(999)


async def test_list_users_respects_limit_and_offset():
    repo = FakeUserRepository({1: "a", 2: "b", 3: "c"})
    service = UserService(repo)
    first_two = await service.list_users(limit=2, offset=0)
    assert first_two == ["a", "b"]
    skip_one = await service.list_users(limit=2, offset=1)
    assert skip_one == ["b", "c"]
```

- Test 1: found → returns the user
- Test 2: missing → raises `UserNotFoundError` (using `pytest.raises`, the negative-test pattern from Day 2)
- Test 3: pagination math (`limit`/`offset`) works correctly

Notice: **no `async` markers needed** — your `pyproject.toml` has `asyncio_mode = "auto"`, so pytest runs `async def` tests automatically.

### 🎯 Why this file matters:
It proves your business logic is correct in milliseconds, with zero database setup. Fast tests get run often; slow tests get skipped.

---

## 8️⃣ `tests/test_user_routes.py` - Testing the Routes Alone

**Location:** `smartcourse/tests/test_user_routes.py`

**What it does:** Tests the HTTP layer (status codes, JSON shape, error mapping) **without a database**, by overriding the service dependency with a fake.

### The setup:

```python
class FakeUser:
    """Mimics a User ORM object for UserRead (from_attributes) to read."""
    def __init__(self, user_id: int):
        self.id = user_id
        self.email = f"user{user_id}@example.com"
        self.username = f"user{user_id}"
        self.full_name = f"User {user_id}"
        self.role = UserRole.STUDENT
        self.is_active = True
        self.avatar_url = None
        self.bio = None
        self.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        self.updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)


class FakeUserService:
    def __init__(self, users): ...
    async def get_user(self, user_id): ...      # raises UserNotFoundError if missing
    async def list_users(self, limit=50, offset=0): ...
```

- `FakeUser` has the same attributes `UserRead` expects — so `from_attributes` can read it
- `FakeUserService` mimics the real service's methods

### The override fixture:

```python
@pytest.fixture(autouse=True)
def clear_overrides():
    """Ensure dependency overrides never leak between tests."""
    yield
    app.dependency_overrides.clear()
```

- `autouse=True` — runs for *every* test in this file, no need to request it
- The code after `yield` runs *after* each test — it clears overrides so one test can't pollute another

### The tests:

```python
def test_get_user_returns_200(client):
    app.dependency_overrides[get_user_service] = lambda: FakeUserService([FakeUser(1)])
    response = client.get("/api/v1/users/1")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 1
    assert "hashed_password" not in body   # <-- proves we don't leak secrets


def test_get_missing_user_returns_404(client):
    app.dependency_overrides[get_user_service] = lambda: FakeUserService([])
    response = client.get("/api/v1/users/999")
    assert response.status_code == 404


def test_list_users_returns_array(client):
    app.dependency_overrides[get_user_service] = lambda: FakeUserService([FakeUser(1), FakeUser(2)])
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    assert len(response.json()) == 2
```

### 🔑 Key Concept: `dependency_overrides`

```python
app.dependency_overrides[get_user_service] = lambda: FakeUserService([FakeUser(1)])
```

This is FastAPI's built-in test seam. It says: "for this test, when any route asks for `get_user_service`, run *this* instead." The route runs its real code (routing, `response_model`, error mapping) but gets a fake service — so **no database is touched**.

Note the assertion `assert "hashed_password" not in body` — this test actually *proves* the `UserRead` schema does its job of hiding the password hash. That's a security guarantee, verified.

### 🎯 Why this file matters:
It tests the real HTTP behavior — status codes, JSON, the `response_model` filter — fast and without infrastructure.

---

## 🗺️ How Day 4 Fits Together

```
                         ┌──────────────── tests ────────────────┐
                         │  test_user_service.py                  │
                         │     UserService + FakeRepository       │  ← no DB
                         │  test_user_routes.py                   │
                         │     routes + FakeService (override)    │  ← no DB
                         └────────────────────────────────────────┘

   Real request flow (verified against real Postgres):

   GET /api/v1/users/5
        │
        ▼
   router.py ──Depends──► get_user_service ──Depends──► get_user_repository ──Depends──► get_db
        │                       │                              │                            │
        │  calls                │ builds                       │ builds                     │ yields
        ▼                       ▼                              ▼                            ▼
   service.get_user(5) ──► UserService ──────────► UserRepository ──────────► AsyncSession ─► PostgreSQL
        │
        │  user is None?  ──► raise UserNotFoundError ──► router maps to HTTP 404
        │  else           ──► return User ──► response_model=UserRead ──► safe JSON (no password)
```

---

## 🧠 Concepts You Learned Today

| Concept | What it means | Where you saw it |
|---------|---------------|------------------|
| **Separation of concerns** | Each layer does one job | the whole design |
| **Repository pattern** | One place owns all data access | `repository.py` |
| **Service layer** | Business rules, DB-agnostic | `service.py` |
| **Thin routes** | HTTP-only, delegate everything | `router.py` |
| **Model vs Schema** | DB row vs public API shape | `models/` vs `schemas/` |
| **`from_attributes`** | Pydantic reads from ORM objects | `schemas/user.py` |
| **`response_model`** | Filters output, hides secrets | `router.py` |
| **Dependency injection** | Dependencies are handed in, not created | `dependencies.py` |
| **Custom exception** | Domain error, HTTP-agnostic | `UserNotFoundError` |
| **Test double / fake** | Same interface, canned data | both test files |
| **Duck typing** | "Same methods" is enough | `FakeUserRepository` |
| **`dependency_overrides`** | Swap a layer for a fake in tests | `test_user_routes.py` |
| **Pagination** | `limit` / `offset` to bound results | `repository.py` |

---

## ✅ Day 4 Definition of Done — Achieved

- ✅ The `users` domain uses `route → service → repository`
- ✅ Database queries live only in the repository (never in routes)
- ✅ Tests isolate the service layer (fake repository) and the route layer (fake service) — no DB needed
- ✅ Verified end-to-end against real Postgres: `GET /users` → `200 []`, `GET /users/1` → `404`
- ✅ 15/15 tests pass (9 previous + 6 new)

---

## 🔭 What Day 5 Builds on This

Day 5 is the **User API foundation**: create-user and get-user endpoints, password hashing, input validation, and duplicate-email handling. It slots directly into the layers you just built — a `create` method on the repository, a `create_user` rule (hash password, reject duplicate email) in the service, and a `POST` route. The pattern is now the mold; new features just pour into it.

---

**Questions? Ask me to go deeper on any layer, dependency injection, or the testing approach!**
