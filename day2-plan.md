# SmartCourse — Day 2 Detailed Build Plan

> **Day 2 theme (from plan.md):** *Settings, Application Structure, and Health Checks*
>
> This is the expanded, copy-paste-friendly version. Follow the steps top to bottom.

---

## 🎯 Goal of Day 2

Yesterday you built the *scaffold* (the app, models, infra). Today you make it **trustworthy**:

1. **Prove the app actually starts and responds** — with an automated test suite.
2. **Make configuration mistakes obvious** — a clear error when an env var is missing, instead of a cryptic stack trace.
3. **Document every `SMARTCOURSE_` setting** — so a new developer knows what to fill in.

> **Senior habit you're learning:** *Before adding new features, make the thing you already built verifiable.* Tests are how you stop being afraid to change code.

---

## ✅ Day 2 Deliverables (Definition of Done)

- [ ] `pytest tests/ -v` runs and passes
- [ ] Tests cover `/health`, `/`, and `/api/v1`
- [ ] A test proves the app **starts up** (lifespan runs) without crashing
- [ ] Missing/invalid config produces a **human-readable** error
- [ ] Every required `SMARTCOURSE_` variable is documented in a table
- [ ] One clean commit: `git commit -m "Add app startup tests and friendly settings validation"`

---

## 🔍 Prerequisites Check (2 minutes)

Run these first. They tell you where you're starting from.

```bash
python --version                 # should be 3.11+  (you have 3.14 ✓)
python -c "from main import app; print('import OK')"
ls tests/                        # currently empty — you'll fill it today
```

If `import OK` prints, you're good to go.

---

## Step 1 — Install the testing tools (10 min)

Right now **pytest is not installed**, and it's missing from `requirements.txt` (it only lives in `pyproject.toml`'s dev section). Fix both.

### 1a. Install the tools

```bash
pip install pytest pytest-asyncio pytest-cov httpx
```

> **Why each one?**
> - `pytest` — the test runner
> - `pytest-asyncio` — lets you test `async def` functions (your `pyproject.toml` sets `asyncio_mode = "auto"`, so this is required or pytest complains)
> - `pytest-cov` — coverage reports (your `pyproject.toml` `addopts` already asks for `--cov`, so this is required for `pytest` to run at all)
> - `httpx` — the HTTP client FastAPI's `TestClient` uses under the hood

### 1b. Record them so teammates get them too

Create a file **`requirements-dev.txt`** in the project root:

```text
# Development & testing dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.25.0
```

> **Why a separate file?** Production servers shouldn't install test tools. Keeping `requirements-dev.txt` separate from `requirements.txt` means production stays lean. (These are already listed in `pyproject.toml [project.optional-dependencies] dev`; this file is the simple, explicit mirror.)

**Verify Step 1:**
```bash
pytest --version        # prints pytest 8.x
```

---

## Step 2 — Make `tests/` a real test package (5 min)

### 2a. Create `tests/__init__.py` (empty file)

```bash
# creates an empty file so Python treats tests/ as a package
touch tests/__init__.py
```

### 2b. Create `tests/conftest.py`

`conftest.py` holds **fixtures** — reusable setup that pytest injects into your tests automatically.

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """
    A test client for the FastAPI app.

    Using `with TestClient(app)` (a context manager) triggers the app's
    lifespan events — so this also proves the app STARTS UP cleanly.
    """
    with TestClient(app) as test_client:
        yield test_client
```

> **What's a fixture?** Any test function that has a parameter named `client` will automatically receive this object. No imports, no manual setup — pytest wires it up by name. This is dependency injection for tests.
>
> **Why the `with` block matters:** `TestClient(app)` as a context manager runs your `lifespan()` startup code (and shutdown on exit). So every test using `client` is implicitly a startup smoke test.

---

## Step 3 — Write the health & startup tests (20 min)

Create `tests/test_health.py`:

```python
# tests/test_health.py
"""Tests for the app's core endpoints and startup."""


def test_app_starts_up(client):
    """If this fixture builds without raising, lifespan startup succeeded."""
    # Reaching here means TestClient entered the `with` block = app started.
    assert client is not None


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["app_name"] == "SmartCourse"
    assert body["version"] == "0.1.0"
    assert "environment" in body


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Welcome to SmartCourse API"
    assert body["docs"] == "/docs"


