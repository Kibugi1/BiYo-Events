from sqlalchemy import func

from ..extensions import db
from ..models.event_group import EventGroup
from ..models.event_membership import EventMembership
from ..models.team_leader_vote import TeamLeaderVote


class TeamLeaderService:

    @staticmethod
    def vote(event, voter, group_id, candidate_membership_id):
        if group_id is None:
            raise ValueError("Team is required")

        group = EventGroup.query.filter_by(
            id=group_id,
            event_id=event.id,
        ).first()

        if group is None:
            raise ValueError("Team not found")

        if group.election_status != "OPEN":
            raise ValueError("Team leader election is not open")

        voter_membership = EventMembership.query.filter_by(
            event_id=event.id,
            user_id=voter.id,
            group_id=group_id,
        ).first()

        if voter_membership is None:
            raise ValueError("You must be a member of this team to vote")

        candidate = EventMembership.query.filter_by(
            id=candidate_membership_id,
            event_id=event.id,
            group_id=group_id,
        ).first()

        if candidate is None:
            raise ValueError("Candidate must be a member of this team")

        if candidate.id == voter_membership.id:
            raise ValueError("You cannot vote for yourself")

        existing_vote = TeamLeaderVote.query.filter_by(
            group_id=group_id,
            voter_membership_id=voter_membership.id,
        ).first()

        if existing_vote is not None:
            raise ValueError("You have already voted for a team leader")

        vote = TeamLeaderVote(
            event_id=event.id,
            group_id=group_id,
            voter_membership_id=voter_membership.id,
            candidate_membership_id=candidate.id,
        )

        db.session.add(vote)
        db.session.commit()

        return vote

    @staticmethod
    def count_votes(group_id):
        results = (
            db.session.query(
                TeamLeaderVote.candidate_membership_id,
                func.count(TeamLeaderVote.id).label("vote_count"),
            )
            .filter_by(group_id=group_id)
            .group_by(TeamLeaderVote.candidate_membership_id)
            .order_by(
                func.count(TeamLeaderVote.id).desc(),
                TeamLeaderVote.candidate_membership_id.asc(),
            )
            .all()
        )

        return [
            {
                "membership_id": membership_id,
                "votes": vote_count,
            }
            for membership_id, vote_count in results
        ]

    @staticmethod
    def open_election(group):
        if group.election_status == "OPEN":
            raise ValueError("Team leader election is already open")

        if group.election_status in {"CLOSED", "FINALIZED"}:
            raise ValueError("Team leader election cannot be reopened")

        group.election_status = "OPEN"
        db.session.commit()

        return group

    @staticmethod
    def close_election(group):
        if group.election_status != "OPEN":
            raise ValueError("Team leader election is not open")

        group.election_status = "CLOSED"
        db.session.commit()

        return group

    @staticmethod
    def finalize_election(group):
        if group.election_status != "CLOSED":
            raise ValueError(
                "Team leader election must be closed before finalizing"
            )

        results = TeamLeaderService.count_votes(group.id)

        if not results:
            raise ValueError("No votes were cast")

        highest_vote_count = results[0]["votes"]

        winners = [
            result
            for result in results
            if result["votes"] == highest_vote_count
        ]

        if len(winners) > 1:
            raise ValueError("Team leader election ended in a tie")

        winner_membership_id = winners[0]["membership_id"]

        winner = EventMembership.query.filter_by(
            id=winner_membership_id,
            group_id=group.id,
            event_id=group.event_id,
        ).first()

        if winner is None:
            raise ValueError("Winning team member could not be found")

        EventMembership.query.filter_by(
            group_id=group.id,
            event_id=group.event_id,
        ).update(
            {"team_role": "MEMBER"},
            synchronize_session=False,
        )

        winner.team_role = "LEADER"
        group.election_status = "FINALIZED"

        db.session.commit()

        return winner
