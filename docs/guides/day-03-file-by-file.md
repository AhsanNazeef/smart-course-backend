# 📖 Day 3 - Complete File-by-File Breakdown

A beginner-friendly guide to everything changed on Day 3, and **why** each piece exists.

---

## 🎯 The Big Picture First

Day 1 defined your database tables **in Python** (the models). But Python models are just a *description* — they don't create anything in the actual database.

Day 3 is where that description becomes **real tables in PostgreSQL**, using a tool called **Alembic**.

The house analogy again:
- **Day 1 models** = The architect's blueprint (drawn on paper)
- **Day 3 migration** = The construction crew that actually builds the house from the blueprint
- **Alembic** = The project manager who keeps a numbered log of every construction step, so the house can be rebuilt (or torn down) exactly the same way, anywhere

---

## What Changed on Day 3

| File | Status | Purpose |
|------|--------|---------|
| `shared/models/enrollment.py` | ✏️ Modified | Added 2 uniqueness rules to protect data |
| `alembic/versions/..._initial_schema.py` | 🆕 New (auto-generated) | The step-by-step instructions to build all tables |

Plus a lot happened in the **database itself** and via **Alembic commands** — we'll cover those too, because they're the real heart of Day 3.

---

## 🔑 Core Concept: What Is a Migration? (Read this first)

A **migration** is a versioned, repeatable instruction file that changes your database structure.

### Why not just create tables directly?

Imagine you have a live app with 10,000 users. You need to add a `phone_number` column. You can't:
- ❌ Delete the database and recreate it (you'd lose all 10,000 users)
- ❌ Manually type SQL on the production server (error-prone, unrepeatable, no record)

Instead, you write a **migration**: "Add a `phone_number` column to `users`." Then:
- ✅ It runs the same way on your laptop, your teammate's laptop, and production
- ✅ It's recorded in version control (Git) like any other code
- ✅ It can be **rolled back** if something goes wrong
- ✅ Alembic tracks which migrations have run, so it never runs one twice

### The mental model

```
Your Python Models  ──(alembic autogenerate)──►  Migration File  ──(alembic upgrade)──►  Real Database Tables
   (the blueprint)                                (the instructions)                        (the actual house)
```

---

## 1️⃣ `shared/models/enrollment.py` - Added Data-Integrity Constraints

**Location:** `smartcourse/shared/models/enrollment.py`

**What changed:** We added **unique constraints** — rules the database itself enforces to prevent bad data.

### Change 1: Import the constraint tool

**Before:**
```python
from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum, DateTime, Boolean, func
```

**After:**
```python
from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum, DateTime, Boolean, func, UniqueConstraint
```

We added `UniqueConstraint` to the import list. That's the tool for saying "this combination of columns must be unique."

### Change 2: Enrollment uniqueness

**Added to the `Enrollment` class:**
```python
class Enrollment(BaseModel):
    """Enrollment model for student-course relationships"""
    __tablename__ = "enrollments"
    __table_args__ = (
        # A student can only have one enrollment row per course.
        # (Re-enrollment after dropping is handled at the service layer later.)
        UniqueConstraint("student_id", "course_id", name="uq_enrollment_student_course"),
    )

    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    ...
```

### Change 3: Progress uniqueness

**Added to the `Progress` class:**
```python
class Progress(BaseModel):
    """Progress model for tracking student learning progress"""
    __tablename__ = "progress"
    __table_args__ = (
        # One progress record per lesson per enrollment.
        # This makes "mark lesson complete" idempotent (Day 11).
        UniqueConstraint("enrollment_id", "lesson_id", name="uq_progress_enrollment_lesson"),
    )

    enrollment_id = Column(Integer, ForeignKey("enrollments.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    ...
```

### 🔑 Key Concept: What is `__table_args__`?

It's a special SQLAlchemy attribute for **table-level settings** — things that apply to the whole table rather than a single column.

- `Column(...)` = a rule about ONE column (e.g., "email is a string")
- `__table_args__` = rules that span MULTIPLE columns (e.g., "student_id + course_id together must be unique")

**Note the trailing comma:**
```python
__table_args__ = (
    UniqueConstraint(...),   # <-- this comma matters!
)
```
`__table_args__` must be a **tuple**. In Python, `(x)` is just `x` in parentheses, but `(x,)` is a tuple with one item. The comma is what makes it a tuple. Forgetting it is a common bug.

### 🔑 Key Concept: What is a UNIQUE constraint?

It tells the database: "no two rows can have the same value(s) here."

A **single-column** unique constraint (from Day 1):
```python
email = Column(String(255), unique=True)   # no two users share an email
```

A **multi-column** (composite) unique constraint (Day 3):
```python
UniqueConstraint("student_id", "course_id")  # the COMBINATION must be unique
```

This means:
- Student 1 in Course 5 → ✅ allowed
- Student 1 in Course 9 → ✅ allowed (different course)
- Student 2 in Course 5 → ✅ allowed (different student)
- Student 1 in Course 5 **again** → ❌ **rejected by the database**

### Why enforce this in the DATABASE, not just in Python code?

You might think: "I'll just check in my Python code before inserting." But that's not safe. Picture two requests arriving at the exact same millisecond:

```
Request A: "Is student 1 enrolled in course 5?" → No → proceed to insert
Request B: "Is student 1 enrolled in course 5?" → No → proceed to insert
                                    (both checks ran before either insert)
Result: TWO duplicate enrollments! 💥
```

This is called a **race condition**. The only bulletproof fix is to make the **database itself** refuse duplicates. The database handles concurrency correctly; your application-level check cannot. This is a foundational senior-engineering lesson.

### 🎯 Why these constraints matter:
- **Enrollment uniqueness** prevents double-charging, double-counting, and duplicate records
- **Progress uniqueness** means "mark lesson complete" can be safely retried — clicking twice won't create two rows (this is called **idempotency**, and you'll build on it in Day 11)

