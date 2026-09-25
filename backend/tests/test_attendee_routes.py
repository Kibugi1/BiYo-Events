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
def second_user(database):
    user = User(
        email="alice@example.com",
        google_id="google-alice",
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
        name="St Camillus Hangout",
        slug="st-camillus-hangout",
        venue="St. Camillus Hall",
        starts_at=datetime(2026, 12, 20, 9, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 12, 20, 17, 0, tzinfo=timezone.utc),
        access_code="CAMILLUS2026",
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


def create_complete_profile(database, user, outstation, username):
    return ProfileService.create_profile(
        user=user,
        full_name=user.email.split("@")[0].title(),
        username=username,
        outstation_id=outstation.id,
        jumuia="St. Camillus Jumuia",
        field_of_study="Software Engineering",
        profession="Software Developer",
    )


def create_membership(database, event, user):
    membership = EventMembership(
        event_id=event.id,
        user_id=user.id,
        role="PARTICIPANT",
    )
    database.session.add(membership)
    database.session.commit()
    return membership


def test_attendees_require_authentication(app, event):
    client = app.test_client()

    response = client.get(
        f"/api/events/{event.id}/attendees",
    )

    assert response.status_code == 401
    assert response.get_json() == {
        "error": "Authentication required",
    }


def test_attendees_require_event_membership(
    app,
    user,
    event,
    authenticated_client,
):
    response = authenticated_client.get(
        f"/api/events/{event.id}/attendees",
    )

    assert response.status_code == 403
    assert response.get_json() == {
        "error": "You are not a member of this event",
    }


def test_event_member_can_view_attendees(
    app,
    database,
    user,
    second_user,
    outstation,
    event,
    authenticated_client,
):
    create_complete_profile(
        database,
        user,
        outstation,
        "brian",
    )

    create_complete_profile(
        database,
        second_user,
        outstation,
        "alice",
    )

    create_membership(database, event, user)
    create_membership(database, event, second_user)

    response = authenticated_client.get(
        f"/api/events/{event.id}/attendees",
    )

    assert response.status_code == 200

    data = response.get_json()

    assert len(data["attendees"]) == 2
    assert data["attendees"][0]["username"] == "brian"
    assert data["attendees"][1]["username"] == "alice"


def test_event_member_can_view_attendee_detail(
    app,
    database,
    user,
    second_user,
    outstation,
    event,
    authenticated_client,
):
    create_complete_profile(
        database,
        user,
        outstation,
        "brian",
    )

    create_complete_profile(
        database,
        second_user,
        outstation,
        "alice",
    )

    create_membership(database, event, user)
    create_membership(database, event, second_user)

    response = authenticated_client.get(
        f"/api/events/{event.id}/attendees/{second_user.id}",
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["attendee"]["user_id"] == second_user.id
    assert data["attendee"]["username"] == "alice"


def test_non_member_cannot_view_attendee_detail(
    app,
    database,
    user,
    second_user,
    outstation,
    event,
    authenticated_client,
):
    create_complete_profile(
        database,
        user,
        outstation,
        "brian",
    )

    create_complete_profile(
        database,
        second_user,
        outstation,
        "alice",
    )

    create_membership(database, event, second_user)

    response = authenticated_client.get(
        f"/api/events/{event.id}/attendees/{second_user.id}",
    )

    assert response.status_code == 403
    assert response.get_json() == {
        "error": "You are not a member of this event",
    }


def test_attendee_detail_returns_404_for_non_attendee(
    app,
    database,
    user,
    outstation,
    event,
    authenticated_client,
):
    create_complete_profile(
        database,
        user,
        outstation,
        "brian",
    )

    create_membership(database, event, user)

    response = authenticated_client.get(
        f"/api/events/{event.id}/attendees/999",
    )

    assert response.status_code == 404
    assert response.get_json() == {
        "error": "Attendee not found",
    }


def test_attendee_directory_exposes_connection_profile(
    app,
    database,
    user,
    second_user,
    outstation,
    event,
    authenticated_client,
):
    create_complete_profile(
        database,
        user,
        outstation,
        "brian",
    )

    create_complete_profile(
        database,
        second_user,
        outstation,
        "alice",
    )

    create_membership(database, event, user)
    create_membership(database, event, second_user)

    response = authenticated_client.get(
        f"/api/events/{event.id}/attendees/{second_user.id}",
    )

    assert response.status_code == 200

    attendee = response.get_json()["attendee"]

    assert attendee["full_name"] == "Alice"
    assert attendee["username"] == "alice"
    assert attendee["jumuia"] == "St. Camillus Jumuia"
    assert attendee["field_of_study"] == "Software Engineering"
    assert attendee["profession"] == "Software Developer"

    assert attendee["outstation"]["id"] == outstation.id
    assert attendee["outstation"]["name"] == "St. Camillus"
    assert attendee["outstation"]["slug"] == "st-camillus"


def test_attendee_directory_exposes_only_public_socials(
    app,
    database,
    user,
    second_user,
    outstation,
    event,
    authenticated_client,
):
    create_complete_profile(
        database,
        user,
        outstation,
        "brian",
    )

    create_complete_profile(
        database,
        second_user,
        outstation,
        "alice",
    )

    create_membership(database, event, user)
    create_membership(database, event, second_user)

    from app.services.profile_service import ProfileService

    public_social = ProfileService.add_social(
        user=second_user,
        platform="instagram",
        username="alice.public",
        profile_url="https://instagram.com/alice.public",
        is_public=True,
    )

    private_social = ProfileService.add_social(
        user=second_user,
        platform="linkedin",
        username="alice.private",
        profile_url="https://linkedin.com/in/alice.private",
        is_public=False,
    )

    response = authenticated_client.get(
        f"/api/events/{event.id}/attendees/{second_user.id}",
    )

    assert response.status_code == 200

    socials = response.get_json()["attendee"]["socials"]

    assert {
        "platform": public_social.platform,
        "username": public_social.username,
        "profile_url": public_social.profile_url,
    } in socials

    assert {
        "platform": private_social.platform,
        "username": private_social.username,
        "profile_url": private_social.profile_url,
    } not in socials
