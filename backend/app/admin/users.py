from flask import Blueprint, jsonify

from ..models import User
from .decorators import super_admin_required

users_bp = Blueprint("admin_users", __name__)


@users_bp.get("/")
@super_admin_required
def list_users():
    users = User.query.order_by(User.created_at.desc()).all()

    return jsonify(
        {
            "users": [
                {
                    "id": user.id,
                    "email": user.email,
                    "system_role": user.system_role,
                    "created_at": user.created_at.isoformat(),
                }
                for user in users
            ],
            "total": len(users),
        }
    )


@users_bp.get("/<int:user_id>")
@super_admin_required
def get_user(user_id):
    user = User.query.get(user_id)

    if user is None:
        return jsonify({"error": "User not found"}), 404

    return jsonify(
        {
            "id": user.id,
            "email": user.email,
            "system_role": user.system_role,
            "created_at": user.created_at.isoformat(),
        }
    )
