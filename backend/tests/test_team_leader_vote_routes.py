from datetime import datetime, timezone

from app.extensions import db
from app.models import (
    Event,
    EventGroup,
    EventMembership,
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
        name="Team Leader Vote Test Event",
        slug="team-leader-vote-test-event",
        description="Test event",
        venue="Test Venue",
        address="Test Address",
        city="Nairobi",
        country="Kenya",
        starts_at=datetime.now(timezone.utc),
        ends_at=datetime.now(timezone.utc),
        access_code="VOTE123",
        status="PUBLISHED",
        registration_status="OPEN",
        moderator_voting_status="FINALIZED",
        voting_status="NOT_STARTED",
        created_by=user.id,
    )
    db.session.add(event)
    db.session.commit()
    return event


def create_team(event):
    group = EventGroup(
        event_id=event.id,
        name="Team 1",
        display_name="Kumalo",
        election_status="OPEN",
    )
    db.session.add(group)
    db.session.commit()
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
    db.session.commit()
    return membership


def login(client, user):
    with client.session_transaction() as session:
        session["user_id"] = user.id


def test_team_member_can_vote_for_team_leader(app):
    client = app.test_client()

    voter = create_user("voter@example.com")
    candidate = create_user("candidate@example.com")

    event = create_event(voter)
    group = create_team(event)

    voter_membership = create_membership(
        event,
        voter,
        group,
    )

    candidate_membership = create_membership(
        event,
        candidate,
        group,
    )

    login(client, voter)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/vote",
        json={
            "candidate_membership_id": candidate_membership.id,
        },
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "Team leader vote recorded"

    assert data["vote"]["group_id"] == group.id
    assert data["vote"]["voter_membership_id"] == voter_membership.id
    assert data["vote"]["candidate_membership_id"] == (
        candidate_membership.id
    )


def test_unauthenticated_user_cannot_vote(app):
    client = app.test_client()

    user = create_user("member@example.com")
    candidate = create_user("candidate@example.com")

    event = create_event(user)
    group = create_team(event)

    create_membership(event, user, group)
    candidate_membership = create_membership(
        event,
        candidate,
        group,
    )

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/vote",
        json={
            "candidate_membership_id": candidate_membership.id,
        },
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication required"


def test_team_member_cannot_vote_for_themselves(app):
    client = app.test_client()

    user = create_user("member@example.com")

    event = create_event(user)
    group = create_team(event)

    membership = create_membership(
        event,
        user,
        group,
    )

    login(client, user)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/vote",
        json={
            "candidate_membership_id": membership.id,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "You cannot vote for yourself"


def test_team_member_cannot_vote_twice(app):
    client = app.test_client()

    voter = create_user("voter@example.com")
    candidate_one = create_user("candidate1@example.com")
    candidate_two = create_user("candidate2@example.com")

    event = create_event(voter)
    group = create_team(event)

    create_membership(event, voter, group)

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

    login(client, voter)

    first_response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/vote",
        json={
            "candidate_membership_id": candidate_one_membership.id,
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/vote",
        json={
            "candidate_membership_id": candidate_two_membership.id,
        },
    )

    assert second_response.status_code == 400
    assert second_response.get_json()["error"] == (
        "You have already voted for a team leader"
    )


def test_non_team_member_cannot_vote(app):
    client = app.test_client()

    team_member = create_user("member@example.com")
    outsider = create_user("outsider@example.com")
    candidate = create_user("candidate@example.com")

    event = create_event(team_member)
    group = create_team(event)

    create_membership(event, team_member, group)

    candidate_membership = create_membership(
        event,
        candidate,
        group,
    )

    login(client, outsider)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/vote",
        json={
            "candidate_membership_id": candidate_membership.id,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "You must be a member of this team to vote"
    )


def test_member_cannot_vote_for_candidate_from_another_team(app):
    client = app.test_client()

    voter = create_user("voter@example.com")
    candidate = create_user("candidate@example.com")

    event = create_event(voter)

    team_one = create_team(event)

    team_two = EventGroup(
        event_id=event.id,
        name="Team 2",
        display_name="Mwecheche",
        election_status="OPEN",
    )

    db.session.add(team_two)
    db.session.commit()

    create_membership(event, voter, team_one)

    candidate_membership = create_membership(
        event,
        candidate,
        team_two,
    )

    login(client, voter)

    response = client.post(
        f"/api/events/{event.id}/teams/{team_one.id}/leader-election/vote",
        json={
            "candidate_membership_id": candidate_membership.id,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "Candidate must be a member of this team"
    )


def test_vote_requires_candidate_membership_id(app):
    client = app.test_client()

    user = create_user("member@example.com")

    event = create_event(user)
    group = create_team(event)

    create_membership(event, user, group)

    login(client, user)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/vote",
        json={},
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "candidate_membership_id is required"
    )


def test_vote_requires_request_body(app):
    client = app.test_client()

    user = create_user("member@example.com")

    event = create_event(user)
    group = create_team(event)

    create_membership(event, user, group)

    login(client, user)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/vote"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Request body is required"


def test_vote_rejected_when_election_is_closed(app):
    client = app.test_client()

    voter = create_user("voter@example.com")
    candidate = create_user("candidate@example.com")

    event = create_event(voter)
    group = create_team(event)

    group.election_status = "CLOSED"
    db.session.commit()

    create_membership(event, voter, group)

    candidate_membership = create_membership(
        event,
        candidate,
        group,
    )

    login(client, voter)

    response = client.post(
        f"/api/events/{event.id}/teams/{group.id}/leader-election/vote",
        json={
            "candidate_membership_id": candidate_membership.id,
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == (
        "Team leader election is not open"
    )
