# 📖 Day 1 - Complete File-by-File Breakdown

A beginner-friendly guide to understanding every file created on Day 1 and **why** each one exists.

---

## 🎯 The Big Picture First

Think of building a backend like building a house:
- **`main.py`** = The front door (entry point)
- **`docker-compose.yml`** = The infrastructure (electricity, water, internet)
- **`shared/config/settings.py`** = The thermostat (configuration)
- **`shared/models/`** = The blueprint (database structure)
- **`shared/utils/database.py`** = The plumbing (how water flows)
- **`pyproject.toml`** = The toolbox (what tools you have)
- **`.env.example`** = The address book (settings for different locations)

Now let's look at each one in detail.

---

## 1️⃣ `main.py` - The Application Entry Point

**Location:** `smartcourse/main.py`

**What it does:** This is where your API application starts. It's like the main door to your house.

### Content Breakdown:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app
from shared.config.settings import settings
import logging
```

**Imports explained:**
- `FastAPI` - The web framework (like Django but faster, modern)
- `CORSMiddleware` - Security middleware that controls who can access your API
- `asynccontextmanager` - A Python pattern for "before and after" events (startup/shutdown)
- `prometheus_client` - For collecting metrics (how many requests, how fast, errors)
- `settings` - The configuration we defined elsewhere

### Key Sections:

#### 1. **Logging Setup**
```python
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```
**Why?** So you can see what's happening when the app runs. In development (DEBUG=True), you see everything. In production, you only see warnings and errors.

#### 2. **Lifespan Context Manager**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.APP_NAME}...")
```

**Why?** This runs code when the app starts and stops.
- **On startup:** You'd typically connect to the database, start background workers
- **On shutdown:** Clean up connections, save state
- The `yield` is the "pause" - everything before runs at startup, everything after runs at shutdown

#### 3. **Create FastAPI App**
```python
app = FastAPI(
    title=settings.APP_NAME,
    description="SmartCourse - Intelligent Course Delivery Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)
```

**Why?** FastAPI needs basic info:
- `title` - What's this API called?
- `description` - What does it do?
- `version` - What version is this?
- `docs_url` - Where to find interactive docs (Swagger)
- `lifespan` - Use the startup/shutdown code we defined above

#### 4. **CORS Middleware**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Why?** By default, browsers block requests from `https://frontend.com` to `https://api.com` (different domains). This middleware says "Actually, I trust these origins."
- `allow_origins` - Which websites can call this API?
- `allow_credentials` - Can they send cookies/auth tokens?
- `allow_methods` - Which HTTP methods? (GET, POST, PUT, DELETE, etc.)
- `allow_headers` - Which headers can they send?

#### 5. **Prometheus Metrics**
```python
app.mount("/metrics", make_asgi_app())
```

**Why?** Mount Prometheus at `/metrics`. When you visit `http://localhost:8000/metrics`, you get data like:
- How many requests? How fast? How many errors?
- Memory usage, CPU usage, etc.

#### 6. **Endpoints**
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": "0.1.0"
    }
```

**Why?** The `/health` endpoint answers: "Is your app alive?"
- Load balancers check this regularly
- Docker Compose healthchecks use this
- Monitoring systems use this to detect if the app crashed

### 🎯 Why main.py matters:
Without it, there's no app. This is the entry point that ties everything together.

---

## 2️⃣ `shared/config/settings.py` - Configuration Management

**Location:** `smartcourse/shared/config/settings.py`

**What it does:** Centralizes all configuration (database URLs, API keys, ports, etc.) in one place.

### Key Concept: Environment Variables

Your app needs to know:
- Which database to use? (localhost for dev, AWS RDS for production)
- What secret key to sign JWTs? (different per environment for security)
- Which LLM provider? (OpenAI, Anthropic, Groq)

Instead of hardcoding these, you read them from **environment variables**.

### Content Breakdown:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SMARTCOURSE_",
        case_sensitive=True,
        extra="ignore",
    )
```

**What this does:**
- `env_file=".env"` - Read settings from a `.env` file in the project root
- `env_prefix="SMARTCOURSE_"` - Only look for variables starting with `SMARTCOURSE_`
  - So you look for `SMARTCOURSE_DATABASE_URL`, not just `DATABASE_URL`
  - This prevents conflicts if you run multiple apps
