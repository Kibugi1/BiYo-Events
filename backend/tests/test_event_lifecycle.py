import pytest

from app.events.constants import (
    EventStatus,
    RegistrationStatus,
    VotingStatus,
)
from app.events.lifecycle import (
    EventLifecycle,
    InvalidEventTransition,
)


class FakeEvent:
    status = EventStatus.DRAFT
    registration_status = RegistrationStatus.CLOSED
    voting_status = VotingStatus.NOT_STARTED


def published_event():
    event = FakeEvent()
    event.status = EventStatus.PUBLISHED
    return event


def voting_ready_event():
    event = published_event()
    event.registration_status = RegistrationStatus.CLOSED
    return event


def test_publish_event():
    event = FakeEvent()

    EventLifecycle.publish(event)

    assert event.status == EventStatus.PUBLISHED


def test_cannot_open_registration_on_draft_event():
    event = FakeEvent()

    with pytest.raises(InvalidEventTransition):
        EventLifecycle.open_registration(event)


def test_open_registration():
    event = published_event()

    EventLifecycle.open_registration(event)

    assert event.registration_status == RegistrationStatus.OPEN


def test_close_registration():
    event = published_event()

    EventLifecycle.open_registration(event)
    EventLifecycle.close_registration(event)

    assert event.registration_status == RegistrationStatus.CLOSED


def test_cannot_open_voting_while_registration_is_open():
    event = published_event()

    EventLifecycle.open_registration(event)

    with pytest.raises(InvalidEventTransition):
        EventLifecycle.open_voting(event)


def test_open_voting():
    event = voting_ready_event()

    EventLifecycle.open_voting(event)

    assert event.voting_status == VotingStatus.OPEN


def test_close_voting():
    event = voting_ready_event()

    EventLifecycle.open_voting(event)
    EventLifecycle.close_voting(event)

    assert event.voting_status == VotingStatus.CLOSED


def test_cancel_event():
    event = published_event()

    EventLifecycle.cancel(event)

    assert event.status == EventStatus.CANCELLED
    assert event.registration_status == RegistrationStatus.CLOSED
    assert event.voting_status == VotingStatus.CLOSED


def test_cannot_complete_with_open_registration():
    event = published_event()
    EventLifecycle.open_registration(event)

    with pytest.raises(InvalidEventTransition):
        EventLifecycle.complete(event)


def test_complete_event():
    event = voting_ready_event()

    EventLifecycle.complete(event)

    assert event.status == EventStatus.COMPLETED
