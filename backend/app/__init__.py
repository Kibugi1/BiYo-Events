import os

from dotenv import load_dotenv
from flask import Flask

from .extensions import cors, db, migrate


load_dotenv()


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv(
        "SECRET_KEY",
        "dev-secret-key"
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "sqlite:///biyo_events.db"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    from .models import Event, EventMembership, User

    from .routes.health import health_bp

    app.register_blueprint(health_bp, url_prefix="/api")

    return app
