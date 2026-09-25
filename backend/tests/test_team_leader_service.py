from datetime import datetime, timezone

import pytest

from app.extensions import db
from app.models.event import Event
from app.models.event_group import EventGroup
from app.models.event_membership import EventMembership
from app.models.user import User
from app.services.team_leader_service import TeamLeaderService


def create_user(email):
    user = User(
        email=email,
        system_role="USER",
    )
    db.session.add(user)
    db.session.flush()
    return user


def create_event(user):
    event = Event(
        name="Team Leader Test",
        slug="team-leader-test",
        description="Test event",
        venue="Test Venue",
        address="Test Address",
        city="Nairobi",
        country="Kenya",
        starts_at=datetime(
            2026,
            12,
            1,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        ends_at=datetime(
            2026,
            12,
            1,
            18,
            0,
            tzinfo=timezone.utc,
        ),
        access_code="TEAM123",
        status="ACTIVE",
        registration_status="OPEN",
        voting_status="NOT_STARTED",
        moderator_voting_status="NOT_STARTED",
        created_by=user.id,
    )
    db.session.add(event)
    db.session.flush()

    return event


def create_team(
    event,
    name="Team 1",
    election_status="OPEN",
):
    group = EventGroup(
        event_id=event.id,
        name=name,
        election_status=election_status,
    )
    db.session.add(group)
    db.session.flush()

    return group


def create_membership(event, user, group):
    membership = EventMembership(
        event_id=event.id,
        user_id=user.id,
        role="PARTICIPANT",
        team_role="MEMBER",
        group_id=group.id,
    )
    db.session.add(membership)
    db.session.flush()

    return membership


# ---------------------------------------------------------
# Voting
# ---------------------------------------------------------


def test_member_can_vote_for_team_leader(app):
    with app.app_context():
        owner = create_user("owner@test.com")
        voter = create_user("voter@test.com")
        candidate = create_user("candidate@test.com")

        event = create_event(owner)
        team = create_team(event)

        voter_membership = create_membership(
            event,
            voter,
            team,
        )

        candidate_membership = create_membership(
            event,
            candidate,
            team,
        )

        vote = TeamLeaderService.vote(
            event=event,
            voter=voter,
            group_id=team.id,
            candidate_membership_id=candidate_membership.id,
        )

        assert vote.group_id == team.id
        assert vote.voter_membership_id == voter_membership.id
        assert vote.candidate_membership_id == candidate_membership.id


def test_member_cannot_vote_for_themselves(app):
    with app.app_context():
        owner = create_user("owner2@test.com")
        voter = create_user("voter2@test.com")

        event = create_event(owner)
        team = create_team(event)

        voter_membership = create_membership(
            event,
            voter,
            team,
        )

        with pytest.raises(
            ValueError,
            match="You cannot vote for yourself",
        ):
            TeamLeaderService.vote(
                event=event,
                voter=voter,
                group_id=team.id,
                candidate_membership_id=voter_membership.id,
            )


def test_member_cannot_vote_for_candidate_from_another_team(app):
    with app.app_context():
        owner = create_user("owner3@test.com")
        voter = create_user("voter3@test.com")
        candidate = create_user("candidate3@test.com")

        event = create_event(owner)

        team_one = create_team(event, "Team 1")
        team_two = create_team(
            event,
            "Team 2",
        )

        create_membership(
            event,
            voter,
            team_one,
        )

        candidate_membership = create_membership(
            event,
            candidate,
            team_two,
        )

        with pytest.raises(
            ValueError,
            match="Candidate must be a member of this team",
        ):
            TeamLeaderService.vote(
                event=event,
                voter=voter,
                group_id=team_one.id,
                candidate_membership_id=candidate_membership.id,
            )


def test_member_can_vote_only_once(app):
    with app.app_context():
        owner = create_user("owner4@test.com")
        voter = create_user("voter4@test.com")
        candidate_one = create_user("candidate4a@test.com")
        candidate_two = create_user("candidate4b@test.com")

        event = create_event(owner)
        team = create_team(event)

        create_membership(
            event,
            voter,
            team,
        )

        candidate_one_membership = create_membership(
            event,
            candidate_one,
            team,
        )

        candidate_two_membership = create_membership(
            event,
            candidate_two,
            team,
        )

        TeamLeaderService.vote(
            event=event,
            voter=voter,
            group_id=team.id,
            candidate_membership_id=candidate_one_membership.id,
        )

        with pytest.raises(
            ValueError,
            match="You have already voted for a team leader",
        ):
            TeamLeaderService.vote(
                event=event,
                voter=voter,
                group_id=team.id,
                candidate_membership_id=candidate_two_membership.id,
            )


def test_non_team_member_cannot_vote(app):
    with app.app_context():
        owner = create_user("owner5@test.com")
        voter = create_user("voter5@test.com")
        candidate = create_user("candidate5@test.com")

        event = create_event(owner)
        team = create_team(event)

        candidate_membership = create_membership(
            event,
            candidate,
            team,
        )

        with pytest.raises(
            ValueError,
            match="You must be a member of this team to vote",
        ):
            TeamLeaderService.vote(
                event=event,
                voter=voter,
                group_id=team.id,
                candidate_membership_id=candidate_membership.id,
            )


def test_count_votes(app):
    with app.app_context():
        owner = create_user("owner6@test.com")
        voter_one = create_user("voter6a@test.com")
        voter_two = create_user("voter6b@test.com")
        candidate = create_user("candidate6@test.com")

        event = create_event(owner)
        team = create_team(event)

        create_membership(
            event,
            voter_one,
            team,
        )

        create_membership(
            event,
            voter_two,
            team,
        )

        candidate_membership = create_membership(
            event,
            candidate,
            team,
        )

        TeamLeaderService.vote(
            event=event,
            voter=voter_one,
            group_id=team.id,
            candidate_membership_id=candidate_membership.id,
        )

        TeamLeaderService.vote(
            event=event,
            voter=voter_two,
            group_id=team.id,
            candidate_membership_id=candidate_membership.id,
        )

        results = TeamLeaderService.count_votes(team.id)

        assert results == [
            {
                "membership_id": candidate_membership.id,
                "votes": 2,
            }
        ]


# ---------------------------------------------------------
# Election lifecycle
# ---------------------------------------------------------


def test_team_leader_election_can_be_opened(app):
    with app.app_context():
        owner = create_user("open-owner@test.com")
        event = create_event(owner)
        team = create_team(
            event,
            election_status="NOT_STARTED",
        )

        result = TeamLeaderService.open_election(team)

        assert result.election_status == "OPEN"


def test_cannot_open_already_open_election(app):
    with app.app_context():
        owner = create_user("already-open@test.com")
        event = create_event(owner)
        team = create_team(
            event,
            election_status="OPEN",
        )

        with pytest.raises(
            ValueError,
            match="Team leader election is already open",
        ):
            TeamLeaderService.open_election(team)


def test_cannot_reopen_closed_election(app):
    with app.app_context():
        owner = create_user("reopen-closed@test.com")
        event = create_event(owner)
        team = create_team(
            event,
            election_status="CLOSED",
        )

        with pytest.raises(
            ValueError,
            match="Team leader election cannot be reopened",
        ):
            TeamLeaderService.open_election(team)


def test_team_leader_election_can_be_closed(app):
    with app.app_context():
        owner = create_user("close-owner@test.com")
        event = create_event(owner)
        team = create_team(
            event,
            election_status="OPEN",
        )

        result = TeamLeaderService.close_election(team)

        assert result.election_status == "CLOSED"


def test_cannot_close_non_open_election(app):
    with app.app_context():
        owner = create_user("close-invalid@test.com")
        event = create_event(owner)
        team = create_team(
            event,
            election_status="NOT_STARTED",
        )

        with pytest.raises(
            ValueError,
            match="Team leader election is not open",
        ):
            TeamLeaderService.close_election(team)


def test_cannot_finalize_open_election(app):
    with app.app_context():
        owner = create_user("finalize-open@test.com")
        event = create_event(owner)
        team = create_team(
            event,
            election_status="OPEN",
        )

        with pytest.raises(
            ValueError,
            match="Team leader election must be closed before finalizing",
        ):
            TeamLeaderService.finalize_election(team)


def test_cannot_finalize_without_votes(app):
    with app.app_context():
        owner = create_user("no-votes@test.com")
        event = create_event(owner)
        team = create_team(
            event,
            election_status="CLOSED",
        )

        with pytest.raises(
            ValueError,
            match="No votes were cast",
        ):
            TeamLeaderService.finalize_election(team)


def test_winner_becomes_team_leader(app):
    with app.app_context():
        owner = create_user("winner-owner@test.com")
        voter_one = create_user("winner-voter1@test.com")
        voter_two = create_user("winner-voter2@test.com")
        candidate = create_user("winner-candidate@test.com")

        event = create_event(owner)
        team = create_team(event)

        create_membership(
            event,
            voter_one,
            team,
        )

        create_membership(
            event,
            voter_two,
            team,
        )

        candidate_membership = create_membership(
            event,
            candidate,
            team,
        )

        TeamLeaderService.vote(
            event=event,
            voter=voter_one,
            group_id=team.id,
            candidate_membership_id=candidate_membership.id,
        )

        TeamLeaderService.vote(
            event=event,
            voter=voter_two,
            group_id=team.id,
            candidate_membership_id=candidate_membership.id,
        )

        TeamLeaderService.close_election(team)

        winner = TeamLeaderService.finalize_election(team)

        assert winner.id == candidate_membership.id
        assert winner.team_role == "LEADER"
        assert team.election_status == "FINALIZED"


def test_tie_prevents_finalization(app):
    with app.app_context():
        owner = create_user("tie-owner@test.com")
        voter_one = create_user("tie-voter1@test.com")
        voter_two = create_user("tie-voter2@test.com")
        candidate_one = create_user("tie-candidate1@test.com")
        candidate_two = create_user("tie-candidate2@test.com")

        event = create_event(owner)
        team = create_team(event)

        create_membership(
            event,
            voter_one,
            team,
        )

        create_membership(
            event,
            voter_two,
            team,
        )

        candidate_one_membership = create_membership(
            event,
            candidate_one,
            team,
        )

        candidate_two_membership = create_membership(
            event,
            candidate_two,
            team,
        )

        TeamLeaderService.vote(
            event=event,
            voter=voter_one,
            group_id=team.id,
            candidate_membership_id=candidate_one_membership.id,
        )

        TeamLeaderService.vote(
            event=event,
            voter=voter_two,
            group_id=team.id,
            candidate_membership_id=candidate_two_membership.id,
        )

        TeamLeaderService.close_election(team)

        with pytest.raises(
            ValueError,
            match="Team leader election ended in a tie",
        ):
            TeamLeaderService.finalize_election(team)

        assert team.election_status == "CLOSED"


def test_finalized_election_cannot_accept_votes(app):
    with app.app_context():
        owner = create_user("finalized-owner@test.com")
        voter = create_user("finalized-voter@test.com")
        candidate = create_user("finalized-candidate@test.com")

        event = create_event(owner)
        team = create_team(
            event,
            election_status="FINALIZED",
        )

        create_membership(
            event,
            voter,
            team,
        )

        candidate_membership = create_membership(
            event,
            candidate,
            team,
        )

        with pytest.raises(
            ValueError,
            match="Team leader election is not open",
        ):
            TeamLeaderService.vote(
                event=event,
                voter=voter,
                group_id=team.id,
                candidate_membership_id=candidate_membership.id,
            )
