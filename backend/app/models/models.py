from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, JSON, String, Text, Time, UniqueConstraint, false, func, true
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Organisation(Base):
    __tablename__ = "organisations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(300), unique=True, index=True, nullable=False)
    # free/trial default; paid tiers set on explicit upgrade
    plan_tier: Mapped[str] = mapped_column(String(32), nullable=False, server_default="team")
    # Billing currency locked at signup (GBP/EUR/USD/INR). Never re-detect later.
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="USD")
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subscription_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=false()
    )
    subscription_current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_warning_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_peak_member_count: Mapped[int] = mapped_column(nullable=False, server_default="1")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    users: Mapped[list[User]] = relationship(back_populates="organisation")
    contacts: Mapped[list[Contact]] = relationship(back_populates="organisation")
    projects: Mapped[list[Project]] = relationship(back_populates="organisation")
    trainings: Mapped[list[Training]] = relationship(back_populates="organisation")
    notes: Mapped[list[Note]] = relationship(back_populates="organisation")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organisation_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("organisations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    team_division: Mapped[str | None] = mapped_column(String(200), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    phone_country: Mapped[str | None] = mapped_column(String(8), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str | None] = mapped_column(String(8), nullable=True)
    team_size: Mapped[str | None] = mapped_column(String(20), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    do_not_email: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=false())
    overdue_email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=true())
    email_unsubscribe_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    verification_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    verification_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reset_token: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, nullable=True)
    reset_token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organisation: Mapped[Organisation | None] = relationship(back_populates="users")
    trainings_created: Mapped[list[Training]] = relationship(
        back_populates="created_by", foreign_keys="Training.created_by_id"
    )
    assignments_as_assignee: Mapped[list[Assignment]] = relationship(
        back_populates="assignee", foreign_keys="Assignment.assignee_user_id"
    )
    assignments_as_assigner: Mapped[list[Assignment]] = relationship(
        back_populates="assigned_by", foreign_keys="Assignment.assigned_by_id"
    )
    projects_managed: Mapped[list[Project]] = relationship(
        back_populates="manager", foreign_keys="Project.manager_id"
    )
    tasks_assigned: Mapped[list[Task]] = relationship(
        back_populates="assignee", foreign_keys="Task.assignee_id"
    )
    tasks_created: Mapped[list[Task]] = relationship(
        back_populates="created_by", foreign_keys="Task.created_by_id"
    )
    notes_created: Mapped[list[Note]] = relationship(
        back_populates="created_by", foreign_keys="Note.created_by_id"
    )
    contact_profile: Mapped[Contact | None] = relationship(
        back_populates="user", uselist=False, foreign_keys="Contact.user_id"
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Contact(Base):
    """Lightweight team member — name + email + role, no account required."""

    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("organisation_id", "email", name="uq_contacts_org_email"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    # Professional role label (not auth role): CEO, Manager, Team Member, Other, etc.
    role: Mapped[str] = mapped_column(String(40), nullable=False, server_default="Team Member")
    role_other: Mapped[str | None] = mapped_column(String(200), nullable=True)
    team_division: Mapped[str | None] = mapped_column(String(200), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, unique=True, index=True
    )
    invited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organisation: Mapped[Organisation] = relationship(back_populates="contacts")
    user: Mapped[User | None] = relationship(back_populates="contact_profile", foreign_keys=[user_id])
    tasks_assigned: Mapped[list[Task]] = relationship(
        back_populates="assignee_contact", foreign_keys="Task.assignee_contact_id"
    )
    assignments_as_assignee: Mapped[list["Assignment"]] = relationship(
        back_populates="assignee_contact", foreign_keys="Assignment.assignee_contact_id"
    )


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    links: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    manager_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organisation: Mapped[Organisation] = relationship(back_populates="projects")
    manager: Mapped[User] = relationship(back_populates="projects_managed", foreign_keys=[manager_id])
    tasks: Mapped[list[Task]] = relationship(back_populates="project")
    notes: Mapped[list[Note]] = relationship(back_populates="project")
    trainings: Mapped[list[Training]] = relationship(back_populates="project")


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    links: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="medium")
    source: Mapped[str] = mapped_column(String(20), nullable=False, server_default="manual")
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    due_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    project_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assignee_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assignee_contact_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    overdue_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organisation: Mapped[Organisation] = relationship()
    project: Mapped[Project | None] = relationship(back_populates="tasks")
    assignee: Mapped[User | None] = relationship(back_populates="tasks_assigned", foreign_keys=[assignee_id])
    assignee_contact: Mapped[Contact | None] = relationship(
        back_populates="tasks_assigned", foreign_keys=[assignee_contact_id]
    )
    created_by: Mapped[User] = relationship(back_populates="tasks_created", foreign_keys=[created_by_id])


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    project_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organisation: Mapped[Organisation] = relationship(back_populates="notes")
    project: Mapped[Project | None] = relationship(back_populates="notes")
    created_by: Mapped[User] = relationship(back_populates="notes_created", foreign_keys=[created_by_id])


class Training(Base):
    __tablename__ = "trainings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organisation_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[str] = mapped_column(String(20), nullable=False)
    storage_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    external_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    youtube_video_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    project_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    organisation: Mapped[Organisation] = relationship(back_populates="trainings")
    project: Mapped[Project | None] = relationship(back_populates="trainings")
    created_by: Mapped[User] = relationship(back_populates="trainings_created", foreign_keys=[created_by_id])
    assignments: Mapped[list[Assignment]] = relationship(back_populates="training")


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        UniqueConstraint("training_id", "assignee_user_id", name="uq_assignments_training_user"),
        UniqueConstraint("training_id", "assignee_contact_id", name="uq_assignments_training_contact"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    training_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("trainings.id", ondelete="CASCADE"), nullable=False, index=True)
    assignee_user_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    assignee_contact_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("contacts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    assigned_by_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="not_started")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    manager_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    training: Mapped[Training] = relationship(back_populates="assignments")
    assignee: Mapped[User | None] = relationship(
        back_populates="assignments_as_assignee", foreign_keys=[assignee_user_id]
    )
    assignee_contact: Mapped[Contact | None] = relationship(
        back_populates="assignments_as_assignee", foreign_keys=[assignee_contact_id]
    )
    assigned_by: Mapped[User] = relationship(back_populates="assignments_as_assigner", foreign_keys=[assigned_by_id])
    tokens: Mapped[list[TrainingToken]] = relationship(back_populates="assignment")


class TrainingToken(Base):
    __tablename__ = "training_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    assignment_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    assignment: Mapped[Assignment] = relationship(back_populates="tokens")
