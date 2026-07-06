from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SMARTCOURSE_",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Settings
    APP_NAME: str = "SmartCourse"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Database Settings
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis Settings
    REDIS_URL: str
    REDIS_CACHE_TTL: int = 3600

    # RabbitMQ Settings
    RABBITMQ_URL: str
    RABBITMQ_TASK_QUEUE: str = "smartcourse_tasks"

    # Kafka Settings
    KAFKA_BOOTSTRAP_SERVERS: str
    KAFKA_CONSUMER_GROUP: str = "smartcourse_group"
    KAFKA_SCHEMA_REGISTRY_URL: str

    # Temporal Settings
    TEMPORAL_HOST: str
    TEMPORAL_PORT: int = 7233
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_TASK_QUEUE: str = "smartcourse_workflows"

    # Security Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI/LLM Settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    DEFAULT_LLM_PROVIDER: str = "openai"

    # Vector Database Settings
    QDRANT_URL: str
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "course_content"

    # Observability Settings
    JAEGER_AGENT_HOST: str = "localhost"
    JAEGER_AGENT_PORT: int = 6831
    JAEGER_SAMPLING_RATE: float = 0.1

    # Monitoring Settings
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    GRAFANA_ADMIN_PASSWORD: str = "admin"

    # CORS Settings
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    UPLOAD_DIR: str = "./uploads"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    BURST_LIMIT: int = 200

    # Background Worker Settings
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300
    CELERY_TASK_TIME_LIMIT: int = 600

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
