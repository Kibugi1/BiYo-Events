from datetime import datetime

from flask import Blueprint, g, jsonify, request
from sqlalchemy.exc import IntegrityError

from ..events.lifecycle import InvalidEventTransition
from ..events.moderator_service import ModeratorError, ModeratorService
from ..events.service import EventService
from .decorators import super_admin_required

events_bp = Blueprint("admin_events", __name__)


def event_to_dict(event):
    return {
        "id": event.id,
        "name": event.name,
        "slug": event.slug,
        "description": event.description,
        "venue": event.venue,
        "address": event.address,
        "city": event.city,
        "country": event.country,
        "starts_at": event.starts_at.isoformat(),
        "ends_at": event.ends_at.isoformat(),
        "access_code": event.access_code,
        "status": event.status,
        "registration_status": event.registration_status,
        "voting_status": event.voting_status,
        "created_by": event.created_by,
        "created_at": event.created_at.isoformat(),
    }


@events_bp.post("/")
@super_admin_required
def create_event():
    data = request.get_json() or {}

    required_fields = [
        "name",
        "slug",
        "venue",
        "starts_at",
        "ends_at",
        "access_code",
    ]

    missing = [field for field in required_fields if not data.get(field)]

    if missing:
        return (
            jsonify(
                {
                    "error": "Missing required fields",
                    "fields": missing,
                }
            ),
            400,
        )

    try:
        starts_at = datetime.fromisoformat(data["starts_at"])
        ends_at = datetime.fromisoformat(data["ends_at"])
    except ValueError:
        return (
            jsonify(
                {"error": "starts_at and ends_at must be valid ISO datetime values"}
            ),
            400,
        )

    if ends_at <= starts_at:
        return jsonify({"error": "ends_at must be after starts_at"}), 400

    try:
        event = EventService.create_event(
            name=data["name"].strip(),
            slug=data["slug"].strip().lower(),
            description=data.get("description"),
            venue=data["venue"].strip(),
            address=data.get("address"),
            city=data.get("city"),
            country=data.get("country", "Kenya"),
            starts_at=starts_at,
            ends_at=ends_at,
            access_code=data["access_code"].strip(),
            created_by=g.current_user.id,
        )
    except IntegrityError:
        from ..extensions import db

        db.session.rollback()

        return (
            jsonify(
                {"error": "An event with this slug or access code already exists."}
            ),
            409,
        )

    return (
        jsonify(
            {
                "message": "Event created successfully",
                "event": event_to_dict(event),
            }
        ),
        201,
    )


@events_bp.get("/")
@super_admin_required
def list_events():
    events = EventService.get_events()

    return jsonify({"events": [event_to_dict(event) for event in events]})


@events_bp.get("/<int:event_id>")
@super_admin_required
def get_event(event_id):
    event = EventService.get_event(event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    return jsonify({"event": event_to_dict(event)})


@events_bp.patch("/<int:event_id>")
@super_admin_required
def update_event(event_id):
    event = EventService.get_event(event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    data = request.get_json() or {}

    allowed_fields = {
        "name",
        "slug",
        "description",
        "venue",
        "address",
        "city",
        "country",
        "starts_at",
        "ends_at",
        "access_code",
    }

    updates = {key: value for key, value in data.items() if key in allowed_fields}

    for field in ("starts_at", "ends_at"):
        if field in updates:
            try:
                updates[field] = datetime.fromisoformat(updates[field])
            except ValueError:
                return jsonify({"error": f"{field} must be a valid ISO datetime"}), 400

    if (
        "starts_at" in updates
        and "ends_at" not in updates
        and updates["starts_at"] >= event.ends_at
    ):
        return jsonify({"error": "starts_at must be before ends_at"}), 400

    if (
        "ends_at" in updates
        and "starts_at" not in updates
        and updates["ends_at"] <= event.starts_at
    ):
        return jsonify({"error": "ends_at must be after starts_at"}), 400

    if (
        "starts_at" in updates
        and "ends_at" in updates
        and updates["ends_at"] <= updates["starts_at"]
    ):
        return jsonify({"error": "ends_at must be after starts_at"}), 400

    try:
        event = EventService.update_event(
            event,
            **updates,
        )
    except IntegrityError:
        from ..extensions import db

        db.session.rollback()

        return (
            jsonify(
                {"error": "An event with this slug or access code already exists."}
            ),
            409,
        )

    return jsonify(
        {
            "message": "Event updated successfully",
            "event": event_to_dict(event),
        }
    )


@events_bp.post("/<int:event_id>/publish")
@super_admin_required
def publish_event(event_id):
    return transition_event(
        event_id,
        EventService.publish,
    )


@events_bp.post("/<int:event_id>/registration/open")
@super_admin_required
def open_registration(event_id):
    return transition_event(
        event_id,
        EventService.open_registration,
    )


@events_bp.post("/<int:event_id>/registration/close")
@super_admin_required
def close_registration(event_id):
    return transition_event(
        event_id,
        EventService.close_registration,
    )


@events_bp.post("/<int:event_id>/voting/open")
@super_admin_required
def open_voting(event_id):
    return transition_event(
        event_id,
        EventService.open_voting,
    )


@events_bp.post("/<int:event_id>/voting/close")
@super_admin_required
def close_voting(event_id):
    return transition_event(
        event_id,
        EventService.close_voting,
    )


@events_bp.post("/<int:event_id>/cancel")
@super_admin_required
def cancel_event(event_id):
    return transition_event(
        event_id,
        EventService.cancel,
    )


@events_bp.post("/<int:event_id>/complete")
@super_admin_required
def complete_event(event_id):
    return transition_event(
        event_id,
        EventService.complete,
    )


def transition_event(event_id, action):
    event = EventService.get_event(event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    try:
        event = action(event)
    except InvalidEventTransition as error:
        return jsonify({"error": str(error)}), 409

    return jsonify(
        {
            "message": "Event updated successfully",
            "event": event_to_dict(event),
        }
    )


@events_bp.post("/<int:event_id>/moderators/open")
@super_admin_required
def open_moderator_voting(event_id):
    event = EventService.get_event(event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    try:
        event = ModeratorService.open_voting(event)
    except ModeratorError as exc:
        return jsonify({"error": str(exc)}), 409

    return jsonify(
        {
            "message": "Moderator voting opened",
            "event_id": event.id,
            "moderator_voting_status": event.moderator_voting_status,
        }
    )


@events_bp.post("/<int:event_id>/moderators/close")
@super_admin_required
def close_moderator_voting(event_id):
    event = EventService.get_event(event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    try:
        event = ModeratorService.close_voting(event)
    except ModeratorError as exc:
        return jsonify({"error": str(exc)}), 409

    return jsonify(
        {
            "message": "Moderator voting closed",
            "event_id": event.id,
            "moderator_voting_status": event.moderator_voting_status,
        }
    )


@events_bp.post("/<int:event_id>/moderators/finalize")
@super_admin_required
def finalize_moderator_voting(event_id):
    event = EventService.get_event(event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    try:
        selected = ModeratorService.finalize(event)
    except ModeratorError as exc:
        return jsonify({"error": str(exc)}), 409

    return jsonify(
        {
            "message": "Moderator election finalized",
            "event_id": event.id,
            "moderator_voting_status": event.moderator_voting_status,
            "moderators": [
                {
                    "candidate_id": candidate.id,
                    "membership_id": candidate.membership_id,
                    "user_id": candidate.membership.user_id,
                }
                for candidate in selected
            ],
        }
    )
