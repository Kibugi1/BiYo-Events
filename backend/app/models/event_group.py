from datetime import datetime, timezone

from ..extensions import db


class EventGroup(db.Model):
    __tablename__ = "event_groups"

    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False,
    )

    name = db.Column(
        db.String(100),
        nullable=False,
    )

    display_name = db.Column(
        db.String(100),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    event = db.relationship(
        "Event",
        backref="groups",
    )

    election_status = db.Column(
    db.String(50),
    nullable=False,
    default="NOT_STARTED",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "event_id",
            "name",
            name="uq_event_group_name",
        ),
    )

    def __repr__(self):
        return f"<EventGroup {self.name}>"
