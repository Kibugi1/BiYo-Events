from flask import Blueprint, g, jsonify, request

from ..events.attendee_service import AttendeeService
from ..extensions import db
from ..models import Event, EventGroup, EventMembership, TeamLeaderVote
from .membership_service import MembershipService
from .moderator_service import ModeratorError, ModeratorService
from ..services.team_leader_service import TeamLeaderService
from .permissions import require_event_organizer

events_bp = Blueprint("events", __name__)


def membership_to_dict(membership):
    return {
        "id": membership.id,
        "event_id": membership.event_id,
        "user_id": membership.user_id,
        "role": membership.role,
        "joined_at": membership.joined_at.isoformat(),
    }


@events_bp.post("/join")
def join_event():
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}
    access_code = data.get("access_code", "").strip()

    if not access_code:
        return jsonify({"error": "access_code is required"}), 400

    event = Event.query.filter_by(access_code=access_code).first()

    if event is None:
        return jsonify({"error": "Invalid event access code"}), 404

    if event.registration_status != "OPEN":
        return jsonify({"error": "Registration is closed for this event"}), 409

    try:
        membership, created = MembershipService.join_event(
            event,
            user,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409

    if not created:
        return jsonify(
            {
                "message": "You are already a member of this event",
                "membership": membership_to_dict(membership),
            }
        )

    return (
        jsonify(
            {
                "message": "Joined event successfully",
                "membership": membership_to_dict(membership),
            }
        ),
        201,
    )


@events_bp.get(
    "/<int:event_id>/teams/<int:group_id>/leader-election"
)
def team_leader_election_status(event_id, group_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    group = EventGroup.query.filter_by(
        id=group_id,
        event_id=event.id,
    ).first()

    if group is None:
        return jsonify({"error": "Team not found"}), 404

    membership = EventMembership.query.filter_by(
        event_id=event.id,
        user_id=user.id,
        group_id=group.id,
    ).first()

    if membership is None:
        return jsonify(
            {"error": "You must be a member of this team"}
        ), 403

    leader = EventMembership.query.filter_by(
        event_id=event.id,
        group_id=group.id,
        team_role="LEADER",
    ).first()

    has_voted = TeamLeaderVote.query.filter_by(
        group_id=group.id,
        voter_membership_id=membership.id,
    ).first() is not None

    return jsonify(
        {
            "team": {
                "id": group.id,
                "name": group.name,
                "display_name": group.display_name,
            },
            "election": {
                "status": group.election_status,
                "has_voted": has_voted,
                "leader": (
                    {
                        "membership_id": leader.id,
                        "user_id": leader.user_id,
                    }
                    if leader
                    else None
                ),
            },
        }
    )

@events_bp.post(
    "/<int:event_id>/teams/<int:group_id>/leader-election/vote"
)
def vote_for_team_leader(event_id, group_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    if not request.data:
        return jsonify({"error": "Request body is required"}), 400

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({"error": "Invalid JSON body"}), 400

    candidate_membership_id = data.get("candidate_membership_id")

    if candidate_membership_id is None:
        return jsonify(
            {"error": "candidate_membership_id is required"}
        ), 400

    try:
        vote = TeamLeaderService.vote(
            event=event,
            voter=user,
            group_id=group_id,
            candidate_membership_id=candidate_membership_id,
        )

        return jsonify(
            {
                "message": "Team leader vote recorded",
                "vote": {
                    "id": vote.id,
                    "group_id": vote.group_id,
                    "voter_membership_id": vote.voter_membership_id,
                    "candidate_membership_id": vote.candidate_membership_id,
                },
            }
        ), 201

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

@events_bp.post(
    "/<int:event_id>/teams/<int:group_id>/leader-election/open"
)
def open_team_leader_election(event_id, group_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    try:
        require_event_organizer(event, user)
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403

    group = EventGroup.query.filter_by(
        id=group_id,
        event_id=event.id,
    ).first()

    if group is None:
        return jsonify({"error": "Team not found"}), 404

    try:
        TeamLeaderService.open_election(group)

        return jsonify(
            {
                "message": "Team leader election opened",
                "team": {
                    "id": group.id,
                    "name": group.name,
                    "display_name": group.display_name,
                },
                "election": {
                    "status": group.election_status,
                },
            }
        ), 200

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@events_bp.post(
    "/<int:event_id>/teams/<int:group_id>/leader-election/close"
)
def close_team_leader_election(event_id, group_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    try:
        require_event_organizer(event, user)
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403

    group = EventGroup.query.filter_by(
        id=group_id,
        event_id=event.id,
    ).first()

    if group is None:
        return jsonify({"error": "Team not found"}), 404

    try:
        TeamLeaderService.close_election(group)

        return jsonify(
            {
                "message": "Team leader election closed",
                "team": {
                    "id": group.id,
                    "name": group.name,
                    "display_name": group.display_name,
                },
                "election": {
                    "status": group.election_status,
                },
            }
        ), 200

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@events_bp.post(
    "/<int:event_id>/teams/<int:group_id>/leader-election/finalize"
)
def finalize_team_leader_election(event_id, group_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    try:
        require_event_organizer(event, user)
    except PermissionError as exc:
        return jsonify({"error": str(exc)}), 403

    group = EventGroup.query.filter_by(
        id=group_id,
        event_id=event.id,
    ).first()

    if group is None:
        return jsonify({"error": "Team not found"}), 404

    try:
        winner = TeamLeaderService.finalize_election(group)

        return jsonify(
            {
                "message": "Team leader election finalized",
                "team": {
                    "id": group.id,
                    "name": group.name,
                    "display_name": group.display_name,
                },
                "election": {
                    "status": group.election_status,
                    "leader": {
                        "membership_id": winner.id,
                        "user_id": winner.user_id,
                    },
                },
            }
        ), 200

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

@events_bp.get("/<int:event_id>/membership")
def my_membership(event_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    membership = MembershipService.get_membership(
        event,
        user,
    )

    if membership is None:
        return jsonify({"error": "You are not a member of this event"}), 404

    return jsonify({"membership": membership_to_dict(membership)})


@events_bp.post("/<int:event_id>/moderators/volunteer")
def volunteer_as_moderator(event_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    try:
        candidate, created = ModeratorService.volunteer(
            event,
            user,
        )
    except ModeratorError as exc:
        return jsonify({"error": str(exc)}), 409

    return (
        jsonify(
            {
                "message": (
                    "You are now a moderator candidate"
                    if created
                    else "You are already a moderator candidate"
                ),
                "candidate": moderator_candidate_to_dict(candidate),
            }
        ),
        201 if created else 200,
    )


@events_bp.post("/<int:event_id>/moderators/withdraw")
def withdraw_as_moderator(event_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    try:
        candidate = ModeratorService.withdraw(
            event,
            user,
        )
    except ModeratorError as exc:
        return jsonify({"error": str(exc)}), 409

    return jsonify(
        {
            "message": "Moderator candidacy withdrawn",
            "candidate": moderator_candidate_to_dict(candidate),
        }
    )


@events_bp.get("/<int:event_id>/moderators/candidates")
def moderator_candidates(event_id):
    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    candidates = ModeratorService.get_candidates(event)

    return jsonify(
        {
            "candidates": [
                moderator_candidate_to_dict(candidate) for candidate in candidates
            ]
        }
    )


@events_bp.post("/<int:event_id>/moderators/vote")
def vote_for_moderator(event_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    data = request.get_json() or {}
    candidate_id = data.get("candidate_id")

    if candidate_id is None:
        return jsonify({"error": "candidate_id is required"}), 400

    try:
        candidate_id = int(candidate_id)
    except (TypeError, ValueError):
        return jsonify({"error": "candidate_id must be an integer"}), 400

    try:
        vote = ModeratorService.vote(
            event,
            user,
            candidate_id,
        )
    except ModeratorError as exc:
        return jsonify({"error": str(exc)}), 409

    return (
        jsonify(
            {
                "message": "Vote recorded successfully",
                "vote": {
                    "id": vote.id,
                    "candidate_id": vote.candidate_id,
                    "created_at": vote.created_at.isoformat(),
                },
            }
        ),
        201,
    )


@events_bp.get("/<int:event_id>/moderators/results")
def moderator_results(event_id):
    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    results = ModeratorService.get_results(event)

    return jsonify(
        {
            "results": [
                {
                    "candidate_id": candidate.id,
                    "membership_id": candidate.membership_id,
                    "status": candidate.status,
                    "vote_count": vote_count,
                }
                for candidate, vote_count in results
            ]
        }
    )


def moderator_candidate_to_dict(candidate):
    membership = candidate.membership

    return {
        "id": candidate.id,
        "event_id": candidate.event_id,
        "membership_id": candidate.membership_id,
        "user_id": membership.user_id,
        "role": membership.role,
        "status": candidate.status,
        "created_at": candidate.created_at.isoformat(),
    }


@events_bp.get("/<int:event_id>/attendees")
def get_attendees(event_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    membership = MembershipService.get_membership(
        event,
        user,
    )

    if membership is None:
        return jsonify({"error": "You are not a member of this event"}), 403

    attendees = AttendeeService.get_event_attendees(event)

    return jsonify(
        {
            "attendees": [
                AttendeeService.serialize_attendee(attendee) for attendee in attendees
            ]
        }
    )


@events_bp.get("/<int:event_id>/attendees/<int:user_id>")
def get_attendee(event_id, user_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    event = db.session.get(Event, event_id)

    if event is None:
        return jsonify({"error": "Event not found"}), 404

    membership = MembershipService.get_membership(
        event,
        user,
    )

    if membership is None:
        return jsonify({"error": "You are not a member of this event"}), 403

    attendee = AttendeeService.get_event_attendee(
        event,
        user_id,
    )

    if attendee is None:
        return jsonify({"error": "Attendee not found"}), 404

    return jsonify({"attendee": AttendeeService.serialize_attendee(attendee)})
