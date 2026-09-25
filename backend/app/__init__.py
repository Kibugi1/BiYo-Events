import os

from dotenv import load_dotenv
from flask import Flask

from .admin.users import users_bp
from .auth.current_user import load_current_user
from .auth.google import init_oauth
from .auth.routes import auth_bp
from .events.routes import events_bp
from .extensions import cors, db, migrate
from .routes.profile import profile_bp

load_dotenv()


def create_app(config=None):
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL", "sqlite:///biyo_events.db"
    )

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if config:
        app.config.update(config)

    db.init_app(app)

    migrate.init_app(app, db)

    cors.init_app(app)

    init_oauth(app)

    from .admin.dashboard import dashboard_bp
    from .admin.events import events_bp as admin_events_bp
    from .admin.routes import admin_bp
    from .routes.health import health_bp

    app.register_blueprint(
        health_bp,
        url_prefix="/api",
    )

    app.register_blueprint(
        admin_bp,
        url_prefix="/api/admin",
    )

    app.register_blueprint(
        auth_bp,
        url_prefix="/api/auth",
    )

    app.register_blueprint(
        dashboard_bp,
        url_prefix="/api/admin/dashboard",
    )

    app.register_blueprint(
        users_bp,
        url_prefix="/api/admin/users",
    )

    app.register_blueprint(
        admin_events_bp,
        url_prefix="/api/admin/events",
    )

    app.register_blueprint(
        events_bp,
        url_prefix="/api/events",
    )

    app.register_blueprint(
        profile_bp,
        url_prefix="/api/profile",
    )

    from .admin.commands.bootstrap import register_commands

    register_commands(app)
    app.before_request(load_current_user)

    return app
