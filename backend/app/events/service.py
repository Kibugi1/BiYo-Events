from ..extensions import db
from ..models import Event, EventMembership
from .lifecycle import EventLifecycle


class EventService:

    @staticmethod
    def create_event(
        *,
        name,
        slug,
        description,
        venue,
        address,
        city,
        country,
        starts_at,
        ends_at,
        access_code,
        created_by,
    ):
        event = Event(
            name=name,
            slug=slug,
            description=description,
            venue=venue,
            address=address,
            city=city,
            country=country,
            starts_at=starts_at,
            ends_at=ends_at,
            access_code=access_code,
            created_by=created_by,
        )

        db.session.add(event)
        db.session.flush()

        organizer_membership = EventMembership(
            event_id=event.id,
            user_id=created_by,
            role="ORGANIZER",
        )

        db.session.add(organizer_membership)
        db.session.commit()

        return event

    @staticmethod
    def get_event(event_id):
        return db.session.get(Event, event_id)

    @staticmethod
    def get_events():
        return Event.query.order_by(Event.created_at.desc()).all()

    @staticmethod
    def update_event(event, **fields):
        for field, value in fields.items():
            if value is not None:
                setattr(event, field, value)

        db.session.commit()

        return event

    @staticmethod
    def publish(event):
        EventLifecycle.publish(event)
        db.session.commit()
        return event

    @staticmethod
    def open_registration(event):
        EventLifecycle.open_registration(event)
        db.session.commit()
        return event

    @staticmethod
    def close_registration(event):
        EventLifecycle.close_registration(event)
        db.session.commit()
        return event

    @staticmethod
    def open_voting(event):
        EventLifecycle.open_voting(event)
        db.session.commit()
        return event

    @staticmethod
    def close_voting(event):
        EventLifecycle.close_voting(event)
        db.session.commit()
        return event

    @staticmethod
    def cancel(event):
        EventLifecycle.cancel(event)
        db.session.commit()
        return event

    @staticmethod
    def complete(event):
        EventLifecycle.complete(event)
        db.session.commit()
        return event
