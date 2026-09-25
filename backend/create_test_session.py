from app import create_app
from app.models import User

app = create_app()


def create_session(user_id, filename):
    with app.app_context():
        user = User.query.get(user_id)

        if user is None:
            print(f"User {user_id} not found")
            return

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["user_id"] = user.id

            cookie = client.get_cookie("session")

            with open(filename, "w") as file:
                file.write(cookie.value)

        print(f"Created {filename}")
        print(f"User: {user.email}")
        print(f"User ID: {user.id}")


create_session(1, "admin.session")
create_session(2, "alice.session")
create_session(3, "carol.session")
create_session(4, "david.session")
create_session(5, "eve.session")
