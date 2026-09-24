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

    status = db.Column(
        db.String(50),
        nullable=False,
        default="DRAFT",
    )

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
