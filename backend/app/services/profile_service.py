from ..extensions import db
from ..models import Outstation, UserProfile, UserSocial


class ProfileService:

    @staticmethod
    def get_profile(user):
        return UserProfile.query.filter_by(user_id=user.id).first()

    @staticmethod
    def is_complete(user):
        profile = ProfileService.get_profile(user)

        if not profile:
            return False

        required_fields = (
            profile.full_name,
            profile.username,
            profile.outstation_id,
            profile.jumuia,
            profile.field_of_study,
        )

        return all(
            value is not None and (not isinstance(value, str) or value.strip())
            for value in required_fields
        )

    @staticmethod
    def create_profile(
        user,
        full_name,
        username,
        outstation_id,
        jumuia=None,
        field_of_study=None,
        profession=None,
    ):
        existing_profile = UserProfile.query.filter_by(user_id=user.id).first()

        if existing_profile:
            raise ValueError("User already has a profile.")

        existing_username = UserProfile.query.filter_by(username=username).first()

        if existing_username:
            raise ValueError("BiYo username is already taken.")

        outstation = db.session.get(Outstation, outstation_id)

        if not outstation:
            raise ValueError("Invalid outstation.")

        profile = UserProfile(
            user_id=user.id,
            full_name=full_name,
            username=username,
            outstation_id=outstation.id,
            jumuia=jumuia,
            field_of_study=field_of_study,
            profession=profession,
        )

        db.session.add(profile)
        db.session.commit()

        return profile

    @staticmethod
    def update_profile(
        user,
        full_name=None,
        username=None,
        outstation_id=None,
        jumuia=None,
        field_of_study=None,
        profession=None,
    ):
        profile = ProfileService.get_profile(user)

        if not profile:
            raise ValueError("User profile does not exist.")

        if username and username != profile.username:
            existing_username = UserProfile.query.filter_by(username=username).first()

            if existing_username:
                raise ValueError("BiYo username is already taken.")

            profile.username = username

        if outstation_id is not None:
            outstation = db.session.get(Outstation, outstation_id)

            if not outstation:
                raise ValueError("Invalid outstation.")

            profile.outstation_id = outstation.id

        if full_name is not None:
            profile.full_name = full_name

        if jumuia is not None:
            profile.jumuia = jumuia

        if field_of_study is not None:
            profile.field_of_study = field_of_study

        if profession is not None:
            profile.profession = profession

        db.session.commit()

        return profile

    @staticmethod
    def add_social(
        user,
        platform,
        username=None,
        profile_url=None,
        is_public=True,
    ):
        profile = ProfileService.get_profile(user)

        if not profile:
            raise ValueError("User profile does not exist.")

        existing_social = UserSocial.query.filter_by(
            user_profile_id=profile.id,
            platform=platform,
        ).first()

        if existing_social:
            raise ValueError(f"{platform} social account already exists.")

        social = UserSocial(
            user_profile_id=profile.id,
            platform=platform,
            username=username,
            profile_url=profile_url,
            is_public=is_public,
        )

        db.session.add(social)
        db.session.commit()

        return social

    @staticmethod
    def update_social(
        user,
        social_id,
        username=None,
        profile_url=None,
        is_public=None,
    ):
        profile = ProfileService.get_profile(user)

        if not profile:
            raise ValueError("User profile does not exist.")

        social = UserSocial.query.filter_by(
            id=social_id,
            user_profile_id=profile.id,
        ).first()

        if not social:
            raise ValueError("Social account does not exist.")

        if username is not None:
            social.username = username

        if profile_url is not None:
            social.profile_url = profile_url

        if is_public is not None:
            social.is_public = is_public

        db.session.commit()

        return social

    @staticmethod
    def remove_social(user, social_id):
        profile = ProfileService.get_profile(user)

        if not profile:
            raise ValueError("User profile does not exist.")

        social = UserSocial.query.filter_by(
            id=social_id,
            user_profile_id=profile.id,
        ).first()

        if not social:
            raise ValueError("Social account does not exist.")

        db.session.delete(social)
        db.session.commit()
