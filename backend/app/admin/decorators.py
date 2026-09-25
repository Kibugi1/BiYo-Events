from functools import wraps

from flask import g, jsonify

from ..auth.roles import SystemRole


def super_admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        user = getattr(g, "current_user", None)

        if user is None:
            return jsonify({"error": "Authentication required"}), 401

        if user.system_role != SystemRole.SUPER_ADMIN:
            return jsonify({"error": "Super Admin access required"}), 403

        return view(*args, **kwargs)

    return wrapped_view