---

## 2️⃣ `alembic/versions/2026_07_08_1916_655df2dcef99_initial_schema.py` - The Migration

**Location:** `smartcourse/alembic/versions/`

**What it does:** Contains the actual instructions to build (and tear down) all 7 tables. Most of it was **auto-generated** by Alembic reading your models.

### The filename decoded

```
2026_07_08_1916_655df2dcef99_initial_schema.py
└────┬────┘ └┬─┘ └─────┬────┘ └──────┬──────┘
   date     time    revision ID    description
```

- **Date + time** — when it was created (from your `alembic.ini` filename template)
- **Revision ID** (`655df2dcef99`) — a unique random hash identifying this migration
- **Description** — the `-m "initial schema"` message you passed

### The header

```python
revision = '655df2dcef99'
down_revision = None
branch_labels = None
depends_on = None
```

- `revision` — this migration's unique ID
- `down_revision = None` — **this is the FIRST migration** (nothing comes before it). The next migration you create will have `down_revision = '655df2dcef99'`, forming a chain.

### 🔑 Key Concept: The migration chain

Migrations form a linked list, each pointing to the one before it:

```
None ──► 655df2dcef99 ──► (next migration) ──► (one after that) ──► ...
         "initial schema"
```

Alembic uses this chain to know the order to apply them, and which ones still need running. `head` means "the newest one in the chain."

### The `upgrade()` function

This runs when you **apply** the migration (move the database *forward*). It builds the tables.

```python
def upgrade() -> None:
    op.create_table('users',
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        ...
        sa.Column('role', sa.Enum('STUDENT', 'INSTRUCTOR', 'ADMIN', name='userrole'), nullable=False),
        ...
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    ...
```

Line-by-line concepts:
- `op.create_table('users', ...)` — the SQL `CREATE TABLE users` expressed in Python
- Each `sa.Column(...)` mirrors exactly what you wrote in your model
- `sa.Enum('STUDENT', 'INSTRUCTOR', 'ADMIN', name='userrole')` — creates a Postgres **enum type** (a column that only accepts these 3 values)
- `sa.PrimaryKeyConstraint('id')` — marks `id` as the primary key
- `op.create_index(..., unique=True)` — builds a fast-lookup index; `unique=True` also enforces no duplicate emails

