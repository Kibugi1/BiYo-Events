import click

from ...auth.roles import SystemRole
from ...extensions import db
from ...models import User


def register_commands(app):
    @app.cli.command("bootstrap-admin")
    @click.option(
        "--email",
        prompt="Super Admin email",
        help="Email address for the first Super Admin.",
    )
    def bootstrap_admin(email):
        """Create the first BiYo Events Super Admin."""

        email = email.strip().lower()

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            if existing_user.system_role == SystemRole.SUPER_ADMIN:
                click.echo("This user is already a Super Admin.")
                return

            click.echo("A user with this email already exists.")
            return

        admin = User(
            email=email,
            system_role=SystemRole.SUPER_ADMIN,
        )

        db.session.add(admin)
        db.session.commit()

        click.echo(f"Super Admin created successfully: {admin.email}")
