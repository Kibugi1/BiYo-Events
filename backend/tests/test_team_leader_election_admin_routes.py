from datetime import datetime, timezone

from app.extensions import db
from app.models import (
    Event,
    EventGroup,
    EventMembership,
    TeamLeaderVote,
    User,
)


def create_user(email):
    user = User(
        email=email,
        system_role="USER",
    )
    db.session.add(user)
    db.session.commit()
    return user


def create_event(user):
    event = Event(
        name="Election Admin Test Event",
        slug="election-admin-test-event",
        description="Test event",
        venue="Test Venue",
        address="Test Address",
        city="Nairobi",
        country="Kenya",
        starts_at=datetime.now(timezone.utc),
        ends_at=datetime.now(timezone.utc),
        access_code="ADMIN123",
        status="PUBLISHED",
        registration_status="OPEN",
        moderator_voting_status="FINALIZED",
        voting_status="NOT_STARTED",
        created_by=user.id,
    )

    db.session.add(event)
    db.session.commit()

    return event


def create_team(event, election_status="NOT_STARTED"):
    group = EventGroup(
        event_id=event.id,
        name="Team 1",
        display_name="Kumalo",
        election_status=election_status,
    )

    db.session.add(group)
    db.session.commit()

    return group


def create_membership(
    event,
    user,
    group,
    role="PARTICIPANT",
):
    membership = EventMembership(
        event_id=event.id,
        user_id=user.id,
        role=role,
        team_role="MEMBER",
        group_id=group.id,
    )

    db.session.add(membership)
    db.session.commit()

    return membership


def login(client, user):
    with client.session_transaction() as session:
        session["user_id"] = user.id


def test_organizer_can_open_team_leader_election(app):
    client = app.test_client()

    organizer = create_user("organizer@example.com")

    event = create_event(organizer)
    group = create_team(event)

    create_membership(
        event,
        organizer,
        group,
        role="ORGANIZER",
    )

    login(client, organizer)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/open"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Team leader election opened"
    assert data["election"]["status"] == "OPEN"


def test_non_organizer_cannot_open_election(app):
    client = app.test_client()

    organizer = create_user("organizer@example.com")
    participant = create_user("participant@example.com")

    event = create_event(organizer)
    group = create_team(event)

    create_membership(
        event,
        organizer,
        group,
        role="ORGANIZER",
    )

    create_membership(
        event,
        participant,
        group,
        role="PARTICIPANT",
    )

    login(client, participant)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/open"
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Organizer access required"


def test_unauthenticated_user_cannot_open_election(app):
    client = app.test_client()

    organizer = create_user("organizer@example.com")

    event = create_event(organizer)
    group = create_team(event)

    create_membership(
        event,
        organizer,
        group,
        role="ORGANIZER",
    )

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/open"
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication required"


def test_organizer_can_close_election(app):
    client = app.test_client()

    organizer = create_user("organizer@example.com")

    event = create_event(organizer)
    group = create_team(
        event,
        election_status="OPEN",
    )

    create_membership(
        event,
        organizer,
        group,
        role="ORGANIZER",
    )

    login(client, organizer)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/close"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Team leader election closed"
    assert data["election"]["status"] == "CLOSED"


def test_non_organizer_cannot_close_election(app):
    client = app.test_client()

    organizer = create_user("organizer@example.com")
    participant = create_user("participant@example.com")

    event = create_event(organizer)
    group = create_team(
        event,
        election_status="OPEN",
    )

    create_membership(
        event,
        organizer,
        group,
        role="ORGANIZER",
    )

    create_membership(
        event,
        participant,
        group,
        role="PARTICIPANT",
    )

    login(client, participant)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/close"
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Organizer access required"


def test_organizer_can_finalize_election(app):
    client = app.test_client()

    organizer = create_user("organizer@example.com")
    candidate = create_user("candidate@example.com")

    event = create_event(organizer)
    group = create_team(
        event,
        election_status="CLOSED",
    )

    create_membership(
        event,
        organizer,
        group,
        role="ORGANIZER",
    )

    candidate_membership = create_membership(
        event,
        candidate,
        group,
    )

    voter = create_user("voter@example.com")

    voter_membership = create_membership(
        event,
        voter,
        group,
    )

    vote = TeamLeaderVote(
        event_id=event.id,
        group_id=group.id,
        voter_membership_id=voter_membership.id,
        candidate_membership_id=candidate_membership.id,
    )

    db.session.add(vote)
    db.session.commit()

    login(client, organizer)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/finalize"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == "Team leader election finalized"
    assert data["election"]["status"] == "FINALIZED"
    assert data["election"]["leader"]["membership_id"] == (
        candidate_membership.id
    )
    assert data["election"]["leader"]["user_id"] == candidate.id

    db.session.refresh(candidate_membership)

    assert candidate_membership.team_role == "LEADER"


def test_non_organizer_cannot_finalize_election(app):
    client = app.test_client()

    organizer = create_user("organizer@example.com")
    participant = create_user("participant@example.com")

    event = create_event(organizer)
    group = create_team(
        event,
        election_status="CLOSED",
    )

    create_membership(
        event,
        organizer,
        group,
        role="ORGANIZER",
    )

    create_membership(
        event,
        participant,
        group,
    )

    login(client, participant)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/finalize"
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == "Organizer access required"


def test_finalize_requires_votes(app):
    client = app.test_client()

    organizer = create_user("organizer@example.com")

    event = create_event(organizer)
    group = create_team(
        event,
        election_status="CLOSED",
    )

    create_membership(
        event,
        organizer,
        group,
        role="ORGANIZER",
    )

    login(client, organizer)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/finalize"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "No votes were cast"


def test_finalize_tie_returns_bad_request(app):
    client = app.test_client()

    organizer = create_user("organizer@example.com")
    candidate_one = create_user("candidate1@example.com")
    candidate_two = create_user("candidate2@example.com")
    voter_one = create_user("voter1@example.com")
    voter_two = create_user("voter2@example.com")

    event = create_event(organizer)

    group = create_team(
        event,
        election_status="CLOSED",
    )

    create_membership(
        event,
        organizer,
        group,
        role="ORGANIZER",
    )

    candidate_one_membership = create_membership(
        event,
        candidate_one,
        group,
    )

    candidate_two_membership = create_membership(
        event,
        candidate_two,
        group,
    )

    voter_one_membership = create_membership(
        event,
        voter_one,
        group,
    )

    voter_two_membership = create_membership(
        event,
        voter_two,
        group,
    )

    vote_one = TeamLeaderVote(
        event_id=event.id,
        group_id=group.id,
        voter_membership_id=voter_one_membership.id,
        candidate_membership_id=candidate_one_membership.id,
    )

    vote_two = TeamLeaderVote(
        event_id=event.id,
        group_id=group.id,
        voter_membership_id=voter_two_membership.id,
        candidate_membership_id=candidate_two_membership.id,
    )

    db.session.add_all(
        [
            vote_one,
            vote_two,
        ]
    )

    db.session.commit()

    login(client, organizer)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/finalize"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "Team leader election ended in a tie"
    )