### 🔑 Key Concept: Table creation ORDER matters

Notice the order: `users` → `courses` → `enrollments` → `modules` → `lessons` → `assets` → `progress`.

This isn't random. A table with a **foreign key** must be created *after* the table it points to:
- `courses` has `instructor_id → users.id`, so `users` must exist first
- `enrollments` points to both `users` and `courses`, so both must exist first

Alembic figured out this dependency order automatically. If it built `courses` before `users`, Postgres would error: "you're referencing a table that doesn't exist yet."

### Your two unique constraints in the migration

Because you added them to the models, autogenerate included them:

```python
# inside op.create_table('enrollments', ...)
sa.UniqueConstraint('student_id', 'course_id', name='uq_enrollment_student_course')

# inside op.create_table('progress', ...)
sa.UniqueConstraint('enrollment_id', 'lesson_id', name='uq_progress_enrollment_lesson')
```

This is the payoff of editing the models *before* generating the migration — the constraints flow through automatically.

### The `downgrade()` function

This runs when you **roll back** (move the database *backward*). It undoes everything `upgrade()` did, in **reverse order**.

```python
def downgrade() -> None:
    op.drop_index(op.f('ix_progress_id'), table_name='progress')
    op.drop_table('progress')
    op.drop_table('assets')
    ...
    op.drop_table('users')
```

Why reverse order? Same foreign-key reason, backwards: you must drop `progress` (which points to `enrollments`) *before* dropping `enrollments`. You can't remove a table that another table still references.

### 🔧 The hand-fix we added (the senior-engineer catch)

Autogenerate produced a `downgrade()` that dropped the tables — but **not** the enum types. We added this at the end:

```python
    # Postgres does NOT auto-drop enum types when their tables are dropped.
    # Drop them explicitly so a later `upgrade` doesn't fail with
    # "type ... already exists".
    sa.Enum(name='enrollmentstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='coursestatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
```

**The problem this solves:**
When Postgres creates a table with an enum column, it also creates a standalone "type" (e.g., `userrole`). But when you `DROP TABLE`, Postgres leaves that type behind. So if you did `downgrade` then `upgrade` again, Postgres would complain: *"type userrole already exists."*

Since re-running migrations is common during development, we drop the enum types explicitly.

- `sa.Enum(name='userrole').drop(...)` — drops the leftover type
- `op.get_bind()` — gets the current database connection to run the drop on
- `checkfirst=True` — "only drop it if it actually exists" (so this never errors)

> **Lesson:** *"Auto-generated" does not mean "perfect."* Always review a migration before applying it. Autogenerate is a great first draft, not a final answer.

### 🎯 Why the migration file matters:
It's the single source of truth for your database's structure, versioned in Git. Anyone — a teammate, a CI server, production — can run it and get the exact same schema.

---

## 3️⃣ The Alembic Commands (What You Actually Ran)

These aren't files, but they're the core of Day 3. Here's what each did.

### `alembic revision --autogenerate -m "initial schema"`

```bash
python -m alembic revision --autogenerate -m "initial schema"
```

- `revision` — create a new migration file
- `--autogenerate` — **compare your models to the current database**, and write the differences into the migration automatically
- `-m "initial schema"` — the description

Because the database was empty and your models define 7 tables, Alembic wrote "create these 7 tables." You saw output like:
```
Detected added table 'users'
Detected added table 'courses'
...
```

> **How does it compare?** Alembic connects to the real database, reads what tables exist, reads your models (`target_metadata` in `alembic/env.py`), and computes the difference. That's why Postgres had to be running.

### `alembic upgrade head`

```bash
python -m alembic upgrade head
```

- `upgrade` — apply migrations (move forward)
- `head` — "apply everything up to the newest migration"