- `case_sensitive=True` - `SMARTCOURSE_DEBUG` and `smartcourse_debug` are different
- `extra="ignore"` - If there are settings in `.env` you don't use, ignore them

### Settings Groups:

**1. Application Settings**
```python
APP_NAME: str = "SmartCourse"          # App name
APP_ENV: str = "development"           # development / staging / production
DEBUG: bool = True                      # Show detailed error messages?
API_V1_PREFIX: str = "/api/v1"         # All v1 endpoints start with /api/v1
```

**Why?** 
- `APP_ENV` helps you behave differently in dev vs production (e.g., less strict CORS in dev)
- `DEBUG=True` in development shows full error messages. `DEBUG=False` in production hides them from users
- `API_V1_PREFIX` is set in one place, not hardcoded everywhere

**2. Database Settings**
```python
DATABASE_URL: str                       # postgresql+asyncpg://user:pass@host:port/db
DATABASE_POOL_SIZE: int = 20           # How many connections to keep open?
DATABASE_MAX_OVERFLOW: int = 10        # If all 20 are busy, open up to 10 more
```

**Why?**
- `DATABASE_URL` tells SQLAlchemy where the database is
- `postgresql+asyncpg://` = Use PostgreSQL with async driver
- `pool_size=20` = If 20 requests come in at once, 20 can talk to the database. If 21st comes, it waits
- `max_overflow=10` = If we're desperate, temporarily open 10 more connections (total 30)

**3. Redis (Cache)**
```python
REDIS_URL: str                          # redis://localhost:6379/0
REDIS_CACHE_TTL: int = 3600            # Cache expires after 1 hour
```

**Why?**
- Redis is fast, in-memory storage for caching
- If a query takes 5 seconds, cache the result for 1 hour
- Next 3,600 requests for that data take 0.001 seconds

**4. RabbitMQ (Messaging)**
```python
RABBITMQ_URL: str                       # amqp://user:pass@host:port/
RABBITMQ_TASK_QUEUE: str = "smartcourse_tasks"  # Queue name
```

**Why?**
- RabbitMQ is a message broker (like a post office for tasks)
- When a request comes in to "send email", you don't send it immediately
- Instead: put a message in the queue → return quickly to user → background worker picks it up and sends the email

**5. Kafka (Event Streaming)**
```python
KAFKA_BOOTSTRAP_SERVERS: str            # localhost:9092
KAFKA_CONSUMER_GROUP: str = "smartcourse_group"
KAFKA_SCHEMA_REGISTRY_URL: str
```

**Why?**
- Kafka is like RabbitMQ but for "events" (not one-off tasks, but streams of events)
- Example: "Student enrolled in course" → event goes to Kafka → multiple services react to it

**6. Temporal (Workflows)**
```python
TEMPORAL_HOST: str                      # localhost
TEMPORAL_PORT: int = 7233
TEMPORAL_NAMESPACE: str = "default"
TEMPORAL_TASK_QUEUE: str = "smartcourse_workflows"
```

**Why?**
- Temporal handles long-running processes with retries and failure recovery
- Example: "Publish a course" might take 10 minutes with multiple steps
- If step 3 fails, Temporal automatically retries it

**7. Security Settings**
```python
SECRET_KEY: str                         # Used to sign JWTs (authentication tokens)
ALGORITHM: str = "HS256"                # Which algorithm to use for signing?
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30   # JWT expires after 30 minutes
```

**Why?**
- `SECRET_KEY` is like a signature stamp - if the signature is faked, we reject the token
- `HS256` = HMAC using SHA-256 (a cryptographic algorithm)
- 30 minutes = Short lived, so if someone steals it, it's only good for 30 min

**8. AI/LLM Settings**
```python
OPENAI_API_KEY: Optional[str] = None
ANTHROPIC_API_KEY: Optional[str] = None
GROQ_API_KEY: Optional[str] = None
DEFAULT_LLM_PROVIDER: str = "openai"
```

