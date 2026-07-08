from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum, DateTime, Boolean, func, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from shared.models.base import BaseModel


class EnrollmentStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    DROPPED = "dropped"
    SUSPENDED = "suspended"


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
    status = Column(SQLEnum(EnrollmentStatus), default=EnrollmentStatus.ACTIVE, nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    progress_percentage = Column(Integer, default=0, nullable=False)
    certificate_issued = Column(Boolean, default=False, nullable=False)
    certificate_url = Column(String(500), nullable=True)

    # Relationships
    student = relationship("User", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
    progress_records = relationship("Progress", back_populates="enrollment", cascade="all, delete-orphan")


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
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    time_spent_minutes = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    enrollment = relationship("Enrollment", back_populates="progress_records")