This ran your `upgrade()` function, creating all the tables. Output:
```
Running upgrade  -> 655df2dcef99, initial schema
```

### `alembic current`

```bash
python -m alembic current
```

Shows which migration the database is currently at:
```
655df2dcef99 (head)
```

`(head)` confirms the database is fully up to date — it's at the newest migration.

### 🔑 Key Concept: How Alembic tracks progress

Alembic created a special table in your database called `alembic_version`. It holds exactly one row: the revision ID of the last-applied migration.

That's how `alembic current` knows where you are, and how `upgrade` knows what still needs running. It never runs the same migration twice because it checks this table first.

---

## 4️⃣ What Happened in the Database

After `alembic upgrade head`, PostgreSQL now contains:

```
List of tables:
 alembic_version   ← Alembic's bookkeeping (which migration are we at)
 users
 courses
 enrollments
 modules
 lessons
 assets
 progress
```

And your two unique constraints are live:
```
uq_enrollment_student_course  →  enrollments
uq_progress_enrollment_lesson →  progress
```

You verified this by querying Postgres directly with `psql`. The tables now physically exist — you could insert a user right now.

---

## 🗺️ How Day 3 Fits Together

```
   You edit models         You run autogenerate        You run upgrade
   (add constraints)             │                           │
        │                        ▼                           ▼
        │              ┌──────────────────┐       ┌────────────────────┐
        └─────────────►│  Migration file  │──────►│  Real PostgreSQL    │
   shared/models/      │  upgrade() /     │       │  tables + constraints│
   enrollment.py       │  downgrade()     │       │  + alembic_version   │
                       └──────────────────┘       └────────────────────┘
                          (you REVIEW &                 (you VERIFY
                           hand-fix here)                with psql here)
```

The workflow, memorized:
1. **Edit models** (Python)
2. **Autogenerate** a migration (`alembic revision --autogenerate`)
3. **Review** the migration (never skip this!)
4. **Apply** it (`alembic upgrade head`)
5. **Verify** (`alembic current` + check the DB)

---

## 🧠 Concepts You Learned Today

| Concept | What it means | Where you saw it |
|---------|---------------|------------------|
| **Migration** | Versioned, repeatable schema change | the migration file |
| **Autogenerate** | Alembic writes the migration by diffing models vs DB | `alembic revision --autogenerate` |
| **upgrade / downgrade** | Apply forward / roll back | migration functions |
| **Migration chain** | Migrations link via `down_revision` | file header |
| **`head`** | The newest migration in the chain | `alembic upgrade head` |
| **Unique constraint** | DB rule: no duplicate values | `UniqueConstraint(...)` |
| **Composite constraint** | Uniqueness across multiple columns | `(student_id, course_id)` |
| **`__table_args__`** | Table-level settings (multi-column rules) | enrollment.py |
| **Race condition** | Two requests conflict at the same instant | why DB-level constraints matter |
| **Idempotency** | Safe to repeat without side effects | progress uniqueness |
| **FK creation order** | Referenced tables must exist first | table order in `upgrade()` |
| **`alembic_version` table** | How Alembic tracks applied migrations | the database |

---

## ✅ Day 3 Definition of Done — Achieved

- ✅ All models reviewed
- ✅ Enrollment & progress uniqueness constraints added
- ✅ Initial migration generated and reviewed (with enum-drop fix)
- ✅ `alembic upgrade head` succeeded → database is at `655df2dcef99 (head)`
- ✅ Tables and constraints verified in PostgreSQL
- ✅ Existing 9 tests still pass
- ✅ Committed & pushed: `819ca23 - Add initial database migration`

---

## 🔭 What Day 4 Builds on This

Now that real tables exist, Day 4 adds the **repository and service layers** for the `users` domain — the pattern `route → service → repository` — so your API routes stay thin and database queries live in one clean place. The tables you just created are what those repositories will read and write.

---

**Questions? Ask me to go deeper on migrations, constraints, or the Alembic workflow!**