**Why?**
- Your app will call external AI APIs
- Each provider needs an API key
- `Optional[str] = None` means it's okay if they're not set (e.g., in local dev)
- `DEFAULT_LLM_PROVIDER` says "If I don't specify, use OpenAI"

**9. Vector Database (Qdrant)**
```python
QDRANT_URL: str                         # http://localhost:6333
QDRANT_API_KEY: Optional[str] = None
QDRANT_COLLECTION_NAME: str = "course_content"
```

**Why?**
- Qdrant stores embeddings (vectors) for semantic search
- If a student asks "How do photosynthesis work?", you search similar vectors in Qdrant
- Much faster than scanning all course text

**10. Observability Settings**
```python
JAEGER_AGENT_HOST: str = "localhost"
JAEGER_AGENT_PORT: int = 6831
JAEGER_SAMPLING_RATE: float = 0.1      # Sample 10% of requests
```

**Why?**
- Jaeger collects traces (how a request flows through your system)
- 100% sampling would be slow, so sample 10% of requests

### Bonus: Property Methods

```python
@property
def cors_origins_list(self) -> List[str]:
    return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
```

**Why?**
- In `.env`, you set `CORS_ORIGINS=http://localhost:3000,http://localhost:8000`
- This property splits it by comma and strips whitespace
- Returns a list: `["http://localhost:3000", "http://localhost:8000"]`

### Singleton Pattern

```python
@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

**Why?**
- `@lru_cache()` means "only create this object once, reuse it forever"
- Don't create a new Settings object on every request
- Read the `.env` file once at startup, cache it

### 🎯 Why settings.py matters:
Without centralized configuration, you'd hardcode URLs and keys everywhere. If you need to change the database URL, you'd have to edit 50 files. With this, you edit `.env` once.

---

## 3️⃣ `.env.example` - Configuration Template

**Location:** `smartcourse/.env.example`

**What it does:** Shows what settings your app needs, with example values.

### Key Concept: `.env` vs `.env.example`

- **`.env.example`** - Committed to Git (safe, no secrets)
- **`.env`** - NOT committed to Git (private, has your real secrets)

Your `.gitignore` file has:
```
.env
```

But NOT:
```
.env.example
```

### Content:

```
SMARTCOURSE_APP_NAME=SmartCourse
SMARTCOURSE_APP_ENV=development
SMARTCOURSE_DEBUG=True
SMARTCOURSE_API_V1_PREFIX=/api/v1
```

**Why?** These are the default values for local development.

```
SMARTCOURSE_DATABASE_URL=postgresql+asyncpg://smartcourse:smartcourse_password@localhost:5432/smartcourse
```

**Translation:**
- `postgresql` - Using PostgreSQL (not MySQL, SQLite, etc.)
- `asyncpg` - Use the async driver
- `smartcourse:smartcourse_password` - Username:Password
- `localhost:5432` - Host:Port (PostgreSQL default port is 5432)
- `smartcourse` - Database name

```
SMARTCOURSE_SECRET_KEY=your-secret-key-here-change-in-production
```

**Important!** This says "change in production". For production, you'd use a long random string like:
```
SMARTCOURSE_SECRET_KEY=7%$#@!9xK2mL4pQrStUvWxYz&*()_+-=[]{}|;:,.<>?/~`
```

```
SMARTCOURSE_OPENAI_API_KEY=your-openai-api-key
SMARTCOURSE_ANTHROPIC_API_KEY=your-anthropic-api-key
SMARTCOURSE_GROQ_API_KEY=your-groq-api-key
```

**Why?** Placeholders so you know what API keys you need to get from each provider.

### 🎯 Why `.env.example` matters:
New developers see exactly what settings they need to fill in. No guessing.

---

## 4️⃣ `.env` - Your Private Configuration

**Location:** `smartcourse/.env` (NOT committed)

**What it does:** Same as `.env.example`, but with YOUR real values.

**Example:**
```
SMARTCOURSE_SECRET_KEY=7%$#@!9xK2mL4pQrStUvWxYz&*()_+-=[]{}|;:,.<>?/~`
SMARTCOURSE_OPENAI_API_KEY=sk-proj-abc123xyz789...
SMARTCOURSE_ANTHROPIC_API_KEY=sk-ant-abc123xyz789...
```

### ⚠️ Security Rule:
- **NEVER commit `.env` to Git**
- If you accidentally commit it with real secrets, rotate them immediately
- Add to `.gitignore`:
  ```
  .env
  .env.local
  ```

### 🎯 Why `.env` matters:
Your credentials stay on your machine, not on GitHub where hackers can see them.

---

## 5️⃣ `shared/models/base.py` - Database Base Model

**Location:** `smartcourse/shared/models/base.py`

**What it does:** Defines common fields that ALL database tables should have.

### Content:

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, func
from datetime import datetime

Base = declarative_base()
```

