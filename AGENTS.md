# SmartCourse — Agent Guidelines

**Version:** 1.1  
**Date:** July 6, 2026  
**Project:** SmartCourse - Intelligent Course Delivery Platform

---

## Project Overview

SmartCourse is an intelligent, large-scale learning platform for universities, enterprises, and training academies. The platform uses AI-powered features and robust architectural design to address challenges in content publishing, learning experience, data consistency, performance, and learning data utilization.

**Organization:** EduCorp  
**Primary Users:** Students, Instructors, Administrators

---

## Quick Reference

### Key Documents
- **Project Requirements:** `project-requirements.md` - Original project specification
- **PRD:** `PRD.md` - Detailed Product Requirements Document
- **AGENTS.md:** This file - Agent working guidelines

### Technology Stack
- **Backend:** Python, FastAPI, PostgreSQL, NoSQL, Redis
- **Workflow:** Temporal, Celery, RabbitMQ, Kafka
- **AI:** LangGraph, OpenAI/Groq/Anthropic, Vector DB
- **Observability:** Prometheus, Grafana, Jaeger, OpenTelemetry
- **DevOps:** Docker, Docker Compose

### Project Goals
1. Robust course management for instructors and students
2. Scalable and reliable operations with automated workflows
3. Consistent learner data across all platform components
4. AI-powered learning experience with contextual assistance
5. Support for 10,000+ concurrent learners

---

## Architecture Overview

### Microservices Architecture
The platform follows a microservices architecture with clear separation of concerns:

**Core Services:**
- **Course Service:** Course creation, management, publishing
- **User Service:** Authentication, authorization, user management
- **Enrollment Service:** Enrollment handling, progress tracking
- **Analytics Service:** Metrics collection and reporting
- **AI Service:** LangGraph-based AI assistant for Q&A and content generation

**Infrastructure Services:**
- **API Gateway:** FastAPI-based REST API layer
- **Workflow Engine:** Temporal for complex workflow orchestration
- **Event Bus:** Kafka for event streaming and async communication
- **Message Queue:** RabbitMQ for task processing
- **Background Workers:** Celery for async job execution

**Data Layer:**
- **PostgreSQL:** Relational data (users, courses, enrollments)
- **NoSQL:** Document storage (course content, assets)
- **Redis:** Caching and session management
- **Vector Database:** Semantic search and AI context retrieval

---

## Key Architectural Patterns

### 1. Event-Driven Architecture
- Course publishing triggers content indexing events
- Enrollment triggers analytics and notification events
- All background workflows are event-driven
- Use Kafka for event streaming with schema registry

### 2. Workflow Orchestration
- Temporal orchestrates complex multi-step workflows
- Course publishing workflow: analysis → indexing → preparation → ready state
- Enrollment workflow: recording → progress init → analytics → notifications
- All workflows must be idempotent and recoverable

### 3. CQRS (Command Query Responsibility Segregation)
- Separate read and write models for performance
- Analytics queries use optimized read models
- Enrollment and course updates use write models with strong consistency

### 4. Saga Pattern for Distributed Transactions
- Course publishing spans multiple services
- Enrollment workflow involves multiple steps
- Compensating actions for workflow failures
- Ensure data consistency across services

---

## Critical Requirements for Agents

### Non-Negotiable Requirements

1. **Data Consistency**
   - All enrollment operations must be consistent
   - No partial updates or orphaned records
   - Strong consistency for critical operations (enrollments, progress)
   - Eventual consistency acceptable for analytics

2. **No Data Loss**
   - Background workflows must not lose data
   - Idempotent operations to prevent duplicate processing
   - Reliable event delivery with at-least-once semantics
   - Dead letter queues for failed events

3. **Workflow Reliability**
   - 99.9% success rate for background workflows
   - Automatic retry with exponential backoff
   - Failure recovery without data corruption
   - Traceable workflow execution with unique IDs

4. **Performance Targets**
   - API response time: <200ms (95th percentile)
   - AI streaming latency: <100ms to first token
   - Support 10,000+ concurrent users
   - Search response: <500ms for complex queries

5. **Scalability**
   - Horizontal scaling for all services
   - Auto-scaling based on load
   - Handle 10x traffic spikes during course launches
   - Independent scaling of background workers

---

## Code Standards & Patterns

### Python/FastAPI Guidelines

**Project Structure:**
```
smartcourse/
├── services/
│   ├── course_service/
│   ├── user_service/
│   ├── enrollment_service/
│   ├── analytics_service/
│   └── ai_service/
├── shared/
│   ├── models/
│   ├── schemas/
│   ├── utils/
│   └── config/
├── workflows/
├── tests/
└── docker/
```

