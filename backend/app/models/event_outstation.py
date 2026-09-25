from datetime import datetime, timezone

from ..extensions import db


class EventOutstation(db.Model):
    __tablename__ = "event_outstations"

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

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    event = db.relationship(
        "Event",
        backref="outstations",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "event_id",
            "name",
            name="uq_event_outstation_name",
        ),
    )

    def __repr__(self):
        return f"<EventOutstation {self.name}>"
