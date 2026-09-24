from datetime import datetime, timezone

from ..extensions import db


class EventMembership(db.Model):
    __tablename__ = "event_memberships"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False,
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
    )

    role = db.Column(
        db.String(50),
        nullable=False,
        default="PARTICIPANT",
    )

    joined_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    event = db.relationship(
        "Event",
        backref="memberships",
    )

    user = db.relationship(
        "User",
        backref="event_memberships",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "event_id",
            "user_id",
            name="uq_event_user",
        ),
    )

    def __repr__(self):
        return (
            f"<EventMembership "
            f"event={self.event_id} "
            f"user={self.user_id} "
            f"role={self.role}>"
        )