**Code Style:**
- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- SOLID principles for class design
- Dependency injection for testability
- Async/await for I/O operations

**API Design:**
- RESTful endpoints with proper HTTP methods
- Pydantic models for request/response validation
- Consistent error responses with proper status codes
- API versioning (e.g., /api/v1/)
- OpenAPI/Swagger documentation

**Database Patterns:**
- SQLAlchemy ORM with async support
- Repository pattern for data access
- Database migrations with Alembic
- Connection pooling for performance
- Transaction management for consistency

### Workflow Orchestration (Temporal)

**Workflow Design:**
- Define workflows as Python activities
- Use Temporal's workflow retry policies
- Implement compensating activities for rollbacks
- Workflow timeouts and heartbeats
- Child workflows for complex operations

**Example Workflow Pattern:**
```python
@workflow.defn
class CoursePublishingWorkflow:
    @workflow.run
    async def run(self, course_id: str) -> str:
        # Step 1: Analyze content
        await workflow.execute_activity(
            analyze_content,
            course_id,
            start_to_close_timeout=timedelta(minutes=10)
        )
        
        # Step 2: Index content
        await workflow.execute_activity(
            index_content,
            course_id,
            start_to_close_timeout=timedelta(minutes=5)
        )
        
        # Step 3: Mark as ready
        await workflow.execute_activity(
            mark_course_ready,
            course_id,
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        return course_id
```

### Event Streaming (Kafka)

**Event Design:**
- Use Avro or JSON schemas with Schema Registry
- Event naming: `{aggregate}.{action}` (e.g., `course.published`)
- Include event metadata (timestamp, correlation ID, causation ID)
- Idempotent event consumers

**Key Events:**
- `course.created`, `course.updated`, `course.published`
- `enrollment.created`, `enrollment.completed`
- `progress.updated`, `certificate.issued`
- `ai.question.asked`, `ai.answer.generated`

### AI Integration (LangGraph)

**AI Workflow Patterns:**
- Use LangGraph for multi-step AI workflows
- Implement streaming responses for real-time interaction
- Context retrieval from vector database
- Fallback mechanisms for AI failures
- Rate limiting and cost management

**RAG Pattern for Q&A:**
```python
# 1. Retrieve relevant context
context = await vector_db.search(query, course_id)

# 2. Generate answer with context
answer = await llm.generate(
    prompt=f"Context: {context}\nQuestion: {query}",
    stream=True
)

# 3. Stream response to client
async for chunk in answer:
    await send_to_client(chunk)
```

---

## Testing Strategy

### Test Coverage Requirements
- **Target:** >80% code coverage
- **Critical paths:** 100% coverage for enrollment and publishing workflows
- **Integration tests:** All service interactions
- **End-to-end tests:** Critical user journeys

### Test Types

**Unit Tests:**
- Test individual functions and classes
- Mock external dependencies (databases, APIs)
- Fast execution (<1 second per test)
- Use pytest with async support

**Integration Tests:**
- Test service interactions
- Use testcontainers for real databases
- Test event streaming with test Kafka
- Test workflow execution

**End-to-End Tests:**
- Complete user journeys (course creation → publishing → enrollment)
- Test background workflow execution
- Test AI assistant integration
- Performance tests for scalability

### Test Data Management
- Use factory pattern for test data creation
- Clean up test data after each test
- Use deterministic test data
- Seed database with consistent test data

---

## Common Tasks & Patterns

### Adding a New API Endpoint

1. Define Pydantic schema for request/response
2. Create repository method for data access
3. Implement service layer with business logic
4. Add FastAPI route with proper HTTP method
5. Add authentication/authorization middleware
6. Write unit and integration tests
7. Update API documentation

### Adding a New Background Workflow

1. Define Temporal workflow with activities
2. Implement retry policies and timeouts
3. Add compensating activities for failures
4. Register workflow with Temporal server
5. Add event triggers for workflow initiation
6. Add monitoring and logging
7. Write integration tests for workflow

### Adding a New AI Feature

1. Define LangGraph workflow for AI logic
2. Implement context retrieval from vector DB
3. Add streaming support for real-time responses
4. Implement fallback mechanisms
5. Add rate limiting and cost controls
6. Add monitoring for AI usage
7. Write tests with mocked LLM responses

### Adding a New Analytics Metric

1. Define metric in data model
2. Add event listener for metric updates
3. Implement metric calculation logic
4. Add to analytics service API
5. Update monitoring dashboards
6. Write tests for metric accuracy

---

## Error Handling & Resilience

### Error Handling Patterns

