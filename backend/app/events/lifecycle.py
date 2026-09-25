from .constants import (
    EventStatus,
    RegistrationStatus,
    VotingStatus,
)


class InvalidEventTransition(Exception):
    """Raised when an event lifecycle transition is not allowed."""


class EventLifecycle:
    @staticmethod
    def publish(event):
        if event.status != EventStatus.DRAFT:
            raise InvalidEventTransition("Only draft events can be published.")

        event.status = EventStatus.PUBLISHED

    @staticmethod
    def open_registration(event):
        if event.status != EventStatus.PUBLISHED:
            raise InvalidEventTransition(
                "Registration can only be opened for published events."
            )

        if event.registration_status == RegistrationStatus.OPEN:
            raise InvalidEventTransition("Registration is already open.")

        event.registration_status = RegistrationStatus.OPEN

    @staticmethod
    def close_registration(event):
        if event.registration_status != RegistrationStatus.OPEN:
            raise InvalidEventTransition("Registration is not open.")

        event.registration_status = RegistrationStatus.CLOSED

    @staticmethod
    def open_voting(event):
        if event.status != EventStatus.PUBLISHED:
            raise InvalidEventTransition(
                "Voting can only be opened for published events."
            )

        if event.registration_status != RegistrationStatus.CLOSED:
            raise InvalidEventTransition(
                "Registration must be closed before voting opens."
            )

        if event.voting_status != VotingStatus.NOT_STARTED:
            raise InvalidEventTransition("Voting has already started or finished.")

        event.voting_status = VotingStatus.OPEN

    @staticmethod
    def close_voting(event):
        if event.voting_status != VotingStatus.OPEN:
            raise InvalidEventTransition("Voting is not open.")

        event.voting_status = VotingStatus.CLOSED

    @staticmethod
    def cancel(event):
        if event.status in {
            EventStatus.CANCELLED,
            EventStatus.COMPLETED,
        }:
            raise InvalidEventTransition("This event cannot be cancelled.")

        event.status = EventStatus.CANCELLED
        event.registration_status = RegistrationStatus.CLOSED
        event.voting_status = VotingStatus.CLOSED

    @staticmethod
    def complete(event):
        if event.status != EventStatus.PUBLISHED:
            raise InvalidEventTransition("Only published events can be completed.")

        if event.voting_status == VotingStatus.OPEN:
            raise InvalidEventTransition(
                "Voting must be closed before the event can be completed."
            )

        if event.registration_status == RegistrationStatus.OPEN:
            raise InvalidEventTransition(
                "Registration must be closed before the event can be completed."
            )

        event.status = EventStatus.COMPLETED
