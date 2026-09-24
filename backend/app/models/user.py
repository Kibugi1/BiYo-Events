from datetime import datetime, timezone

from ..extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    google_id = db.Column(
        db.String(255),
        unique=True,
        nullable=True,
        index=True,
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    system_role = db.Column(
        db.String(50),
        nullable=False,
        default="USER",
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<User {self.email}>"
