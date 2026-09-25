import pytest

from datetime import datetime, timezone


from app.events.moderator_constants import ModeratorCandidateStatus
from app.events.moderator_constants import ModeratorVotingStatus
from app.events.moderator_service import ModeratorError
from app.events.moderator_service import ModeratorService
from app.extensions import db
from app.models import Event
from app.models import EventMembership
from app.models import ModeratorCandidate
from app.models import ModeratorVote
from app.models import User


@pytest.fixture
def moderator_event(app):
    organizer = User(
        email="organizer@test.biyo",
        google_id="test-organizer",
        system_role="SUPER_ADMIN",
    )

    alice = User(
        email="alice@test.biyo",
        google_id="test-alice",
        system_role="USER",
    )

    carol = User(
        email="carol@test.biyo",
        google_id="test-carol",
        system_role="USER",
    )

    david = User(
        email="david@test.biyo",
        google_id="test-david",
        system_role="USER",
    )

    eve = User(
        email="eve@test.biyo",
        google_id="test-eve",
        system_role="USER",
    )

    db.session.add_all([organizer, alice, carol, david, eve])
    db.session.flush()

    event = Event(
        name="Moderator Test Event",
        slug="moderator-test-event",
        description="Test event for moderator election.",
        venue="Test Venue",
        address="Test Address",
        city="Nairobi",
        country="Kenya",
        starts_at=datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 10, 1, 18, 0, tzinfo=timezone.utc),
        access_code="TEST123",
        status="PUBLISHED",
        registration_status="OPEN",
        voting_status="NOT_STARTED",
        moderator_voting_status=ModeratorVotingStatus.NOT_STARTED,
        created_by=organizer.id,
    )

    db.session.add(event)
    db.session.flush()

    memberships = [
        EventMembership(
            event_id=event.id,
            user_id=organizer.id,
            role="ORGANIZER",
        ),
        EventMembership(
            event_id=event.id,
            user_id=alice.id,
            role="PARTICIPANT",
        ),
        EventMembership(
            event_id=event.id,
            user_id=carol.id,
            role="PARTICIPANT",
        ),
        EventMembership(
            event_id=event.id,
            user_id=david.id,
            role="PARTICIPANT",
        ),
        EventMembership(
            event_id=event.id,
            user_id=eve.id,
            role="PARTICIPANT",
        ),
    ]

    db.session.add_all(memberships)
    db.session.commit()

    return {
        "event": event,
        "organizer": organizer,
        "alice": alice,
        "carol": carol,
        "david": david,
        "eve": eve,
    }


def test_participant_can_volunteer(moderator_event):
    event = moderator_event["event"]
    alice = moderator_event["alice"]

    candidate, created = ModeratorService.volunteer(event, alice)

    assert created is True
    assert candidate.status == ModeratorCandidateStatus.ACTIVE
    assert candidate.membership.user_id == alice.id


def test_participant_cannot_volunteer_twice(moderator_event):
    event = moderator_event["event"]
    alice = moderator_event["alice"]

    first_candidate, created = ModeratorService.volunteer(event, alice)
    second_candidate, created_again = ModeratorService.volunteer(event, alice)

    assert created is True
    assert created_again is False
    assert second_candidate.id == first_candidate.id

    assert ModeratorCandidate.query.filter_by(
        event_id=event.id,
        membership_id=first_candidate.membership_id,
    ).count() == 1


def test_moderator_voting_can_open(moderator_event):
    event = moderator_event["event"]

    ModeratorService.open_voting(event)

    assert event.moderator_voting_status == ModeratorVotingStatus.OPEN


def test_participant_can_vote(moderator_event):
    event = moderator_event["event"]
    alice = moderator_event["alice"]
    carol = moderator_event["carol"]

    alice_candidate, _ = ModeratorService.volunteer(event, alice)
    carol_candidate, _ = ModeratorService.volunteer(event, carol)

    ModeratorService.open_voting(event)

    vote = ModeratorService.vote(
        event,
        alice,
        carol_candidate.id,
    )

    assert vote.voter_membership.user_id == alice.id
    assert vote.candidate_id == carol_candidate.id


def test_participant_cannot_vote_twice(moderator_event):
    event = moderator_event["event"]
    alice = moderator_event["alice"]
    carol = moderator_event["carol"]
    david = moderator_event["david"]

    carol_candidate, _ = ModeratorService.volunteer(event, carol)
    david_candidate, _ = ModeratorService.volunteer(event, david)

    ModeratorService.open_voting(event)

    ModeratorService.vote(event, alice, carol_candidate.id)

    with pytest.raises(
        ModeratorError,
        match="You have already voted.",
    ):
        ModeratorService.vote(event, alice, david_candidate.id)


def test_participant_cannot_vote_for_self(moderator_event):
    event = moderator_event["event"]
    alice = moderator_event["alice"]

    candidate, _ = ModeratorService.volunteer(event, alice)

    ModeratorService.open_voting(event)

    with pytest.raises(
        ModeratorError,
        match="You cannot vote for yourself.",
    ):
        ModeratorService.vote(event, alice, candidate.id)


