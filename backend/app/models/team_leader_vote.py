from datetime import datetime, timezone

from ..extensions import db


class TeamLeaderVote(db.Model):
    __tablename__ = "team_leader_votes"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    event_id = db.Column(
        db.Integer,
        db.ForeignKey("events.id"),
        nullable=False,
    )

    group_id = db.Column(
        db.Integer,
        db.ForeignKey("event_groups.id"),
        nullable=False,
    )

    voter_membership_id = db.Column(
        db.Integer,
        db.ForeignKey("event_memberships.id"),
        nullable=False,
    )

    candidate_membership_id = db.Column(
        db.Integer,
        db.ForeignKey("event_memberships.id"),
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    event = db.relationship(
        "Event",
        backref="team_leader_votes",
    )

    group = db.relationship(
        "EventGroup",
        backref="team_leader_votes",
    )

    voter_membership = db.relationship(
        "EventMembership",
        foreign_keys=[voter_membership_id],
    )

    candidate_membership = db.relationship(
        "EventMembership",
        foreign_keys=[candidate_membership_id],
    )

    __table_args__ = (
        db.UniqueConstraint(
            "group_id",
            "voter_membership_id",
            name="uq_team_leader_vote_voter",
        ),
    )

    def __repr__(self):
        return (
            f"<TeamLeaderVote "
            f"group={self.group_id} "
            f"voter={self.voter_membership_id} "
            f"candidate={self.candidate_membership_id}>"
        )
