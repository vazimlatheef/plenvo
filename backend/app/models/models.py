from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func, true
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    trainings_created: Mapped[list[Training]] = relationship(
        back_populates="created_by", foreign_keys="Training.created_by_id"
    )
    assignments_as_assignee: Mapped[list[Assignment]] = relationship(
        back_populates="assignee", foreign_keys="Assignment.assignee_user_id"
    )
    assignments_as_assigner: Mapped[list[Assignment]] = relationship(
        back_populates="assigned_by", foreign_keys="Assignment.assigned_by_id"
    )


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    youtube_video_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    created_by: Mapped[User] = relationship(back_populates="trainings_created", foreign_keys=[created_by_id])
    assignments: Mapped[list[Assignment]] = relationship(back_populates="training")


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (UniqueConstraint("training_id", "assignee_user_id", name="uq_assignments_training_assignee"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    training_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, index=True)
    assignee_user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="not_started")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    training: Mapped[Training] = relationship(back_populates="assignments")
    assignee: Mapped[User] = relationship(back_populates="assignments_as_assignee", foreign_keys=[assignee_user_id])
    assigned_by: Mapped[User] = relationship(back_populates="assignments_as_assigner", foreign_keys=[assigned_by_id])
