from flask import g, session

from ..extensions import db

from ..models import User


def load_current_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.current_user = None
        return

    g.current_user = db.session.get(User, user_id)
