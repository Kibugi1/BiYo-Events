from ..models.event_membership import EventMembership


def get_event_membership(event, user):
    if user is None:
        return None

    return EventMembership.query.filter_by(
        event_id=event.id,
        user_id=user.id,
    ).first()


def require_event_organizer(event, user):
    membership = get_event_membership(event, user)

    if membership is None:
        raise PermissionError(
            "You are not a member of this event"
        )

    if membership.role != "ORGANIZER":
        raise PermissionError(
            "Organizer access required"
        )

    return membership


def require_team_member(event, user, group_id):
    membership = EventMembership.query.filter_by(
        event_id=event.id,
        user_id=user.id,
        group_id=group_id,
    ).first()

    if membership is None:
        raise PermissionError(
            "You must be a member of this team"
        )

    return membership