**Translation:**
- `declarative_base()` creates a base class for all models
- Think of it like "make a blueprint template"

```python
class BaseModel(Base):
    """Base model with common fields for all models"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
```

**Breaking it down:**

`__abstract__ = True`
- This means "don't create a database table for this class"
- It's just a template for other models to inherit from

`id = Column(Integer, primary_key=True, index=True)`
- `id` - The column name
- `Integer` - Type (whole numbers: 1, 2, 3, not 1.5)
- `primary_key=True` - This is the unique identifier for each row
- `index=True` - Create a database index on this column (makes lookups fast)

`created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)`
- `DateTime(timezone=True)` - Type (date + time + timezone)
- `server_default=func.now()` - **The database** automatically fills this with current time
  - NOT Python, the DATABASE itself
  - Why? Because if 100 requests hit the database at the same second, they get the exact same timestamp from the database (not slightly different ones)
- `nullable=False` - Can't be empty (every row MUST have a creation time)

`updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)`
- Same as `created_at`, but...
- `onupdate=func.now()` - When this row is modified, automatically update this to current time

```python
def to_dict(self):
    """Convert model to dictionary"""
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

**What this does:**
- When you want to return a model as JSON, you convert it to a dictionary
- `{c.name: getattr(self, c.name) for c in self.__table__.columns}` means:
  - For every column in the table...
  - Get its name and value...
  - Put them in a dictionary

**Example:**
```python
user = User(email="alice@example.com", ...)
user.to_dict()
# Returns: {"id": 1, "email": "alice@example.com", "created_at": "2026-07-06T10:00:00", ...}
```

### 🎯 Why base.py matters:
Instead of adding `id`, `created_at`, `updated_at` to every model, you inherit them once. DRY principle (Don't Repeat Yourself).

---

## 6️⃣ `shared/models/user.py` - User Database Model

**Location:** `smartcourse/shared/models/user.py`

**What it does:** Defines what a "User" row looks like in the database.

### Content:

```python
class UserRole(str, enum.Enum):
    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"
```

**Translation:**
- `Enum` = A fixed set of allowed values
- Users can ONLY be one of these three roles
- The database will reject `role="dinosaur"`

```python
class User(BaseModel):
    """User model for students, instructors, and admins"""
    __tablename__ = "users"
