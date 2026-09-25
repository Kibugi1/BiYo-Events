from ..extensions import db
from ..models import EventMembership
from ..services.profile_service import ProfileService


class MembershipService:

    @staticmethod
    def join_event(event, user):
        existing_membership = EventMembership.query.filter_by(
            event_id=event.id,
            user_id=user.id,
        ).first()

        if existing_membership:
            return existing_membership, False

        if not ProfileService.is_complete(user):
            raise ValueError("Please complete your profile before joining the event.")

        membership = EventMembership(
            event_id=event.id,
            user_id=user.id,
            role="PARTICIPANT",
        )

        db.session.add(membership)
        db.session.commit()

        return membership, True

    @staticmethod
    def get_membership(event, user):
        return EventMembership.query.filter_by(
            event_id=event.id,
            user_id=user.id,
        ).first()

    @staticmethod
    def get_event_members(event):
        return (
            EventMembership.query.filter_by(event_id=event.id)
            .order_by(EventMembership.joined_at.asc())
            .all()
        )
