# Configuration Reference

All settings use the `SMARTCOURSE_` prefix and load from `.env`.
Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

If a required variable is missing, the app prints a clear
`CONFIGURATION ERROR` message at startup (see `shared/config/settings.py`).

---

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
| `SMARTCOURSE_CELERY_BROKER_URL` | `amqp://smartcourse:smartcourse_password@localhost:5672/` | Celery broker |
| `SMARTCOURSE_CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Celery results |

---

## Optional (have sensible defaults)

| Variable | Default | Purpose |
|---|---|---|
| `SMARTCOURSE_APP_NAME` | `SmartCourse` | Application name |
| `SMARTCOURSE_APP_ENV` | `development` | Environment name |
| `SMARTCOURSE_DEBUG` | `True` | Verbose logs / auto-reload |
| `SMARTCOURSE_API_V1_PREFIX` | `/api/v1` | Base path for v1 endpoints |
| `SMARTCOURSE_DATABASE_POOL_SIZE` | `20` | Open DB connections to keep |
| `SMARTCOURSE_DATABASE_MAX_OVERFLOW` | `10` | Extra DB connections under load |
| `SMARTCOURSE_REDIS_CACHE_TTL` | `3600` | Cache expiry (seconds) |
| `SMARTCOURSE_RABBITMQ_TASK_QUEUE` | `smartcourse_tasks` | Default task queue name |
| `SMARTCOURSE_KAFKA_CONSUMER_GROUP` | `smartcourse_group` | Kafka consumer group |
| `SMARTCOURSE_TEMPORAL_PORT` | `7233` | Temporal server port |
| `SMARTCOURSE_TEMPORAL_NAMESPACE` | `default` | Temporal namespace |
| `SMARTCOURSE_TEMPORAL_TASK_QUEUE` | `smartcourse_workflows` | Temporal task queue |
| `SMARTCOURSE_ALGORITHM` | `HS256` | JWT signing algorithm |
| `SMARTCOURSE_ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `SMARTCOURSE_REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `SMARTCOURSE_OPENAI_API_KEY` | `None` | OpenAI API key |
| `SMARTCOURSE_ANTHROPIC_API_KEY` | `None` | Anthropic API key |
| `SMARTCOURSE_GROQ_API_KEY` | `None` | Groq API key |
| `SMARTCOURSE_DEFAULT_LLM_PROVIDER` | `openai` | Which AI provider to use |
| `SMARTCOURSE_QDRANT_API_KEY` | `None` | Qdrant API key (if secured) |
| `SMARTCOURSE_QDRANT_COLLECTION_NAME` | `course_content` | Vector collection name |
| `SMARTCOURSE_JAEGER_AGENT_HOST` | `localhost` | Jaeger agent host |
| `SMARTCOURSE_JAEGER_AGENT_PORT` | `6831` | Jaeger agent port |
| `SMARTCOURSE_JAEGER_SAMPLING_RATE` | `0.1` | Fraction of requests traced |
| `SMARTCOURSE_PROMETHEUS_PORT` | `9090` | Prometheus port |
| `SMARTCOURSE_GRAFANA_PORT` | `3000` | Grafana port |
| `SMARTCOURSE_GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana admin password |
| `SMARTCOURSE_CORS_ORIGINS` | `http://localhost:3000,http://localhost:8000` | Allowed CORS origins (comma-separated) |
| `SMARTCOURSE_MAX_UPLOAD_SIZE` | `10485760` | Max upload bytes (10MB) |
| `SMARTCOURSE_UPLOAD_DIR` | `./uploads` | Local upload directory |
| `SMARTCOURSE_RATE_LIMIT_PER_MINUTE` | `100` | API rate limit |
| `SMARTCOURSE_BURST_LIMIT` | `200` | Rate limit burst allowance |
| `SMARTCOURSE_CELERY_TASK_SOFT_TIME_LIMIT` | `300` | Celery soft timeout (seconds) |
| `SMARTCOURSE_CELERY_TASK_TIME_LIMIT` | `600` | Celery hard timeout (seconds) |

---

> **Tip:** To find which variables are required, open `shared/config/settings.py`
> and look for any field **without** a default value (e.g. `DATABASE_URL: str`).
> Fields with `= <value>` or `Optional[...] = None` are optional.
