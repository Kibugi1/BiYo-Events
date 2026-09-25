from datetime import datetime, timezone

from ..extensions import db


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )

    full_name = db.Column(db.String(150), nullable=False)

    username = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    outstation_id = db.Column(
        db.Integer,
        db.ForeignKey("outstations.id"),
        nullable=False,
    )

    jumuia = db.Column(db.String(150), nullable=True)

    field_of_study = db.Column(db.String(150), nullable=True)

    profession = db.Column(db.String(150), nullable=True)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship(
        "User",
        backref=db.backref("profile", uselist=False),
    )

    outstation = db.relationship(
        "Outstation",
        backref="profiles",
    )

    def __repr__(self):
        return f"<UserProfile {self.username}>"
