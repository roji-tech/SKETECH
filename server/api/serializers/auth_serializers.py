from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
import logging

from ..models import RefreshTokenUsage
from rest_framework_simplejwt.settings import api_settings
from django.db import transaction
from main.models import School, User

logger = logging.getLogger(__name__)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Customizes JWT default Serializer to add more information about user"""
    username_field = "email"

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # token["is_superuser"] = user.is_superuser
        user_school: School | None = School.get_user_school(user)
        if user_school:
            token["school_name"] = str(user_school.name)
            token["school_short_name"] = str(
                user_school.short_name)

            if user_school.logo:
                token["school_logo"] = str(user_school.logo.url)
        else:
            token["school_logo"] = ""
            token["school_name"] = ""
            token["school_short_name"] = ""

        token["username"] = user.username
        token["email"] = user.email

        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        # Safely access image URL
        token['image'] = user.image.url if user.image else None
        token['gender'] = user.gender
        token['phone'] = user.phone
        token['role'] = user.role
        return token


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    refresh = serializers.CharField()
    access = serializers.CharField(read_only=True)
    token_class = RefreshToken

    def validate(self, attrs):
        print(attrs)
        refresh = self.token_class(attrs["refresh"])
        # print(refresh.payload)

        data = {"access": str(refresh.access_token)}

        # Decode the refresh token to get the user ID
        try:
            payload = refresh.payload
            # Assuming 'user_id' is the key for the user ID in the payload
            user_id = payload['user_id']
        except KeyError:
            raise serializers.ValidationError("Invalid refresh token.")

        # Fetch the user from the database
        user = User.objects.get(id=user_id)

        TIME_RANGE_SECONDS = 3600  # 1 hour reuse range
        valid_token = RefreshTokenUsage.get_valid_token(
            user, TIME_RANGE_SECONDS)

        if valid_token:
            # Reuse the existing refresh token
            access_token = str(refresh.access_token)
            return {
                "access": access_token,
                "refresh": valid_token,
            }
        else:
            if api_settings.ROTATE_REFRESH_TOKENS:
                # If no valid token, proceed with the default behavior and rotation
                data = super().validate(attrs)

                # Save the new refresh token in the database
                RefreshTokenUsage.objects.create(
                    user=user,
                    refresh_token=data["refresh"],
                )
                if api_settings.BLACKLIST_AFTER_ROTATION:

                    try:
                        # Attempt to blacklist the given refresh token
                        refresh.blacklist()
                    except AttributeError:
                        # If blacklist app not installed, `blacklist` method will
                        # not be present
                        pass

                refresh.set_jti()
                refresh.set_exp()
                refresh.set_iat()

                data["refresh"] = str(refresh)

        return data


class SchoolRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['name', 'phone', 'email', 'address', 'subdomain']
        extra_kwargs = {
            'name': {'error_messages': {'required': 'School name is required.'}},
            'phone': {'error_messages': {'required': 'School phone number is required.'}},
            'email': {'error_messages': {'required': 'School email is required.'}},
            'address': {'required': True, 'allow_blank': True,
                        'error_messages': {'required': 'School address is required.'}},
            'subdomain': {'required': True,
                          'error_messages': {'required': 'Subdomain is required.'}}
        }

    def validate_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Please provide a school name.")
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "School name is too short. It should be at least 2 characters long.")
        return value.strip()

    def validate_phone(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Please provide a school phone number.")
        # Basic phone number validation - adjust regex as needed for your requirements
        if not re.match(r'^\+?[0-9\s-]{8,20}$', value):
            raise serializers.ValidationError(
                "Please enter a valid phone number.")
        return value.strip()

    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("School email is required.")
        try:
            validate_email(value)
            return value.lower().strip()
        except ValidationError:
            raise serializers.ValidationError(
                "Please enter a valid email address for the school."
            )

    def validate_subdomain(self, value):
        SYSTEM_SUBDOMAINS = ['www', 'app', 'api', 'admin']
        value = value.lower().strip()

        if value in SYSTEM_SUBDOMAINS:
            raise serializers.ValidationError(
                "This subdomain is reserved. Please choose a different one."
            )
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Subdomain is required."
            )

        if not re.match(r'^[a-z0-9]+(?:-[a-z0-9]+)*$', value):
            raise serializers.ValidationError(
                "Subdomain can only contain lowercase letters, numbers, and hyphens. "
                "It cannot start or end with a hyphen, or contain special characters or spaces."
            )

        if len(value) < 3:
            raise serializers.ValidationError(
                "Subdomain must be at least 3 characters long."
            )

        if len(value) > 63:
            raise serializers.ValidationError(
                "Subdomain cannot exceed 63 characters."
            )

        if School.objects.filter(subdomain__iexact=value).exists():
            raise serializers.ValidationError(
                "This subdomain is already taken. Please choose a different one."
            )

        return value

    def validate_address(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError(
                "School address is required."
            )
        if len(value.strip()) < 3:
            raise serializers.ValidationError(
                "Please provide a more detailed school address."
            )
        return value.strip()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Custom user registration serializer that handles both user and school creation.
    """
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password is required.',
            'blank': 'Password cannot be empty.'
        }
    )

    # School fields
    school_name = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            'required': 'School name is required.',
            'blank': 'School name cannot be empty.'
        }
    )
    school_phone = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            'required': 'School phone number is required.',
            'blank': 'School phone number cannot be empty.'
        }
    )
    school_email = serializers.EmailField(
        write_only=True,
        required=True,
        error_messages={
            'required': 'School email is required.',
            'blank': 'School email cannot be empty.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    school_address = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            'required': 'School address is required.',
            'blank': 'School address cannot be empty.'
        }
    )
    subdomain = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            'required': 'Subdomain is required.',
            'blank': 'Subdomain cannot be empty.'
        }
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'gender',
            'password', 'school_name', 'school_phone',
            'school_email', 'school_address', 'subdomain'
        ]
        extra_kwargs = {
            'first_name': {
                'error_messages': {
                    'required': 'First name is required.',
                    'blank': 'First name cannot be empty.'
                }
            },
            'last_name': {
                'error_messages': {
                    'required': 'Last name is required.',
                    'blank': 'Last name cannot be empty.'
                }
            },
            'email': {
                'required': True,
                'error_messages': {
                    'required': 'Email is required.',
                    'blank': 'Email cannot be empty.',
                    'invalid': 'Please enter a valid email address.'
                }
            },
            'gender': {
                'required': True,
                'error_messages': {
                    'required': 'Please select your gender.',
                    'invalid_choice': 'Please select a valid gender.'
                }
            }
        }

    def validate_first_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("First name is required.")
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "First name is too short. It should be at least 2 characters long.")
        if not re.match(r'^[\w\s\-\.\']+$', value):
            raise serializers.ValidationError(
                "First name contains invalid characters.")
        return value.strip()

    def validate_last_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Last name is required.")
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                "Last name is too short. It should be at least 2 characters long.")
        if not re.match(r'^[\w\s\-\.\']+$', value):
            raise serializers.ValidationError(
                "Last name contains invalid characters.")
        return value.strip()

    def validate_email(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Email is required.")
        try:
            validate_email(value)
            if User.objects.filter(email__iexact=value).exists():
                raise serializers.ValidationError(
                    "This email is already registered. Please use a different email or try to log in."
                )
            return value.lower().strip()
        except ValidationError:
            raise serializers.ValidationError(
                "Please enter a valid email address.")

    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError("Password is required.")
        try:
            validate_password(value)
            return value
        except ValidationError as e:
            # Convert Django's ValidationError to a more user-friendly format
            errors = list(e.messages)
            for i, error in enumerate(errors):
                if "too short" in error:
                    errors[i] = "Password is too short. It must contain at least 8 characters."
                elif "too common" in error:
                    errors[i] = "Password is too common. Please choose a stronger password."
                elif "entirely numeric" in error:
                    errors[i] = "Password cannot be entirely numeric."
                elif "similar to" in error:
                    errors[i] = "Password is too similar to your personal information."
            raise serializers.ValidationError(errors)

    def validate_gender(self, value):
        if not value or value not in dict(User.GENDER_CHOICES):
            raise serializers.ValidationError("Please select a valid gender.")
        return value

    def create(self, validated_data):
        """Create user and associated school"""
        # Extract school data
        school_data = {
            'name': validated_data.pop('school_name'),
            'phone': validated_data.pop('school_phone'),
            'email': validated_data.pop('school_email'),
            'address': validated_data.pop('school_address'),
            'subdomain': validated_data.pop('subdomain')
        }

        # Set user role and required fields
        # Set role to owner for school registration
        validated_data['role'] = 'owner'
        # Set is_staff to True for school owners
        validated_data['is_staff'] = True
        validated_data['is_active'] = True  # Ensure user is active

        password = validated_data.pop('password')

        print("validated_data", validated_data, "\n\n")
        print("school_data", school_data, "\n\n")

        # Create the user instance (don't save yet)
        user = User(**validated_data)
        user.set_password(password)

        with transaction.atomic():
            try:
                # Save user first to get user ID for school owner
                user.save()

                # Create school with the saved user as owner
                school_serializer = SchoolRegistrationSerializer(
                    data=school_data,
                    context=self.context  # Pass context for any nested serializers
                )
                if school_serializer.is_valid():
                    school = school_serializer.save(owner=user)
                else:
                    # Raise validation error with field-specific errors
                    errors = {}
                    for field, error_list in school_serializer.errors.items():
                        errors[field] = error_list

                    print("\n\n\n\nerrors", errors)
                    raise serializers.ValidationError(errors)

                # Update user with school reference and set username
                user.school = school
                user.username = f"{user.email}{User.ES_Sep}{school.id}"
                user.save()

                # TODO: Uncomment when email verification is set up
                # if not user.is_email_verified:
                #     send_verification_email_to_user(User, user, self.context['request'])
                print("\n\nUser created successfully: ",
                      user, "\n\n", "School: ", school)
                return user

            except Exception as e:
                logger.error(
                    f"Error in UserRegistrationSerializer: {str(e)}",
                    exc_info=True
                )
                # If we get here, it's an unexpected error
                error_msg = (
                    "An unexpected error occurred during registration. "
                    "Please try again later. If the problem persists, please contact support."
                )
                if isinstance(e, serializers.ValidationError):
                    # If the error is a serializer validation error,
                    # we need to handle it differently
                    errors = e.detail
                else:
                    # Otherwise, wrap the error in a ValidationError
                    errors = {"non_field_errors": [error_msg]}
                raise serializers.ValidationError(errors)
