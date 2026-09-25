import pytest

from app.extensions import db
from app.models import Outstation, User
from app.services.profile_service import ProfileService


@pytest.fixture
def user(database):
    user = User(
        email="brian@example.com",
        google_id="google-brian",
    )
    database.session.add(user)
    database.session.commit()

    return user


@pytest.fixture
def outstation(database):
    outstation = Outstation(
        name="St. Camillus",
        slug="st-camillus",
    )
    database.session.add(outstation)
    database.session.commit()

    return outstation


def test_create_profile(app, user, outstation):
    profile = ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
        jumuia="St. Camillus Jumuia",
        field_of_study="Software Engineering",
        profession="Software Developer",
    )

    assert profile.id is not None
    assert profile.user_id == user.id
    assert profile.full_name == "Brian Njuguna"
    assert profile.username == "brian"
    assert profile.outstation_id == outstation.id
    assert profile.jumuia == "St. Camillus Jumuia"
    assert profile.field_of_study == "Software Engineering"
    assert profile.profession == "Software Developer"


def test_cannot_create_duplicate_profile(app, user, outstation):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
    )

    with pytest.raises(ValueError, match="already has a profile"):
        ProfileService.create_profile(
            user=user,
            full_name="Brian Njuguna",
            username="brian2",
            outstation_id=outstation.id,
        )


def test_cannot_use_duplicate_username(app, user, outstation, database):
    another_user = User(
        email="another@example.com",
        google_id="google-another",
    )
    database.session.add(another_user)
    database.session.commit()

    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
    )

    with pytest.raises(ValueError, match="username is already taken"):
        ProfileService.create_profile(
            user=another_user,
            full_name="Another Brian",
            username="brian",
            outstation_id=outstation.id,
        )


def test_cannot_use_invalid_outstation(app, user):
    with pytest.raises(ValueError, match="Invalid outstation"):
        ProfileService.create_profile(
            user=user,
            full_name="Brian Njuguna",
            username="brian",
            outstation_id=999,
        )


def test_get_profile(app, user, outstation):
    created_profile = ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
    )

    profile = ProfileService.get_profile(user)

    assert profile.id == created_profile.id
    assert profile.username == "brian"


def test_profile_is_incomplete_when_user_has_no_profile(app, user):
    assert ProfileService.is_complete(user) is False


def test_profile_is_complete_when_required_fields_are_present(
    app,
    user,
    outstation,
):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
        jumuia="St. Camillus Jumuia",
        field_of_study="Software Engineering",
    )

    assert ProfileService.is_complete(user) is True


def test_profile_is_incomplete_without_jumuia(app, user, outstation):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
        field_of_study="Software Engineering",
    )

    assert ProfileService.is_complete(user) is False


def test_profile_is_incomplete_without_field_of_study(
    app,
    user,
    outstation,
):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
        jumuia="St. Camillus Jumuia",
    )

    assert ProfileService.is_complete(user) is False


def test_profile_is_incomplete_with_whitespace_required_field(
    app,
    user,
    outstation,
):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
        jumuia="   ",
        field_of_study="Software Engineering",
    )

    assert ProfileService.is_complete(user) is False


def test_update_profile(app, user, outstation, database):
    second_outstation = Outstation(
        name="St. Peter",
        slug="st-peter",
    )
    database.session.add(second_outstation)
    database.session.commit()

    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
    )

    profile = ProfileService.update_profile(
        user=user,
        full_name="Brian Njuguna Updated",
        username="brian-dev",
        outstation_id=second_outstation.id,
        jumuia="St. Peter Jumuia",
        field_of_study="Computer Science",
        profession="Software Engineer",
    )

    assert profile.full_name == "Brian Njuguna Updated"
    assert profile.username == "brian-dev"
    assert profile.outstation_id == second_outstation.id
    assert profile.jumuia == "St. Peter Jumuia"
    assert profile.field_of_study == "Computer Science"
    assert profile.profession == "Software Engineer"


def test_add_social(app, user, outstation):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
    )

    social = ProfileService.add_social(
        user=user,
        platform="instagram",
        username="brian.njuguna",
        profile_url="https://instagram.com/brian.njuguna",
    )

    assert social.id is not None
    assert social.platform == "instagram"
    assert social.username == "brian.njuguna"
    assert social.profile_url == "https://instagram.com/brian.njuguna"
    assert social.is_public is True


def test_cannot_add_same_social_platform_twice(app, user, outstation):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
    )

    ProfileService.add_social(
        user=user,
        platform="instagram",
        username="brian",
    )

    with pytest.raises(
        ValueError,
        match="social account already exists",
    ):
        ProfileService.add_social(
            user=user,
            platform="instagram",
            username="another_brian",
        )


def test_update_social(app, user, outstation):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
    )

    social = ProfileService.add_social(
        user=user,
        platform="instagram",
        username="brian",
    )

    updated_social = ProfileService.update_social(
        user=user,
        social_id=social.id,
        username="brian.dev",
        profile_url="https://instagram.com/brian.dev",
        is_public=False,
    )

    assert updated_social.username == "brian.dev"
    assert updated_social.profile_url == "https://instagram.com/brian.dev"
    assert updated_social.is_public is False


def test_remove_social(app, user, outstation):
    ProfileService.create_profile(
        user=user,
        full_name="Brian Njuguna",
        username="brian",
        outstation_id=outstation.id,
    )

    social = ProfileService.add_social(
        user=user,
        platform="instagram",
        username="brian",
    )

    ProfileService.remove_social(
        user=user,
        social_id=social.id,
    )

    assert database_social_does_not_exist(app, social.id)


def database_social_does_not_exist(app, social_id):
    from app.models import UserSocial

    return db.session.get(UserSocial, social_id) is None
