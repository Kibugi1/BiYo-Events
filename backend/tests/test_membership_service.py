from datetime import datetime, timezone

import pytest

from app.events.membership_service import MembershipService
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


def test_user_with_complete_profile_can_join_event(
    app,
    user,
    outstation,
    event,
):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
        jumuia="St. Camillus Jumuia",
        field_of_study="Software Engineering",
    )

    membership, created = MembershipService.join_event(event, user)

    assert created is True
    assert membership.user_id == user.id
    assert membership.event_id == event.id
    assert membership.role == "PARTICIPANT"


def test_user_without_profile_cannot_join_event(
    app,
    user,
    event,
):
    with pytest.raises(
        ValueError,
        match="complete your profile",
    ):
        MembershipService.join_event(event, user)

    membership = EventMembership.query.filter_by(
        event_id=event.id,
        user_id=user.id,
    ).first()

    assert membership is None


def test_user_with_incomplete_profile_cannot_join_event(
    app,
    user,
    outstation,
    event,
):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
    )

    with pytest.raises(
        ValueError,
        match="complete your profile",
    ):
        MembershipService.join_event(event, user)

    membership = EventMembership.query.filter_by(
        event_id=event.id,
        user_id=user.id,
    ).first()

    assert membership is None


def test_join_event_is_idempotent_for_existing_member(
    app,
    user,
    outstation,
    event,
):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
        jumuia="St. Camillus Jumuia",
        field_of_study="Software Engineering",
    )

    first_membership, first_created = MembershipService.join_event(
        event,
        user,
    )

    second_membership, second_created = MembershipService.join_event(
        event,
        user,
    )

    assert first_created is True
    assert second_created is False
    assert second_membership.id == first_membership.id

    memberships = EventMembership.query.filter_by(
        event_id=event.id,
        user_id=user.id,
    ).all()

    assert len(memberships) == 1
