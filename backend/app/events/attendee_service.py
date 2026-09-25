from ..models import EventMembership, UserProfile


class AttendeeService:
    @staticmethod
    def get_event_attendees(event):
        return (
            EventMembership.query.filter_by(event_id=event.id)
            .join(UserProfile, UserProfile.user_id == EventMembership.user_id)
            .order_by(EventMembership.joined_at.asc())
            .all()
        )

    @staticmethod
    def get_event_attendee(event, user_id):
        return (
            EventMembership.query.filter_by(
                event_id=event.id,
                user_id=user_id,
            )
            .join(UserProfile, UserProfile.user_id == EventMembership.user_id)
            .first()
        )

    @staticmethod
    def serialize_attendee(membership):
        profile = membership.user.profile

        return {
            "user_id": membership.user_id,
            "full_name": profile.full_name,
            "username": profile.username,
            "outstation": {
                "id": profile.outstation.id,
                "name": profile.outstation.name,
                "slug": profile.outstation.slug,
            },
            "jumuia": profile.jumuia,
            "field_of_study": profile.field_of_study,
            "profession": profile.profession,
            "socials": [
                {
                    "platform": social.platform,
                    "username": social.username,
                    "profile_url": social.profile_url,
                }
                for social in profile.socials
                if social.is_public
            ],
        }
