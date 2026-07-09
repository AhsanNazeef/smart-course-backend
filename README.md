# SmartCourse - Intelligent Course Delivery Platform

An intelligent, large-scale learning platform designed to support modern digital education for universities, enterprises, and training academies.

## Features

- **Robust Course Management**: Create, structure, and publish courses efficiently
- **Intelligent Learning Experience**: AI-powered contextual Q&A and content enhancement
- **Scalable Operations**: Event-driven architecture with automated workflows
- **Real-time Analytics**: Comprehensive metrics and monitoring
- **Enterprise-Grade**: Support for 10,000+ concurrent learners

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Git

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Database**: PostgreSQL (relational), NoSQL (documents)
- **Cache**: Redis
- **Message Queue**: RabbitMQ
- **Event Streaming**: Apache Kafka
- **Workflow Orchestration**: Temporal
- **Task Processing**: Celery

### AI/ML
- **AI Framework**: LangGraph
- **LLM Providers**: OpenAI, Groq, Anthropic
- **Vector Database**: Qdrant

### Observability
- **Metrics**: Prometheus
- **Visualization**: Grafana
- **Tracing**: Jaeger
- **Instrumentation**: OpenTelemetry

## Architecture

SmartCourse is a **microservices application in a monorepo, with a database per service**.
Each service (User, Course, Enrollment, Analytics, AI) is its own independently-runnable
FastAPI app that owns its own database and communicates with others only via **Kafka
events** and **HTTP** — never by sharing a database. See
[ADR-001](docs/architecture/adr-001-microservices-monorepo.md) for the decision and the
service-by-service migration plan.

## Project Structure

```text
smartcourse/
|-- services/                    # one folder per microservice (own app + own DB)
|   |-- user_service/
|   |   |-- api/                 # routes (thin HTTP layer)
|   |   |-- core/                # service + repository (logic + data access)
|   |   |-- models/              # this service's own DB models
|   |   |-- alembic/             # this service's own migrations
|   |   `-- main.py              # this service's FastAPI entry point
|   |-- course_service/          # (same internal shape)
|   |-- enrollment_service/
|   |-- analytics_service/
|   `-- ai_service/
|-- shared/                      # cross-service code ONLY (no business data models)
|   |-- events/                  # event contracts (Kafka message schemas)
|   |-- utils/                   # shared helpers
|   `-- config/                  # base configuration
|-- workflows/                   # Temporal workflows (cross-service orchestration)
|-- docker/                      # Docker configurations
|-- docker-compose.yml           # runs every service + its own database
|-- pyproject.toml               # Python project configuration
`-- requirements.txt             # Python dependencies
```

> **Migration note:** the repo is being moved from an initial modular monolith to the
> layout above **one service at a time** (User service first). Some paths (e.g. a
> top-level `main.py`, a shared `alembic/`, `shared/models/`) still reflect the monolith
> and will be relocated into their owning service as the migration proceeds.

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd SmartCourse
```

### 2. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your configuration
```

Application settings use the `SMARTCOURSE_` environment variable prefix.

### 3. Start Infrastructure Services

```bash
docker-compose up -d
```

This will start:
- PostgreSQL (port 5432)
- Redis (port 6379)
- RabbitMQ (ports 5672, 15672)
- Kafka (ports 9092, 29092)
- Temporal (ports 7233, 8233)
- Temporal UI (port 8088)
- Qdrant (port 6333)
- Prometheus (port 9090)
- Grafana (port 3000)
- Jaeger (port 16686)

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run Database Migrations

```bash
alembic upgrade head
```

### 6. Start the Application

```bash
python main.py
```

The API will be available at `http://localhost:8000`.

### 7. Access API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov

# Run specific test file
pytest tests/test_specific.py -v
```

## Monitoring & Observability

### Grafana Dashboard
- URL: `http://localhost:3000`
- Default credentials: `admin` / `admin`

### Prometheus
- URL: `http://localhost:9090`

### Jaeger Tracing
- URL: `http://localhost:16686`

### Temporal UI
- URL: `http://localhost:8088`

### RabbitMQ Management
- URL: `http://localhost:15672`
- Default credentials: `smartcourse` / `smartcourse_password`

## Development Commands

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View service logs
docker-compose logs -f [service_name]

# Restart a specific service
docker-compose restart [service_name]

# Run database migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Rollback migrations
alembic downgrade -1

# Start development server with auto-reload
uvicorn main:app --reload

# Format code
black .

# Lint code
ruff check .

# Type checking
mypy shared/ services/
```

## API Endpoints

### Health Check
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics endpoint

### API v1
- `GET /api/v1` - API v1 root

### Courses (Coming Soon)
- `POST /api/v1/courses` - Create a course
- `GET /api/v1/courses` - List courses
- `GET /api/v1/courses/{id}` - Get course details
- `PUT /api/v1/courses/{id}` - Update course
- `DELETE /api/v1/courses/{id}` - Delete course

### Users (Coming Soon)
- `POST /api/v1/users/register` - Register user
- `POST /api/v1/users/login` - User login
- `GET /api/v1/users/me` - Get current user

### Enrollments (Coming Soon)
- `POST /api/v1/enrollments` - Enroll in course
- `GET /api/v1/enrollments` - List enrollments
- `GET /api/v1/enrollments/{id}` - Get enrollment details

## Security

- JWT-based authentication
- Role-based access control (RBAC)
- Encrypted data at rest
- TLS for network communication
- Rate limiting and abuse prevention

## Documentation

Full documentation lives in [docs/](docs/README.md). Highlights:

- [Documentation Index](docs/README.md)
- [Product Requirements Document](docs/product/prd.md)
- [Project Requirements](docs/product/requirements.md)
- [Implementation Roadmap (2-month plan)](docs/planning/roadmap.md)
- [Configuration Reference](docs/reference/configuration.md)
- [Agent Guidelines](AGENTS.md)

## Contributing

1. Create a feature branch
2. Make your changes
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## License

[Your License Here]

## Team

SmartCourse Development Team

## Support

For issues and questions, please contact the development team.

---

**Note**: This is a development setup. For production deployment, additional security and configuration steps are required.
