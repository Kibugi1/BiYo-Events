from app import create_app
from app.extensions import db
from app.models import Outstation

app = create_app()

OUTSTATIONS = [
    ("St. Peter", "st-peter"),
    ("St. Joseph", "st-joseph"),
    ("Our Lady of Fatima", "our-lady-of-fatima"),
    ("St. Mark", "st-mark"),
    ("St. Cecilia", "st-cecilia"),
    ("St. Camillus", "st-camillus"),
]


with app.app_context():
    for name, slug in OUTSTATIONS:
        existing = Outstation.query.filter_by(slug=slug).first()

        if existing:
            print(f"Already exists: {name}")
            continue

        db.session.add(
            Outstation(
                name=name,
                slug=slug,
            )
        )

    db.session.commit()

    print("Outstations seeded successfully.")
