from datetime import datetime, timezone

from ..extensions import db


class ModeratorVote(db.Model):
    __tablename__ = "moderator_votes"

    id = db.Column(db.Integer, primary_key=True)

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False,
    )

    voter_membership_id = db.Column(
        db.Integer,
        db.ForeignKey("event_memberships.id"),
        nullable=False,
    )

    candidate_id = db.Column(
        db.Integer,
        db.ForeignKey("moderator_candidates.id"),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    event = db.relationship(
        "Event",
        backref="moderator_votes",
    )

    voter_membership = db.relationship(
        "EventMembership",
        foreign_keys=[voter_membership_id],
        backref="moderator_votes_cast",
    )

    candidate = db.relationship(
        "ModeratorCandidate",
        backref="votes",
    )

    __table_args__ = (
        db.UniqueConstraint(
            "event_id",
            "voter_membership_id",
            name="uq_event_moderator_voter",
        ),
    )

    def __repr__(self):
        return (
            f"<ModeratorVote "
            f"event={self.event_id} "
            f"voter={self.voter_membership_id} "
            f"candidate={self.candidate_id}>"
        )
