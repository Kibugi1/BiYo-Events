from sqlalchemy import func

from ..extensions import db
from ..models import EventMembership, ModeratorCandidate, ModeratorVote
from .moderator_constants import ModeratorCandidateStatus, ModeratorVotingStatus


class ModeratorError(Exception):
    """Base exception for moderator election errors."""


class ModeratorService:

    @staticmethod
    def volunteer(event, user):
        membership = EventMembership.query.filter_by(
            event_id=event.id,
            user_id=user.id,
        ).first()

        if membership is None:
            raise ModeratorError("You must be an event member to volunteer.")

        if membership.role != "PARTICIPANT":
            raise ModeratorError("Only participants can volunteer as candidates.")

        if event.moderator_voting_status != ModeratorVotingStatus.NOT_STARTED:
            raise ModeratorError(
                "Moderator volunteering is closed once voting has started."
            )

        existing_candidate = ModeratorCandidate.query.filter_by(
            event_id=event.id,
            membership_id=membership.id,
        ).first()

        if existing_candidate:
            return existing_candidate, False

        candidate = ModeratorCandidate(
            event_id=event.id,
            membership_id=membership.id,
            status=ModeratorCandidateStatus.ACTIVE,
        )

        db.session.add(candidate)
        db.session.commit()

        return candidate, True

    @staticmethod
    def withdraw(event, user):
        membership = EventMembership.query.filter_by(
            event_id=event.id,
            user_id=user.id,
        ).first()

        if membership is None:
            raise ModeratorError("You must be an event member.")

        candidate = ModeratorCandidate.query.filter_by(
            event_id=event.id,
            membership_id=membership.id,
        ).first()

        if candidate is None:
            raise ModeratorError("You are not a moderator candidate.")

        if candidate.status != ModeratorCandidateStatus.ACTIVE:
            raise ModeratorError("This candidate is no longer active.")

        if event.moderator_voting_status != ModeratorVotingStatus.NOT_STARTED:
            raise ModeratorError("Candidates cannot withdraw after voting has started.")

        candidate.status = ModeratorCandidateStatus.WITHDRAWN
        db.session.commit()

        return candidate

    @staticmethod
    def get_candidates(event):
        return (
            ModeratorCandidate.query.filter_by(
                event_id=event.id,
            )
            .order_by(ModeratorCandidate.created_at.asc())
            .all()
        )

    @staticmethod
    def open_voting(event):
        if event.moderator_voting_status != ModeratorVotingStatus.NOT_STARTED:
            raise ModeratorError(
                "Moderator voting cannot be opened from its current state."
            )

        event.moderator_voting_status = ModeratorVotingStatus.OPEN
        db.session.commit()

        return event

    @staticmethod
    def close_voting(event):
        if event.moderator_voting_status != ModeratorVotingStatus.OPEN:
            raise ModeratorError("Moderator voting is not open.")

        event.moderator_voting_status = ModeratorVotingStatus.CLOSED
        db.session.commit()

        return event

    @staticmethod
    def vote(event, user, candidate_id):
        if event.moderator_voting_status != ModeratorVotingStatus.OPEN:
            raise ModeratorError("Moderator voting is not open.")

        voter_membership = EventMembership.query.filter_by(
            event_id=event.id,
            user_id=user.id,
        ).first()

        if voter_membership is None:
            raise ModeratorError("You must be an event member to vote.")

        if voter_membership.role != "PARTICIPANT":
            raise ModeratorError("Only participants can vote.")

        candidate = ModeratorCandidate.query.filter_by(
            id=candidate_id,
            event_id=event.id,
        ).first()

        if candidate is None:
            raise ModeratorError("Candidate not found.")

        if candidate.status != ModeratorCandidateStatus.ACTIVE:
            raise ModeratorError("This candidate is not active.")

        if candidate.membership_id == voter_membership.id:
            raise ModeratorError("You cannot vote for yourself.")

        existing_vote = ModeratorVote.query.filter_by(
            event_id=event.id,
            voter_membership_id=voter_membership.id,
        ).first()

        if existing_vote:
            raise ModeratorError("You have already voted.")

        vote = ModeratorVote(
            event_id=event.id,
            voter_membership_id=voter_membership.id,
            candidate_id=candidate.id,
        )

        db.session.add(vote)
        db.session.commit()

        return vote

    @staticmethod
    def get_results(event):
        results = (
            db.session.query(
                ModeratorCandidate,
                func.count(ModeratorVote.id).label("vote_count"),
            )
            .outerjoin(
                ModeratorVote,
                ModeratorVote.candidate_id == ModeratorCandidate.id,
            )
            .filter(
                ModeratorCandidate.event_id == event.id,
                ModeratorCandidate.status == ModeratorCandidateStatus.ACTIVE,
            )
            .group_by(ModeratorCandidate.id)
            .order_by(
                func.count(ModeratorVote.id).desc(),
                ModeratorCandidate.created_at.asc(),
                ModeratorCandidate.id.asc(),
            )
            .all()
        )

        return results

    @staticmethod
    def finalize(event):
        if event.moderator_voting_status != ModeratorVotingStatus.CLOSED:
            raise ModeratorError("Moderator voting must be closed before finalization.")

        candidates = ModeratorService.get_results(event)

        if len(candidates) < 3:
            raise ModeratorError(
                "At least 3 active candidates are required to finalize the election."
            )

        selected = candidates[:3]
        selected_ids = {candidate.id for candidate, _ in selected}

        for candidate, _ in candidates:
            if candidate.id in selected_ids:
                candidate.status = ModeratorCandidateStatus.SELECTED
                candidate.membership.role = "MODERATOR"
            else:
                candidate.status = ModeratorCandidateStatus.NOT_SELECTED

        event.moderator_voting_status = ModeratorVotingStatus.FINALIZED

        db.session.commit()

        return selected