```

- `User` class will become a `users` table in the database
- Inherits from `BaseModel`, so it gets `id`, `created_at`, `updated_at` automatically

```python
email = Column(String(255), unique=True, index=True, nullable=False)
```

- `String(255)` - Text up to 255 characters
- `unique=True` - No two users can have the same email
- `index=True` - Create an index (fast lookup by email)
- `nullable=False` - Email is required

```python
username = Column(String(100), unique=True, index=True, nullable=False)
```

- Same as email, but for usernames

```python
full_name = Column(String(255), nullable=False)
```

- Just the full name, not unique (two people can be named "John Smith")

```python
hashed_password = Column(String(255), nullable=False)
```

- **Important:** It's `hashed_password`, NOT `password`
- NEVER store plain passwords
- Always hash them (one-way encryption)
- If someone steals the database, they can't recover passwords

```python
role = Column(SQLEnum(UserRole), default=UserRole.STUDENT, nullable=False)
```

- `SQLEnum(UserRole)` - Use the UserRole enum we defined
- `default=UserRole.STUDENT` - If not specified, default to student
- `nullable=False` - Role is required

```python
is_active = Column(Boolean, default=True, nullable=False)
```

- `Boolean` - True or False
- `default=True` - New users are active by default
- Set to False if you want to deactivate a user (soft delete)

```python
avatar_url = Column(String(500), nullable=True)
bio = Column(String(1000), nullable=True)
```

- `nullable=True` - These are optional (users don't have to fill them in)

```python
# Relationships
created_courses = relationship("Course", back_populates="instructor", foreign_keys="Course.instructor_id")
enrollments = relationship("Enrollment", back_populates="student")
```

**What are relationships?**
- In a relational database, tables are linked
- An instructor (User) creates many courses (Course)
- A student (User) enrolls in many enrollments (Enrollment)
- These relationships let you do:
  ```python
  user = User.query.get(1)
  user.created_courses  # All courses created by this user
  user.enrollments      # All enrollments for this user
  ```

### 🎯 Why user.py matters:
Defines the structure of users in your database. No users = no app.

---

## 7️⃣ `shared/models/course.py` - Course/Module/Lesson Models

**Location:** `smartcourse/shared/models/course.py`

**What it does:** Defines course content structure (courses contain modules contain lessons).

### Content (similar pattern):

```python
class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    READY = "ready"
    PUBLISHED = "published"
```

Courses can be in one of three states. Same enum pattern as UserRole.

```python
class Course(BaseModel):
    __tablename__ = "courses"
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(CourseStatus), default=CourseStatus.DRAFT, nullable=False)
    language = Column(String(10), default="en", nullable=False)
    difficulty = Column(String(20), default="beginner", nullable=False)
