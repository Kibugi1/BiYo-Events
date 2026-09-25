from datetime import datetime, timezone

from app.models import (
    Event,
    EventGroup,
    EventMembership,
    TeamLeaderVote,
    User,
)
from app.extensions import db


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
        name="Team Leader Test Event",
        slug="team-leader-test-event",
        description="Test event",
        venue="Test Venue",
        address="Test Address",
        city="Nairobi",
        country="Kenya",
        starts_at=datetime.now(timezone.utc),
        ends_at=datetime.now(timezone.utc),
        access_code="TEAM123",
        status="PUBLISHED",
        registration_status="OPEN",
        moderator_voting_status="FINALIZED",
        voting_status="NOT_STARTED",
        created_by=user.id,
    )
    db.session.add(event)
    db.session.commit()
    return event


def create_team(event, name="Team 1"):
    group = EventGroup(
        event_id=event.id,
        name=name,
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


def test_team_member_can_view_election_status(app):
    client = app.test_client()

    user = create_user("member@example.com")
    event = create_event(user)
    group = create_team(event)
    membership = create_membership(event, user, group)

    login(client, user)

    response = client.get(
        f"/api/events/{event.id}/teams/{group.id}/leader-election"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["team"]["id"] == group.id
    assert data["team"]["name"] == "Team 1"
    assert data["team"]["display_name"] == "Kumalo"

    assert data["election"]["status"] == "OPEN"
    assert data["election"]["has_voted"] is False
    assert data["election"]["leader"] is None


def test_non_member_cannot_view_team_election(app):
    client = app.test_client()

    owner = create_user("owner@example.com")
    outsider = create_user("outsider@example.com")

    event = create_event(owner)
    group = create_team(event)

    create_membership(event, owner, group)

    login(client, outsider)

    response = client.get(
        f"/api/events/{event.id}/teams/{group.id}/leader-election"
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == (
        "You must be a member of this team"
    )


def test_unauthenticated_user_cannot_view_team_election(app):
    client = app.test_client()

    user = create_user("member@example.com")
    event = create_event(user)
    group = create_team(event)
    create_membership(event, user, group)

    response = client.get(
        f"/api/events/{event.id}/teams/{group.id}/leader-election"
    )

    assert response.status_code == 401
    assert response.get_json()["error"] == "Authentication required"


def test_team_election_not_found(app):
    client = app.test_client()

    user = create_user("member@example.com")
    event = create_event(user)

    login(client, user)

    response = client.get(
        f"/api/events/{event.id}/teams/9999/leader-election"
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "Team not found"


def test_team_member_sees_that_they_have_voted(app):
    client = app.test_client()

    voter = create_user("voter@example.com")
    candidate = create_user("candidate@example.com")

    event = create_event(voter)
    group = create_team(event)

    voter_membership = create_membership(event, voter, group)
    candidate_membership = create_membership(event, candidate, group)

    vote = TeamLeaderVote(
        event_id=event.id,
        group_id=group.id,
        voter_membership_id=voter_membership.id,
        candidate_membership_id=candidate_membership.id,
    )

    db.session.add(vote)
    db.session.commit()

    login(client, voter)

    response = client.get(
        f"/api/events/{event.id}/teams/{group.id}/leader-election"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["election"]["status"] == "OPEN"
    assert data["election"]["has_voted"] is True
    assert data["election"]["leader"] is None


def test_team_member_sees_finalized_leader(app):
    client = app.test_client()

    member = create_user("member@example.com")
    leader = create_user("leader@example.com")

    event = create_event(member)
    group = create_team(event)

    create_membership(event, member, group)

    leader_membership = create_membership(
        event,
        leader,
        group,
    )

    group.election_status = "FINALIZED"
    leader_membership.team_role = "LEADER"

    db.session.commit()

    login(client, member)

    response = client.get(
        f"/api/events/{event.id}/teams/{group.id}/leader-election"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["election"]["status"] == "FINALIZED"
    assert data["election"]["leader"] == {
        "membership_id": leader_membership.id,
        "user_id": leader.id,
    }