def test_api_v1_root(client):
    response = client.get("/api/v1")

    assert response.status_code == 200
    body = response.json()
    # The v1 root advertises the endpoint groups the API will expose
    assert "endpoints" in body
    for group in ("courses", "users", "enrollments", "analytics", "ai"):
        assert group in body["endpoints"]


def test_unknown_route_returns_404(client):
    """A route that doesn't exist should 404 — proves routing is sane."""
    response = client.get("/this-does-not-exist")
    assert response.status_code == 404


def test_metrics_endpoint_exists(client):
    """Prometheus metrics should be mounted and scrapeable."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus exposition format is plain text
    assert "text/plain" in response.headers["content-type"]
```

> **How to read a test:**
> - **Arrange** — set things up (the `client` fixture already did this)
> - **Act** — do the thing (`client.get(...)`)
> - **Assert** — check the result (`assert ...`)
>
> If any `assert` is false, the test fails and pytest shows you exactly which line and what the actual value was.

**Verify Step 3:**
```bash
pytest tests/ -v
```
You should see 6 green `PASSED` lines.

---

## Step 4 — Make settings errors human-readable (25 min)

### The problem

Your [shared/config/settings.py](shared/config/settings.py) has ~10 **required** variables (no default): `DATABASE_URL`, `REDIS_URL`, `RABBITMQ_URL`, `KAFKA_BOOTSTRAP_SERVERS`, `SECRET_KEY`, etc.

If one is missing, Python currently throws a wall of Pydantic traceback that a beginner can't parse. Today you turn that into a clear message.

### The fix

Open [shared/config/settings.py](shared/config/settings.py). At the bottom, replace the `get_settings()` function with this version:

```python
import sys
from pydantic import ValidationError


@lru_cache()
def get_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        _print_friendly_settings_error(exc)
        raise SystemExit(1)


def _print_friendly_settings_error(exc: ValidationError) -> None:
    """Turn a Pydantic ValidationError into a readable config message."""
    missing = [
        str(err["loc"][0])
        for err in exc.errors()
        if err["type"] == "missing"
    ]
    lines = [
        "",
        "=" * 64,
        "  CONFIGURATION ERROR — SmartCourse cannot start",
        "=" * 64,
    ]
    if missing:
        lines.append("  Missing required environment variables:")
        for field in missing:
            lines.append(f"    - SMARTCOURSE_{field}")
        lines.append("")
        lines.append("  Fix it:")
        lines.append("    1. Copy the template:   cp .env.example .env")
        lines.append("    2. Fill in the values above in your new .env file")
    else:
        lines.append("  Some settings are invalid:")
        for err in exc.errors():
            field = ".".join(str(p) for p in err["loc"])
            lines.append(f"    - SMARTCOURSE_{field}: {err['msg']}")
    lines.append("=" * 64)
    print("\n".join(lines), file=sys.stderr)
```

> **What this does:**
> - `ValidationError` is what Pydantic raises when required fields are missing.
> - We inspect `exc.errors()` (a list of dicts describing each problem).
> - Errors of type `"missing"` mean a required var wasn't provided.
> - We print a clean box pointing the developer to `.env.example`.
> - `raise SystemExit(1)` stops the program with a non-zero exit code (the Unix convention for "something went wrong").

### See it work (safe test)

Temporarily rename your `.env` and try to import — you should get the friendly box, not a traceback:

```bash
mv .env .env.backup
python -c "from shared.config.settings import get_settings; get_settings.cache_clear(); get_settings()"
# ^ you should see the CONFIGURATION ERROR box
mv .env.backup .env      # ⚠️ restore it immediately!
```

> **Important:** put `.env` back right after. Everything (including your tests) needs it.

---

## Step 5 — Document every `SMARTCOURSE_` variable (20 min)

Create **`docs/configuration.md`** (make the `docs/` folder if needed):

```bash
mkdir -p docs
```

Then fill `docs/configuration.md` with a table like this (one row per setting in `settings.py`). Mark which are **required** (no default) vs **optional** (has default):

```markdown
# Configuration Reference

All settings use the `SMARTCOURSE_` prefix and load from `.env`.
Copy `.env.example` to `.env` and fill in the required values.

## Required (app won't start without these)

| Variable | Example | Purpose |
|---|---|---|
| `SMARTCOURSE_DATABASE_URL` | `postgresql+asyncpg://smartcourse:smartcourse_password@localhost:5432/smartcourse` | PostgreSQL connection |
| `SMARTCOURSE_REDIS_URL` | `redis://localhost:6379/0` | Cache / sessions |
| `SMARTCOURSE_RABBITMQ_URL` | `amqp://smartcourse:smartcourse_password@localhost:5672/` | Task broker |
| `SMARTCOURSE_KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Event streaming |
| `SMARTCOURSE_KAFKA_SCHEMA_REGISTRY_URL` | `http://localhost:8081` | Kafka schemas |
| `SMARTCOURSE_TEMPORAL_HOST` | `localhost` | Workflow engine host |
| `SMARTCOURSE_SECRET_KEY` | `change-me-to-a-long-random-string` | Signs JWT tokens |
| `SMARTCOURSE_QDRANT_URL` | `http://localhost:6333` | Vector DB |
| `SMARTCOURSE_CELERY_BROKER_URL` | `amqp://...` | Celery broker |
| `SMARTCOURSE_CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Celery results |

## Optional (have sensible defaults)

| Variable | Default | Purpose |
|---|---|---|
| `SMARTCOURSE_APP_ENV` | `development` | Environment name |
| `SMARTCOURSE_DEBUG` | `True` | Verbose logs / auto-reload |
| `SMARTCOURSE_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT lifetime |
| `SMARTCOURSE_DEFAULT_LLM_PROVIDER` | `openai` | Which AI provider |
| `SMARTCOURSE_RATE_LIMIT_PER_MINUTE` | `100` | API rate limit |

> Tip: to regenerate the "required" list, look in `shared/config/settings.py`
> for any field **without** a default value — those are the required ones.
```

> **Why this matters:** Configuration is the #1 reason "it works on my machine but not yours." A documented table removes the guesswork.

---

## 🧪 Final Verification (run everything)

```bash
# 1. All tests pass
pytest tests/ -v

# 2. App still imports
python -c "from main import app; print('import OK')"

# 3. Coverage report generated (from pyproject addopts)
#    open htmlcov/index.html in a browser to see what's tested
```

Expected: all tests green, `import OK`, and an `htmlcov/` folder appears.

---

## 📦 Commit Your Work

```bash
git add tests/ requirements-dev.txt docs/configuration.md shared/config/settings.py
git status                      # review what you're committing
git commit -m "Add app startup tests and friendly settings validation"
```

> **Don't commit:** `.env`, `htmlcov/`, `.pytest_cache/`, `__pycache__/`. Check they're in `.gitignore`.

---

## 📚 Learn (the "why" behind today)

Spend 30–45 min on these. You just used all three concepts.

1. **Pydantic Settings** — how env vars become typed Python objects
   https://docs.pydantic.dev/latest/concepts/pydantic_settings/
2. **FastAPI lifespan events** — the startup/shutdown code your test exercises
   https://fastapi.tiangolo.com/advanced/events/
3. **FastAPI testing (`TestClient`)** — how to test an API without running a server
   https://fastapi.tiangolo.com/tutorial/testing/
4. **pytest fixtures** — the `conftest.py` injection you just wrote
   https://docs.pytest.org/en/stable/how-to/fixtures.html

**Key ideas to be able to explain out loud by end of day:**
- What is a fixture, and how did pytest know to pass `client` to your tests?
- Why does `with TestClient(app)` prove the app *starts up*, not just that routes exist?
- What is a `ValidationError` and when does Pydantic raise it?
- Why keep `requirements-dev.txt` separate from `requirements.txt`?

---

## 🧯 Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `unknown config option: asyncio_mode` | `pytest-asyncio` not installed | `pip install pytest-asyncio` |
| `unrecognized arguments: --cov` | `pytest-cov` not installed | `pip install pytest-cov` |
| `ModuleNotFoundError: main` | Running pytest from wrong dir | Run from project root (where `main.py` is) |
| Tests fail with config error | `.env` missing | `cp .env.example .env` |
| `ImportError: httpx` | `httpx` not installed | `pip install httpx` |

---

## 🔭 What Day 3 will build on this

Tomorrow (Day 3) you generate your **first Alembic migration** from the models you already have. Today's tests become your safety net: after the migration, you re-run `pytest` to confirm nothing broke.