```

**Key new concept: Foreign Key**
```python
instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
```

- `instructor_id` is an ID that points to a row in the `users` table
- `ForeignKey("users.id")` = Must match an actual user ID
- Database rejects: `instructor_id=999` if user 999 doesn't exist
- This ensures data integrity (no orphan courses)

```python
class Module(BaseModel):
    __tablename__ = "modules"
    
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False)  # Module 1, Module 2, Module 3
```

- A module belongs to one course
- `order` lets you control the sequence

```python
class Lesson(BaseModel):
    __tablename__ = "lessons"
    
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    order = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=True)  # Minutes
```

- A lesson belongs to one module
- `duration` is in minutes (optional)

### 🎯 Why course.py matters:
Defines the course structure. Without it, you have no way to store courses in the database.

---

## 8️⃣ `shared/models/enrollment.py` - Enrollment & Progress Models

**Location:** `smartcourse/shared/models/enrollment.py`

**What it does:** Tracks which students are enrolled in which courses, and their progress.

### Content:

```python
class Enrollment(BaseModel):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint('user_id', 'course_id', name='uq_user_course'),)
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    status = Column(String(20), default="active", nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
```

**Key concept: Unique Constraint**
```python
__table_args__ = (UniqueConstraint('user_id', 'course_id', name='uq_user_course'),)
```

- A student can't enroll in the same course twice
- The combination of (user_id, course_id) must be unique
- Database rejects: Student 1 enrolling in Course 5 again

```python
enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
completed_at = Column(DateTime(timezone=True), nullable=True)
```

- When did they enroll? (Required)
- When did they complete? (Optional - null until they finish)

```python
class Progress(BaseModel):
    __tablename__ = "progress"
    
    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
```

- For each lesson in an enrollment, track if it's completed
- This lets you show "You've completed 15/30 lessons" (progress bar)

### 🎯 Why enrollment.py matters:
Tracks who is learning what, and how far they've gotten.

---

## 9️⃣ `shared/utils/database.py` - Database Connection Management

**Location:** `smartcourse/shared/utils/database.py`

**What it does:** Sets up the plumbing for connecting to PostgreSQL.

### Content:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
    future=True
)
```

**Breaking it down:**

`create_async_engine` - Creates an async engine
- Async = Non-blocking. Request A doesn't wait for Request B's database query to finish
- If you had regular (sync) queries, Request A would block while talking to the database

`settings.DATABASE_URL` - The connection string
- `postgresql+asyncpg://smartcourse:smartcourse_password@localhost:5432/smartcourse`

`pool_size=20` - Keep 20 connections open to the database
- When a request comes in, grab one from the pool
- If all 20 are busy, wait

`max_overflow=10` - If desperate, open 10 more (total 30)
- But this is temporary (returns to 20 when request finishes)

`echo=settings.DEBUG` - If DEBUG=True, print all SQL to console
- Useful for debugging, but noisy in production

```python
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)
```

**What is a session?**
- A session is a conversation with the database
- Request A creates a session, runs queries, closes the session
- Request B creates its own session, doesn't see Request A's changes (until committed)

`expire_on_commit=False` - After committing, keep the data in memory
- If you query a user, modify it, commit, the Python object still has the data
- You don't have to re-query it from the database

`autocommit=False` - Don't auto-commit changes
- Must explicitly call `await session.commit()`
- Safer (prevents accidental permanent changes)

`autoflush=False` - Don't auto-flush changes to the database
- Gives you control over when database sees your changes

```python
async def get_db() -> AsyncSession:
    """Dependency for getting async database sessions"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**What is this?**
- This is a "dependency injection" function
- Used by FastAPI routes like this:
  ```python
  @app.get("/users/{user_id}")
  async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
      user = await db.query(User).filter(User.id == user_id).first()
      return user
  ```
- FastAPI automatically calls `get_db()` for every request
- Creates a session, passes it to your route
- After the route finishes, closes the session

The `try/finally` ensures the session is ALWAYS closed, even if the route crashes.

```python
async def init_db():
    """Initialize database connection"""
    async with engine.begin() as conn:
        from shared.models import Base
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
```

**What does this do?**
- Creates all tables in the database based on your models
- Only for development/testing
- In production, you use Alembic migrations

```python
async def close_db():
    """Close database connection"""
    await engine.dispose()
    logger.info("Database connection closed")
```

- Closes all connections in the pool
- Call this when the app shuts down

### 🎯 Why database.py matters:
Without this, routes have no way to talk to the database.

---

## 🔟 `alembic.ini` - Migration Configuration

**Location:** `smartcourse/alembic.ini`

**What it does:** Tells Alembic how to manage database schema changes.

### Key Concept: Migrations

Imagine you're deploying to production with 1 million users:
- You can't just drop the table and recreate it (data loss!)
- You need step-by-step instructions: "Add this column", "Create this index", "Rename this"
- These step-by-step instructions are "migrations"

### Content:

```
[alembic]
script_location = alembic
```

- Migrations are stored in the `alembic/` directory

```
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
```

- Migration filenames look like: `2026_07_06_1030_abc123_add_user_table.py`
- Date + time + hash + description
- Prevents conflicts if two developers create migrations simultaneously

```
prepend_sys_path = .
```

- Add current directory to Python path
- Lets Alembic import your models

```
version_path_separator = os
```

- Use OS-specific path separators (/ on Unix, \ on Windows)

### 🎯 Why alembic.ini matters:
Without this, Alembic doesn't know where to find your models or where to store migrations.

---

## 1️⃣1️⃣ `alembic/env.py` - Alembic Environment

**Location:** `smartcourse/alembic/env.py`

**What it does:** Configures how Alembic should run migrations.

### Key Concepts:

```python
from sqlalchemy import engine_from_config, pool
from alembic import context
from shared.models import Base
from shared.config.settings import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

- Load the settings
- Tell Alembic which database to use (read from settings)

```python
target_metadata = Base.metadata
```

- This is the "truth" - the schema defined in your models
- Alembic compares current database schema to this
- Any differences = generate a migration

### 🎯 Why env.py matters:
Tells Alembic how to detect schema changes and generate migrations.

---

## 1️⃣2️⃣ `docker-compose.yml` - Local Infrastructure

**Location:** `smartcourse/docker-compose.yml`

**What it does:** Defines all 11 services that run locally for development.

### Big Picture:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    container_name: smartcourse-postgres
```

- `postgres` is the service name
- `image: postgres:15-alpine` = Download official PostgreSQL 15 image (alpine = small)
- `container_name` = Docker container name (for reference)

```yaml
    environment:
      POSTGRES_USER: smartcourse
      POSTGRES_PASSWORD: smartcourse_password
      POSTGRES_DB: smartcourse
```

- Environment variables for PostgreSQL
- Creates a database named `smartcourse` with user `smartcourse`

```yaml
    ports:
      - "5432:5432"
```

- Maps port 5432 inside container to port 5432 on your machine
- `host:container`
- So you can connect to `localhost:5432` from your Python code

```yaml
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

- `postgres_data` is a Docker volume (persistent storage)
- Without this, when the container stops, all data is lost
- With this, data survives container restarts

```yaml
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U smartcourse"]
      interval: 10s
      timeout: 5s
      retries: 5
```

- Every 10 seconds, run `pg_isready` to check if PostgreSQL is healthy
- If 5 checks fail, Docker marks container as unhealthy
- Useful for knowing when a service is ready before starting dependent services

### Similar patterns for all 11 services:

**Redis** - Fast in-memory cache
**RabbitMQ** - Message broker for tasks (with UI at port 15672)
**Kafka** - Event streaming (with Zookeeper for coordination)
**Schema Registry** - Kafka schema storage
**Temporal** - Workflow orchestration (with UI at port 8088)
**Qdrant** - Vector database for AI embeddings
**Prometheus** - Metrics collection
**Grafana** - Metrics visualization (UI at port 3000)
**Jaeger** - Distributed tracing (UI at port 16686)

### At the bottom:

```yaml
volumes:
  postgres_data:
  redis_data:
  # ... etc
```

- Names the volumes so they persist across container restarts

### 🎯 Why docker-compose.yml matters:
One command (`docker-compose up`) starts 11 services. Without it, you'd have to:
1. Download PostgreSQL installer, install, run
2. Download Redis installer, install, run
3. Download RabbitMQ installer, install, run
4. ... (9 more times)

Nightmare! Docker Compose automates all of this.

---

## 1️⃣3️⃣ `pyproject.toml` - Project Metadata & Dependencies

**Location:** `smartcourse/pyproject.toml`

**What it does:** Declares all Python packages your project needs.

### Content:

```toml
[project]
name = "smartcourse"
version = "0.1.0"
description = "SmartCourse - Intelligent Course Delivery Platform"
requires-python = ">=3.11"
```

- Project name, version, description
- Requires Python 3.11 or newer

```toml
dependencies = [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "sqlalchemy[asyncio]>=2.0.0",
    ...
]
```

**Breaking down key dependencies:**

- `fastapi` - The web framework
- `uvicorn` - The web server (runs FastAPI)
- `sqlalchemy[asyncio]` - ORM + async support
- `asyncpg` - Async PostgreSQL driver
- `alembic` - Database migrations
- `pydantic` - Data validation
- `python-jose` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `redis` - Cache client
- `celery` - Task queue
- `kafka-python`, `aiokafka` - Kafka clients
- `temporalio` - Temporal client
- `langgraph` - AI workflow library
- `openai`, `anthropic` - LLM providers
- `qdrant-client` - Vector database client
- `opentelemetry-*` - Tracing/observability
- `prometheus-client` - Metrics export

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.11.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]
```

- Development dependencies (testing, linting, formatting)
- Install with: `pip install smartcourse[dev]`

### Tool Configuration:

```toml
[tool.black]
line-length = 100
target-version = ['py311']
```

- Black is a code formatter
- Format lines to max 100 characters
- Use Python 3.11 syntax

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --cov=services --cov=shared --cov=workflows --cov-report=html"
```

