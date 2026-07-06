from sqlalchemy import Column, String, Text, Integer, ForeignKey, Enum as SQLEnum, Numeric, Boolean
from sqlalchemy.orm import relationship
import enum
from shared.models.base import BaseModel

# Forward references for relationships
# User will be imported later to avoid circular imports


class CourseStatus(str, enum.Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    READY = "ready"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Course(BaseModel):
    """Course model"""
    __tablename__ = "courses"

    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    short_description = Column(String(500), nullable=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(SQLEnum(CourseStatus), default=CourseStatus.DRAFT, nullable=False)
    enrollment_limit = Column(Integer, nullable=True)
    current_enrollments = Column(Integer, default=0, nullable=False)
    price = Column(Numeric(10, 2), nullable=True)
    duration_hours = Column(Integer, nullable=True)
    difficulty_level = Column(String(50), nullable=True)  # beginner, intermediate, advanced
    thumbnail_url = Column(String(500), nullable=True)
    language = Column(String(10), default="en", nullable=False)

    # Relationships
    instructor = relationship("User", back_populates="created_courses", foreign_keys=[instructor_id])
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    enrollments = relationship("Enrollment", back_populates="course", cascade="all, delete-orphan")


class Module(BaseModel):
    """Module model for course organization"""
    __tablename__ = "modules"

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    order = Column(Integer, default=0, nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")


class Lesson(BaseModel):
    """Lesson model"""
    __tablename__ = "lessons"

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    order = Column(Integer, default=0, nullable=False)
    video_url = Column(String(500), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)

    # Relationships
    module = relationship("Module", back_populates="lessons")
    assets = relationship("Asset", back_populates="lesson", cascade="all, delete-orphan")


class Asset(BaseModel):
    """Asset model for learning materials"""
    __tablename__ = "assets"

    title = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, video, image, document
    file_size = Column(Integer, nullable=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=True)
    description = Column(Text, nullable=True)

    # Relationships
    lesson = relationship("Lesson", back_populates="assets")
