from datetime import datetime, timezone

from ..extensions import db


class UserSocial(db.Model):
    __tablename__ = "user_socials"

    id = db.Column(db.Integer, primary_key=True)

    user_profile_id = db.Column(
        db.Integer,
        db.ForeignKey("user_profiles.id"),
        nullable=False,
    )

    platform = db.Column(db.String(50), nullable=False)

    username = db.Column(db.String(100), nullable=True)

    profile_url = db.Column(db.String(255), nullable=True)

    is_public = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
    )

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

    profile = db.relationship(
        "UserProfile",
        backref=db.backref(
            "socials",
            cascade="all, delete-orphan",
        ),
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_profile_id",
            "platform",
            name="uq_user_social_platform",
        ),
    )

    def __repr__(self):
        return (
            f"<UserSocial profile={self.user_profile_id} " f"platform={self.platform}>"
        )