- Pytest (testing framework) configuration
- `asyncio_mode = "auto"` - Automatically handle async tests
- Find tests in `tests/` directory
- Test files start with `test_`
- Generate coverage reports (how much code is tested)

### 🎯 Why pyproject.toml matters:
New developer runs `pip install -r requirements.txt` or `pip install -e '.[dev]'`, gets all 38 packages in seconds instead of manually installing each one.

---

## 1️⃣4️⃣ `requirements.txt` - Simple Dependency List

**Location:** `smartcourse/requirements.txt`

**What it does:** Alternative to pyproject.toml. Simple list of packages.

### Content:

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sqlalchemy[asyncio]>=2.0.0
...
```

- Same as pyproject.toml dependencies, just in a flat file
- Old-school way of declaring dependencies
- Modern projects use pyproject.toml instead

### 🎯 Why requirements.txt matters:
Some deployment tools only understand requirements.txt (e.g., older PaaS providers). Kept for compatibility.

---

## 1️⃣5️⃣ `docker/prometheus/prometheus.yml` - Metrics Configuration

**Location:** `smartcourse/docker/prometheus/prometheus.yml`

**What it does:** Tells Prometheus where to collect metrics from.

### Content (first part you opened):

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    monitor: 'smartcourse-monitor'
```

- Every 15 seconds, collect metrics from endpoints
- `external_labels` - Add a label to all metrics (helps organize them)

