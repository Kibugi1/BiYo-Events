from datetime import datetime, timezone

import pytest

from app.events.attendee_service import AttendeeService
from app.models import Event, EventMembership, Outstation, User, UserProfile


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


def create_profile(database, user, outstation, username):
    profile = UserProfile(
        user_id=user.id,
        full_name=user.email.split("@")[0].title(),
        username=username,
        outstation_id=outstation.id,
    )
    database.session.add(profile)
    database.session.commit()
    return profile


def create_membership(database, event, user):
    membership = EventMembership(
        event_id=event.id,
        user_id=user.id,
        role="PARTICIPANT",
    )
    database.session.add(membership)
    database.session.commit()
    return membership


def test_get_event_attendees(
    app,
    database,
    event,
    user,
    second_user,
    outstation,
):
    create_profile(database, user, outstation, "brian")
    create_profile(database, second_user, outstation, "alice")

    create_membership(database, event, user)
    create_membership(database, event, second_user)

    attendees = AttendeeService.get_event_attendees(event)

    assert len(attendees) == 2
    assert attendees[0].user_id == user.id
    assert attendees[1].user_id == second_user.id


def test_get_event_attendee(
    app,
    database,
    event,
    user,
    outstation,
):
    create_profile(database, user, outstation, "brian")
    create_membership(database, event, user)

    membership = AttendeeService.get_event_attendee(
        event,
        user.id,
    )

    assert membership is not None
    assert membership.user_id == user.id
    assert membership.event_id == event.id


def test_get_event_attendee_returns_none_for_non_member(
    app,
    database,
    event,
    user,
    outstation,
):
    create_profile(database, user, outstation, "brian")

    membership = AttendeeService.get_event_attendee(
        event,
        user.id,
    )

    assert membership is None
