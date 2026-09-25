from datetime import datetime, timezone

from ..extensions import db


class Outstation(db.Model):
    __tablename__ = "outstations"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(
        db.String(100),
        nullable=False,
        unique=True,
    )

    slug = db.Column(
        db.String(120),
        nullable=False,
        unique=True,
        index=True,
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self):
        return f"<Outstation {self.name}>"
