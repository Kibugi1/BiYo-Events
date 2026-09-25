from flask import Blueprint, jsonify, session, url_for

from ..extensions import db
from ..models import User
from .google import oauth
from .roles import SystemRole

auth_bp = Blueprint(
    "auth",
    __name__,
)


@auth_bp.get("/google/login")
def google_login():
    redirect_uri = url_for(
        "auth.google_callback",
        _external=True,
    )

    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.get("/google/callback")
def google_callback():
    token = oauth.google.authorize_access_token()

    userinfo = token.get("userinfo")

    if not userinfo:
        return jsonify({"error": "Unable to retrieve Google user information"}), 400

    google_id = userinfo["sub"]
    email = userinfo["email"].strip().lower()

    user = User.query.filter_by(google_id=google_id).first()

    if user is None:
        user = User.query.filter_by(email=email).first()

    if user is None:
        user = User(
            google_id=google_id,
            email=email,
            system_role=SystemRole.USER,
        )

        db.session.add(user)

    else:
        user.google_id = google_id

    db.session.commit()

    session["user_id"] = user.id

    return jsonify(
        {
            "message": "Authentication successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "system_role": user.system_role,
            },
        }
    )
