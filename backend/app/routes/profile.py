from flask import Blueprint, g, jsonify, request

from ..services.profile_service import ProfileService

profile_bp = Blueprint("profile", __name__)


@profile_bp.get("")
def get_profile():
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    profile = ProfileService.get_profile(user)

    if profile is None:
        return jsonify({"error": "Profile not found"}), 404

    return jsonify(
        {
            "profile": {
                "id": profile.id,
                "user_id": profile.user_id,
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
                        "id": social.id,
                        "platform": social.platform,
                        "username": social.username,
                        "profile_url": social.profile_url,
                        "is_public": social.is_public,
                    }
                    for social in profile.socials
                ],
            }
        }
    )




@profile_bp.post("")
def create_profile():
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}

    required_fields = [
        "full_name",
        "username",
        "outstation_id",
    ]

    missing_fields = [field for field in required_fields if not data.get(field)]

    if missing_fields:
        return (
            jsonify(
                {
                    "error": "Missing required fields",
                    "fields": missing_fields,
                }
            ),
            400,
        )

    try:
        profile = ProfileService.create_profile(
            user=user,
            full_name=data["full_name"].strip(),
            username=data["username"].strip().lower(),
            outstation_id=int(data["outstation_id"]),
            jumuia=data.get("jumuia"),
            field_of_study=data.get("field_of_study"),
            profession=data.get("profession"),
        )

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409

    return (
        jsonify(
            {
                "message": "Profile created successfully",
                "profile": {
                    "id": profile.id,
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
                },
            }
        ),
        201,
    )

@profile_bp.post("/socials")
def add_social():
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}

    platform = data.get("platform", "").strip().lower()

    if not platform:
        return jsonify({"error": "platform is required"}), 400

    try:
        social = ProfileService.add_social(
            user=user,
            platform=platform,
            username=data.get("username"),
            profile_url=data.get("profile_url"),
            is_public=data.get("is_public", True),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409

    return (
        jsonify(
            {
                "message": "Social account added successfully",
                "social": {
                    "id": social.id,
                    "platform": social.platform,
                    "username": social.username,
                    "profile_url": social.profile_url,
                    "is_public": social.is_public,
                },
            }
        ),
        201,
    )


@profile_bp.patch("/socials/<int:social_id>")
def update_social(social_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    data = request.get_json() or {}

    try:
        social = ProfileService.update_social(
            user=user,
            social_id=social_id,
            username=data.get("username"),
            profile_url=data.get("profile_url"),
            is_public=data.get("is_public"),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify(
        {
            "message": "Social account updated successfully",
            "social": {
                "id": social.id,
                "platform": social.platform,
                "username": social.username,
                "profile_url": social.profile_url,
                "is_public": social.is_public,
            },
        }
    )


@profile_bp.delete("/socials/<int:social_id>")
def delete_social(social_id):
    user = getattr(g, "current_user", None)

    if user is None:
        return jsonify({"error": "Authentication required"}), 401

    try:
        ProfileService.remove_social(
            user=user,
            social_id=social_id,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404

    return jsonify(
        {
            "message": "Social account removed successfully",
        }
    )