def test_organizer_cannot_vote(moderator_event):
    event = moderator_event["event"]
    organizer = moderator_event["organizer"]
    alice = moderator_event["alice"]

    candidate, _ = ModeratorService.volunteer(event, alice)

    ModeratorService.open_voting(event)

    with pytest.raises(
        ModeratorError,
        match="Only participants can vote.",
    ):
        ModeratorService.vote(event, organizer, candidate.id)


def test_moderator_voting_can_close(moderator_event):
    event = moderator_event["event"]

    ModeratorService.open_voting(event)
    ModeratorService.close_voting(event)

    assert event.moderator_voting_status == ModeratorVotingStatus.CLOSED


def test_results_count_votes(moderator_event):
    event = moderator_event["event"]
    alice = moderator_event["alice"]
    carol = moderator_event["carol"]
    david = moderator_event["david"]
    eve = moderator_event["eve"]

    alice_candidate, _ = ModeratorService.volunteer(event, alice)
    carol_candidate, _ = ModeratorService.volunteer(event, carol)
    david_candidate, _ = ModeratorService.volunteer(event, david)

    ModeratorService.open_voting(event)

    ModeratorService.vote(event, alice, carol_candidate.id)
    ModeratorService.vote(event, carol, david_candidate.id)
    ModeratorService.vote(event, david, alice_candidate.id)
    ModeratorService.vote(event, eve, alice_candidate.id)

    results = ModeratorService.get_results(event)

    result_map = {
        candidate.membership.user.email: vote_count
        for candidate, vote_count in results
    }

    assert result_map["alice@test.biyo"] == 2
    assert result_map["carol@test.biyo"] == 1
    assert result_map["david@test.biyo"] == 1


def test_finalize_selects_exactly_three_moderators(moderator_event):
    event = moderator_event["event"]
    alice = moderator_event["alice"]
    carol = moderator_event["carol"]
    david = moderator_event["david"]
    eve = moderator_event["eve"]

    alice_candidate, _ = ModeratorService.volunteer(event, alice)
    carol_candidate, _ = ModeratorService.volunteer(event, carol)
    david_candidate, _ = ModeratorService.volunteer(event, david)

    ModeratorService.open_voting(event)

    ModeratorService.vote(event, alice, carol_candidate.id)
    ModeratorService.vote(event, carol, david_candidate.id)
    ModeratorService.vote(event, david, alice_candidate.id)
    ModeratorService.vote(event, eve, alice_candidate.id)

    ModeratorService.close_voting(event)

    selected = ModeratorService.finalize(event)

    assert len(selected) == 3
    assert event.moderator_voting_status == ModeratorVotingStatus.FINALIZED

    selected_memberships = EventMembership.query.filter_by(
        event_id=event.id,
        role="MODERATOR",
    ).all()

    assert len(selected_memberships) == 3


def test_selected_candidates_become_moderators(moderator_event):
    event = moderator_event["event"]
    alice = moderator_event["alice"]
    carol = moderator_event["carol"]
    david = moderator_event["david"]
    eve = moderator_event["eve"]

    alice_candidate, _ = ModeratorService.volunteer(event, alice)
    carol_candidate, _ = ModeratorService.volunteer(event, carol)
    david_candidate, _ = ModeratorService.volunteer(event, david)

    ModeratorService.open_voting(event)

    ModeratorService.vote(event, alice, carol_candidate.id)
    ModeratorService.vote(event, carol, david_candidate.id)
    ModeratorService.vote(event, david, alice_candidate.id)
    ModeratorService.vote(event, eve, alice_candidate.id)

    ModeratorService.close_voting(event)
    ModeratorService.finalize(event)

    for user in [alice, carol, david]:
        membership = EventMembership.query.filter_by(
            event_id=event.id,
            user_id=user.id,
        ).first()

        assert membership.role == "MODERATOR"


def test_organizer_remains_organizer(moderator_event):
    event = moderator_event["event"]
    organizer = moderator_event["organizer"]
    alice = moderator_event["alice"]
    carol = moderator_event["carol"]
    david = moderator_event["david"]
    eve = moderator_event["eve"]

    alice_candidate, _ = ModeratorService.volunteer(event, alice)
    carol_candidate, _ = ModeratorService.volunteer(event, carol)
    david_candidate, _ = ModeratorService.volunteer(event, david)

    ModeratorService.open_voting(event)

    ModeratorService.vote(event, alice, carol_candidate.id)
    ModeratorService.vote(event, carol, david_candidate.id)
    ModeratorService.vote(event, david, alice_candidate.id)
    ModeratorService.vote(event, eve, alice_candidate.id)

    ModeratorService.close_voting(event)
    ModeratorService.finalize(event)

    membership = EventMembership.query.filter_by(
        event_id=event.id,
        user_id=organizer.id,
    ).first()

    assert membership.role == "ORGANIZER"


def test_cannot_vote_when_voting_is_closed(moderator_event):
    event = moderator_event["event"]
    alice = moderator_event["alice"]
    carol = moderator_event["carol"]

    candidate, _ = ModeratorService.volunteer(event, carol)

    ModeratorService.open_voting(event)
    ModeratorService.close_voting(event)

    with pytest.raises(
        ModeratorError,
        match="Moderator voting is not open.",
    ):
        ModeratorService.vote(event, alice, candidate.id)