**API Errors:**
- Use HTTP status codes appropriately
- Return consistent error response format
- Include error codes for client handling
- Log errors with sufficient context
- Implement rate limiting for abuse prevention

**Workflow Errors:**
- Implement retry policies with exponential backoff
- Use dead letter queues for permanently failed events
- Alert on critical workflow failures
- Manual intervention processes for unrecoverable failures
- Workflow state inspection for debugging

**Database Errors:**
- Implement connection retry logic
- Use transactions for multi-step operations
- Handle deadlock with retry
- Circuit breaker for database outages
- Connection pooling for performance

### Monitoring & Alerting

**Key Metrics to Monitor:**
- API response times and error rates
- Workflow success/failure rates
- Database connection pool usage
- Event queue depth
- AI API costs and latency
- Cache hit rates

**Alert Thresholds:**
- API error rate >1% for 5 minutes
- Workflow failure rate >0.1% for 10 minutes
- Database connection pool >80% utilization
- Event queue depth >1000 for 5 minutes
- AI API latency >5 seconds

---

## Deployment & DevOps

### Local Development

**Prerequisites:**
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL, Redis, Kafka (via Docker)
- Temporal server (via Docker)

**Development Commands:**
```bash
# Start all services
docker-compose up -d

# Run migrations
alembic upgrade head

# Run tests
pytest tests/ -v --cov

# Start development server
uvicorn services.api.main:app --reload
```

### Build & Deployment

**Docker Strategy:**
- Multi-stage builds for optimized images
- Separate images for each service
- Use .dockerignore to minimize image size
- Tag images with git commit SHA

**Environment Variables:**
- Use environment-specific configuration
- Never commit secrets to repository
- Use secret management for production
- Validate required variables on startup

---

## Performance Optimization

### Caching Strategy
- Cache frequently accessed course data in Redis
- Cache user sessions and permissions
- Cache AI responses for identical queries
- Implement cache invalidation on data updates
- Monitor cache hit rates

### Database Optimization
- Use database indexes for frequent queries
- Implement read replicas for analytics queries
- Use connection pooling
- Optimize complex queries with EXPLAIN ANALYZE
- Partition large tables by date

### Async Processing
- Use Celery for background tasks
- Implement task prioritization
- Use async I/O for database and API calls
- Stream large responses instead of buffering
- Implement backpressure handling

---

## Security Considerations

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- Permission checks at service layer
- Secure API key management
- Regular security audits

### Data Protection
- Encrypt sensitive data at rest
- Use TLS for all network communication
- Implement input validation and sanitization
- SQL injection prevention with parameterized queries
- XSS prevention with proper output encoding

### API Security
- Rate limiting per user/IP
- API key authentication for external integrations
- CORS configuration for web clients
- Request signing for webhooks
- Audit logging for sensitive operations

---

## Documentation Standards

### Code Documentation
- Docstrings for all public functions and classes
- Type hints for function signatures
- Inline comments for complex logic
- Architecture diagrams for system design
- API documentation with OpenAPI/Swagger

### Project Documentation
- Keep README.md updated with setup instructions
- Document architecture decisions (ADRs)
- Maintain changelog for significant changes
- Document deployment procedures
- Create runbooks for common operations

---

## Communication & Collaboration

### Git Workflow
- Use feature branches for new development
- Pull requests for code review
- Descriptive commit messages
- Semantic versioning for releases
- Tag releases in git

### Code Review Guidelines
- Review for code quality and consistency
- Check for security vulnerabilities
- Verify test coverage
- Ensure documentation is updated
- Approve only when all checks pass

---

## Learning-First Development Workflow

This project is being built as both a production-quality backend system and a guided learning track. Agents must treat every meaningful change as a small engineering lesson, not just a code delivery.

### Step-by-Step Delivery
- Build in small, reviewable vertical slices instead of large hidden rewrites.
- Before substantial edits, briefly explain the immediate goal and the files or concepts involved.
- After implementation, summarize what changed, why it was added, how it fits the SmartCourse architecture, and how to verify it locally.
- Prefer one complete, working slice over several half-finished layers.
- Keep each step aligned with the PRD, existing architecture, and senior engineering practices.

### Explain What Was Added
For every new feature, service, workflow, database model, migration, queue, event, AI component, or observability component, include:

1. **What was added** - the concrete files, endpoints, models, services, or infrastructure.
2. **Why it was added** - the product or architecture requirement it supports.
3. **How it works** - the key flow in plain language before diving into details.
4. **How to run or test it** - commands, URLs, or expected outputs.
5. **What to study next** - focused links to official documentation or high-quality references for the exact technologies used.

