from datetime import datetime, timezone

from ..extensions import db


class ModeratorCandidate(db.Model):
    __tablename__ = "moderator_candidates"

    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False,
    )

    membership_id = db.Column(
        db.Integer,
        db.ForeignKey("event_memberships.id"),
        nullable=False,
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="ACTIVE",
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    event = db.relationship(
        "Event",
        backref="moderator_candidates",
    )

    membership = db.relationship(
        "EventMembership",
        backref="moderator_candidate",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "event_id",
            "membership_id",
            name="uq_event_moderator_candidate",
        ),
    )

    def __repr__(self):
        return (
            f"<ModeratorCandidate "
            f"event={self.event_id} "
            f"membership={self.membership_id}>"
        )
