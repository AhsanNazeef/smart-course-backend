# SmartCourse Documentation

Central index for all project documentation. The root [`README.md`](../README.md)
covers setup and quick start; everything else lives here.

## 🏛️ Architecture

Key architectural decisions (ADRs).

| Doc | Description |
|-----|-------------|
| [architecture/adr-001-microservices-monorepo.md](architecture/adr-001-microservices-monorepo.md) | Decision to use microservices (monorepo, database-per-service) + migration plan |

## 📦 Product

What we're building and why.

| Doc | Description |
|-----|-------------|
| [product/prd.md](product/prd.md) | Product Requirements Document — vision, features, scope |
| [product/requirements.md](product/requirements.md) | Project requirements and constraints |

## 🗺️ Planning

The roadmap and day-by-day build plans.

| Doc | Description |
|-----|-------------|
| [planning/roadmap.md](planning/roadmap.md) | Microservices implementation & learning plan (rolling-wave: detailed near-term, themed later) |
| [planning/day-02.md](planning/day-02.md) | Detailed Day 2 build plan (tests + settings validation) |

## 📘 Guides

Beginner-friendly, file-by-file walkthroughs of what was built each day.

| Doc | Description |
|-----|-------------|
| [guides/day-01-file-by-file.md](guides/day-01-file-by-file.md) | Every Day 1 file explained (scaffold & infrastructure) |
| [guides/day-02-file-by-file.md](guides/day-02-file-by-file.md) | Every Day 2 file explained (tests & config validation) |
| [guides/day-03-file-by-file.md](guides/day-03-file-by-file.md) | Every Day 3 change explained (migrations & constraints) |
| [guides/day-04-file-by-file.md](guides/day-04-file-by-file.md) | Every Day 4 file explained (repository & service layers) |

## 🔧 Reference

Operational reference material.

| Doc | Description |
|-----|-------------|
| [reference/configuration.md](reference/configuration.md) | All `SMARTCOURSE_` environment variables |

---

## Folder Layout

```text
docs/
├── README.md              # this index
├── architecture/          # architecture decision records (ADRs)
│   └── adr-001-microservices-monorepo.md
├── product/               # what & why
│   ├── prd.md
│   └── requirements.md
├── planning/              # roadmap & daily build plans
│   ├── roadmap.md
│   └── day-02.md
├── guides/                # learning walkthroughs
│   ├── day-01-file-by-file.md
│   ├── day-02-file-by-file.md
│   ├── day-03-file-by-file.md
│   └── day-04-file-by-file.md
└── reference/             # operational reference
    └── configuration.md
```

> **Note:** `README.md` and `AGENTS.md` intentionally stay in the project root —
> they're conventional entry points that tools and contributors expect there.