### Study Links Requirement
- Provide study links whenever introducing or materially changing a technology such as FastAPI, SQLAlchemy, Alembic, PostgreSQL, Redis, RabbitMQ, Kafka, Temporal, Celery, LangGraph, OpenAI/Groq/Anthropic integration, Qdrant, Prometheus, Grafana, Jaeger, OpenTelemetry, Docker, or Docker Compose.
- Prefer official documentation first, then reputable tutorials only when official docs are too reference-heavy for the current learning step.
- Keep links focused: include only the resources relevant to the current change instead of dumping the entire stack every time.
- When a concept is advanced, include a short glossary of the important terms used in that change.

### Baseline Official Study Resources
- FastAPI: https://fastapi.tiangolo.com/
- SQLAlchemy asyncio: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Alembic migrations: https://alembic.sqlalchemy.org/en/latest/
- PostgreSQL: https://www.postgresql.org/docs/
- Docker Compose: https://docs.docker.com/compose/
- Temporal Python SDK: https://docs.temporal.io/develop/python
- Kafka: https://kafka.apache.org/documentation/
- Redis: https://redis.io/docs/latest/
- RabbitMQ tutorials: https://www.rabbitmq.com/tutorials
- LangGraph: https://docs.langchain.com/oss/python/langgraph/overview
- Prometheus: https://prometheus.io/docs/prometheus/latest/getting_started/
- OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/

### Senior Engineering Expectations
- Explain tradeoffs, not only the chosen solution.
- Call out risks, missing production hardening, and follow-up work honestly.
- Add tests, migrations, observability, idempotency, and error handling when the scope requires them.
- Avoid premature complexity; introduce distributed systems tools only when the current step needs them or when the PRD milestone calls for them.
- Document important architecture decisions as ADRs when they affect long-term direction.

---

## Troubleshooting Common Issues

### Workflow Failures
1. Check Temporal workflow history
2. Review activity logs for errors
3. Verify external service availability
4. Check event queue for stuck events
5. Review retry policy configuration

### Performance Issues
1. Check API response times in monitoring
2. Review database query performance
3. Check cache hit rates
4. Review background worker queue depth
5. Profile slow endpoints

### AI Integration Issues
1. Check LLM API status and quotas
2. Review vector database query performance
3. Verify context retrieval accuracy
4. Check streaming implementation
5. Review AI usage costs

---

## Learning Objectives for This Project

This project is designed to help you gain practical experience with:

- **Software Architecture:** Microservices, event-driven design, CQRS
- **Design Principles:** SOLID principles, design patterns
- **Workflow Orchestration:** Temporal for complex workflows
- **Distributed Systems:** Event streaming, message queues
- **Event-Driven Architecture:** Kafka, event sourcing
- **AI Integration:** LangGraph, RAG patterns, LLM integration
- **Backend Scalability:** Horizontal scaling, caching, optimization
- **Observability:** Monitoring, tracing, logging
- **Modern Backend Technologies:** FastAPI, async Python, modern databases

The objective is not only to complete the milestones but also to deeply understand these technologies and architectural patterns.

---

## Getting Started Checklist

When starting work on this project:

1. **Read the PRD** (`PRD.md`) - Understand requirements and use cases
2. **Review the architecture** - Understand the microservices design
3. **Set up local environment** - Docker Compose for all dependencies
4. **Review existing code** - Understand code patterns and conventions
5. **Run tests** - Ensure test suite passes
6. **Check monitoring** - Verify observability stack is working
7. **Join team communication** - Understand collaboration workflow

---

## Quick Commands Reference

```bash
# Development
docker-compose up -d                    # Start all services
docker-compose down                     # Stop all services
docker-compose logs -f [service]        # View service logs
pytest tests/ -v --cov                  # Run tests with coverage
alembic upgrade head                    # Run database migrations
alembic revision --autogenerate -m "msg" # Create migration

# Temporal
temporal workflow start [workflow]      # Start workflow
temporal workflow describe [id]         # Describe workflow
temporal task-queue list                # List task queues

# Docker
docker build -t smartcourse/[service] . # Build service image
docker push registry/smartcourse/[service] # Push image
docker ps                               # List running containers
docker exec -it [container] bash       # Enter container shell

# Monitoring
curl http://localhost:9090/metrics      # Prometheus metrics
curl http://localhost:16686/search     # Jaeger tracing UI
```

---

## Contact & Support

For questions or issues related to this project:

1. Check existing documentation (PRD, this file, README)
2. Review architecture diagrams and ADRs
3. Check monitoring dashboards for system issues
4. Consult with team members for design decisions
5. Create issues for bugs or feature requests

---

**Last Updated:** July 6, 2026  
**Maintained by:** SmartCourse Development Team
