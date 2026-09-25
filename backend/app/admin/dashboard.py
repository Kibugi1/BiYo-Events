from flask import Blueprint, jsonify

from ..models import Event, EventMembership, User
from .decorators import super_admin_required

dashboard_bp = Blueprint(
    "admin_dashboard",
    __name__,
)


@dashboard_bp.get("/")
@super_admin_required
def dashboard():
    total_users = User.query.count()
    total_events = Event.query.count()
    total_memberships = EventMembership.query.count()

    return jsonify(
        {
            "users": {
                "total": total_users,
            },
            "events": {
                "total": total_events,
            },
            "memberships": {
                "total": total_memberships,
            },
        }
    )
