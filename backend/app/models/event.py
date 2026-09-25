from datetime import datetime, timezone

from ..extensions import db


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(150),
        nullable=False,
    )

    slug = db.Column(
        db.String(180),
        unique=True,
        nullable=False,
        index=True,
    )

    description = db.Column(
        db.Text,
        nullable=True,
    )

    # Event location
    venue = db.Column(
        db.String(150),
        nullable=False,
    )

    address = db.Column(
        db.String(255),
        nullable=True,
    )

    city = db.Column(
        db.String(100),
        nullable=True,
    )

    country = db.Column(
        db.String(100),
        nullable=True,
        default="Kenya",
    )

    # Event schedule
    starts_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )

    ends_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
    )

    # Event access
    access_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    # Event lifecycle
    status = db.Column(
        db.String(50),
        nullable=False,
        default="DRAFT",
    )

    registration_status = db.Column(
        db.String(50),
        nullable=False,
        default="CLOSED",
    )

    moderator_voting_status = db.Column(
        db.String(50),
        nullable=False,
        default="NOT_STARTED",
    )

    voting_status = db.Column(
        db.String(50),
        nullable=False,
        default="NOT_STARTED",
    )

    # Ownership
    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    creator = db.relationship(
        "User",
        backref="created_events",
    )

    def __repr__(self):
        return f"<Event {self.name}>"