```yaml
scrape_configs:
  - job_name: 'fastapi'
    static_configs:
      - targets: ['localhost:8000']
```

- Job named "fastapi"
- Collect metrics from `http://localhost:8000/metrics`
- Every 15 seconds, Prometheus scrapes `/metrics` on your FastAPI app

```yaml
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

- Also monitor Prometheus itself (meta!)
- Collect metrics about Prometheus's memory usage, scrape time, etc.

### 🎯 Why prometheus.yml matters:
Without this, Prometheus doesn't know where to find your metrics. You'd have no monitoring.

---

## 1️⃣6️⃣ `alembic/script.py.mako` - Migration Template

**Location:** `smartcourse/alembic/script.py.mako`

**What it does:** Template for generating new migration files.

When you run:
```bash
alembic revision --autogenerate -m "add user table"
```

Alembic creates a new file based on this template. It's boilerplate you don't need to edit.

### 🎯 Why script.py.mako matters:
Ensures all migration files have the same structure and metadata.

---

## Summary: The Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Python Code                      │
│              (routes, services, business logic)              │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    main.py (FastAPI app)                    │
│        (receives HTTP requests, routes them to handlers)    │
└─────────────────────────┬───────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         │                │                │
    ┌────▼────┐   ┌──────▼─────┐   ┌─────▼──────┐
    │Settings │   │ Prometheus │   │   CORS     │
    │ (.env)  │   │  Metrics   │   │ Middleware │
    └─────────┘   └────────────┘   └────────────┘
         │
    ┌────▼────────────────────────────────────────┐
    │     Database Connection (SQLAlchemy)        │
    │  (async sessions, connection pooling)       │
    └────┬────────────────────────────────────────┘
         │
    ┌────▼────────────────────────────────────────┐
    │          PostgreSQL Database                │
    │  (User, Course, Module, Lesson, etc)       │
    │  (managed by Alembic migrations)            │
    └─────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│          Docker Compose (11 Services in Containers)         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PostgreSQL │ Redis │ RabbitMQ │ Kafka │ Temporal │ Qdrant │
│  Prometheus │ Grafana │ Jaeger │ Zookeeper │ Schema Reg │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 The "Why" Behind Everything

### Why FastAPI?
- Modern (2018+), not old (Django 2005)
- Async/await support (fast, handles lots of requests)
- Automatic OpenAPI docs
- Built-in data validation

### Why PostgreSQL?
- Reliable, mature, open-source
- Better than SQLite for production (SQLite locks the file)
- Supports async

### Why Alembic?
- Safe schema changes (don't lose data)
- Rollback support (oops, I made a mistake)
- Version control for your database

### Why Docker Compose?
- One command to start everything
- Same setup on every machine (no "works on my machine" bugs)
- Mirrors production infrastructure

### Why Pydantic Settings?
- Environment variable configuration
- Type checking (no typos)
- Easy to switch environments (dev/staging/prod)

### Why Prometheus/Grafana/Jaeger?
- Know what your app is doing
- Spot problems before users complain
- Debug issues faster

---

## 🚀 Next Steps

Now that you understand the foundation:

**Days 2-7** will build:
- Routes (API endpoints users call)
- Services (business logic)
- Repositories (database queries)
- Authentication (login/JWT)
- Tests (ensure nothing breaks)

Each day adds features on top of this solid foundation.

---

**Questions? Let me know which file you want me to dive deeper into!**
