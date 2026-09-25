from datetime import datetime, timezone

import pytest

from app.models import Event, EventMembership, Outstation, User
from app.services.profile_service import ProfileService


@pytest.fixture
def user(database):
    user = User(
        email="brian@example.com",
        google_id="google-brian",
    )
    database.session.add(user)
    database.session.commit()

    return user


@pytest.fixture
def outstation(database):
    outstation = Outstation(
        name="St. Camillus",
        slug="st-camillus",
    )
    database.session.add(outstation)
    database.session.commit()

    return outstation


@pytest.fixture
def event(database, user):
    event = Event(
        name="St. Camillus YSC Hangout",
        slug="st-camillus-ysc-hangout",
        description="Test event",
        venue="Test Venue",
        address="Test Address",
        city="Nairobi",
        country="Kenya",
        starts_at=datetime(2026, 12, 20, 9, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 12, 20, 17, 0, tzinfo=timezone.utc),
        access_code="CAMILLUS2026",
        status="PUBLISHED",
        registration_status="OPEN",
        voting_status="NOT_STARTED",
        moderator_voting_status="NOT_STARTED",
        created_by=user.id,
    )
    database.session.add(event)
    database.session.commit()

    return event


@pytest.fixture
def authenticated_client(app, user):
    client = app.test_client()

    with client.session_transaction() as session:
        session["user_id"] = user.id

    return client


def test_join_requires_authentication(app, event):
    client = app.test_client()

    response = client.post(
        "/api/events/join",
        json={"access_code": "CAMILLUS2026"},
    )

    assert response.status_code == 401
    assert response.get_json() == {
        "error": "Authentication required",
    }


def test_join_rejects_invalid_access_code(
    app,
    user,
    authenticated_client,
):
    response = authenticated_client.post(
        "/api/events/join",
        json={"access_code": "WRONGCODE"},
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "error": "Invalid event access code",
    }


def test_join_rejects_incomplete_profile(
    app,
    user,
    event,
    authenticated_client,
):
    response = authenticated_client.post(
        "/api/events/join",
        json={"access_code": event.access_code},
    )

    assert response.status_code == 409
    assert response.get_json() == {
        "error": "Please complete your profile before joining the event.",
    }


def test_join_succeeds_with_complete_profile(
    app,
    user,
    outstation,
    event,
    authenticated_client,
):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
        jumuia="St. Camillus Jumuia",
        field_of_study="Software Engineering",
    )

    response = authenticated_client.post(
        "/api/events/join",
        json={"access_code": event.access_code},
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["message"] == "Joined event successfully"
    assert data["membership"]["event_id"] == event.id
    assert data["membership"]["user_id"] == user.id
    assert data["membership"]["role"] == "PARTICIPANT"


def test_join_is_idempotent(
    app,
    user,
    outstation,
    event,
    authenticated_client,
):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
        jumuia="St. Camillus Jumuia",
        field_of_study="Software Engineering",
    )

    first_response = authenticated_client.post(
        "/api/events/join",
        json={"access_code": event.access_code},
    )

    second_response = authenticated_client.post(
        "/api/events/join",
        json={"access_code": event.access_code},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 200

    data = second_response.get_json()

    assert data["message"] == "You are already a member of this event"

    memberships = EventMembership.query.filter_by(
        event_id=event.id,
        user_id=user.id,
    ).all()

    assert len(memberships) == 1


def test_join_rejects_closed_registration(
    app,
    user,
    outstation,
    event,
    authenticated_client,
):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
        jumuia="St. Camillus Jumuia",
        field_of_study="Software Engineering",
    )

    event.registration_status = "CLOSED"
    from app.extensions import db

    db.session.commit()

    response = authenticated_client.post(
        "/api/events/join",
        json={"access_code": event.access_code},
    )

    assert response.status_code == 409
    assert response.get_json() == {
        "error": "Registration is closed for this event",
    }
