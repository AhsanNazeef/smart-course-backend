# SmartCourse — Intelligent Course Delivery Platform

## Overview

EduCorp is building **SmartCourse**, an intelligent, large-scale learning platform designed to support modern digital education for universities, enterprises, and training academies.

The company is experiencing rapid growth in enrolled learners and instructors, which has exposed several limitations in their current systems.

---

# Current Challenges

1. **Slow Content Publishing**
   - Content publishing is slow and manual.
   - Instructors struggle to launch new courses and update existing ones.

2. **Poor Learning Experience**
   - Students struggle to find relevant information.
   - No intelligent search.
   - No contextual assistance.
   - No adaptive learning support.

3. **Inconsistent Data**
   - Course data, learner progress, and analytics are scattered.
   - Reporting dashboards often differ from the actual platform state.

4. **Performance Issues**
   - High user traffic causes delays.
   - Enrollments, notifications, and background jobs become slow.

5. **Unused Learning Data**
   - Rich interaction data is generated.
   - It is not utilized for recommendations or learning improvements.

---

# Business Goals & Vision

SmartCourse should provide the following capabilities.

## 1. Robust Course Management

Instructors should be able to:

- Create courses
- Define modules
- Upload learning materials
- Publish course updates

Students should be able to:

- Browse courses
- Enroll in courses
- Track learning progress
- Interact with course content

---

## 2. Scalable & Reliable Operations

Publishing a course should automatically trigger:

- Content indexing
- Content extraction
- Intelligent search preparation

Enrollment should automatically trigger:

- Progress initialization
- Analytics updates
- Notifications

---

## 3. Consistent Learner Data

The platform must maintain reliable and durable data for:

- Enrollments
- Progress
- Course completion
- Certificates

The data should always remain easy to query and consistent.

---

## 4. Intelligent Learning Experience

Students should be able to:

- Ask questions about course material
- Receive context-aware AI answers

Instructors should be able to generate:

- Course summaries
- Quiz questions
- Explanations
- Learning objectives

---

## 5. Smooth Real-Time Interaction

AI-generated responses may require long-running processing.

The system should:

- Stream responses incrementally
- Avoid blocking other users
- Maintain responsiveness

---

## 6. Long-Term Scalability

The platform should support:

- Tens of thousands of concurrent learners
- Traffic spikes during course launches
- Corporate training events
- Reliable background workflows

---

# Core Functional Requirements

## 1. Course & User Management

The system should support:

### Course Management

- Create courses
- Update courses
- Manage modules
- Manage learning assets

### User Management

Support the following user roles:

- Student
- Instructor
- Admin

### Enrollment Rules

The system should handle:

- Duplicate enrollments
- Enrollment limits
- Course prerequisites
- Enrollment history

Every enrollment and update must remain consistent across the platform.

---

## 2. Content Publishing Workflow

When an instructor publishes or updates a course:

- Analyze course content
- Break content into:
  - Modules
  - Lessons
  - Chunks

Store processed data to support:

- Fast retrieval
- Intelligent search
- Context-based queries

The system should:

- Mark the course as **Ready** after successful processing.
- Prevent partial failures from corrupting the workflow.

---

## 3. Enrollment Workflow

When a student enrolls:

- Record enrollment
- Initialize learning progress
- Update analytics
- Send welcome notifications (if applicable)

The workflow must support:

- High throughput
- Idempotency
- Backpressure handling
- Failure recovery
- No duplicate processing

---

## 4. Intelligent Learning Assistant

### A. Contextual Q&A

Students can:

- Ask questions about course material

The system should:

- Retrieve relevant course sections
- Generate context-aware answers

---

### B. Content Enhancement

Instructors can request:

- Summaries
- Learning objectives
- Quiz questions
- Explanations

The system should:

- Generate content from course material
- Support streaming responses
- Handle incomplete or ambiguous requests gracefully

---

## 5. Distributed & Event-Driven Behaviors

The following events should trigger background workflows:

- Course publishing
- Enrollment analytics
- Notifications
- AI preparation/indexing

These workflows should:

- Run independently
- Be traceable
- Recover from failures
- Prevent duplicate processing
- Handle workload spikes

---

## 6. Analytics Metrics

The platform should provide the following metrics.

### Users

- Total Students
- Total Instructors

### Courses

- Total Published Courses
- Most Popular Courses

### Enrollment

- New Enrollments (Day/Week/Month)
- Average Courses per Student

### Learning Progress

- Course Completion Rate
- Average Time to Complete Course

### AI Assistant

- Number of questions asked
- Number of answers generated
- Type of AI assistance used

### Reliability

- Failed background events
- Workflow failures
- Notification failures

---

## 7. System Observability & Reliability

The platform must provide:

- Clear separation of responsibilities
- Centralized logging
- Monitoring
- Distributed tracing

Failures should be easy to diagnose for:

- Course publishing
- Enrollment workflows
- AI assistant
- Background processing

High consistency and data accuracy are mandatory.

---

# Technology Stack

## Backend

- Python
- FastAPI
- PostgreSQL
- NoSQL Database
- Redis
- Celery Workers
- RabbitMQ
- Kafka
- Schema Registry
- Temporal (Workflow Orchestration)

---

## AI

- LangGraph
- LLM Provider
  - OpenAI
  - Groq
  - Anthropic
- Vector Database (Choose the most suitable)

---

## Observability & Monitoring

- Prometheus
- Grafana
- Jaeger
- OpenTelemetry

---

## DevOps

- Docker
- Docker Compose

---

# Expected Outcomes

By the end of the assignment, SmartCourse should:

## 1. Product Requirements Document (PRD)

Create a PRD containing:

- Key use cases
- Functional requirements
- Non-functional requirements
- Implementation timeline
- Milestones
- Feature-to-deliverable traceability

---

## 2. Complete Course Lifecycle

Support:

- Course creation
- Course publishing
- Student engagement
- Course completion

---

## 3. Reliable Background Operations

Ensure reliable execution of:

- Publishing workflows
- Indexing
- Analytics
- Notifications

No data loss or duplicate processing should occur.

---

## 4. Intelligent Learning Assistant

Provide an AI assistant capable of:

- Answering student questions
- Enhancing instructor content

---

## 5. Scalability

Scale efficiently for:

- Real-time APIs
- Background workers
- Increasing user traffic

---

## 6. High Architectural Quality

The solution will be evaluated based on:

- Clean code
- Maintainability
- SOLID principles
- Appropriate design patterns
- Workflow orchestration
- Stability under failures
- Documentation quality
- Architecture diagrams
- Test coverage
- Test quality

---

## 7. Learning Objective

This assignment is intended to help you deeply understand:

- Software architecture
- Design principles
- Workflow orchestration
- Distributed systems
- Event-driven architecture
- AI integration
- Backend scalability
- Observability
- Modern backend technologies

The objective is not only to complete the milestones but also to gain practical experience with the technologies and architectural patterns involved.