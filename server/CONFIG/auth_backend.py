from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.conf import settings
from main.tenancy.managers import get_current_school
from main.models import Student  # Import Student model

UserModel = get_user_model()


class SchoolEmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        This function is used to authenticate a user. It first extracts the school from the request.
        Then it checks if the username is provided in the kwargs or in the request. If not, it returns None.
        the username here is the email of the user being passed in, so we use the get_username function to get the username.
        by passing in the email to the get_username function, it returns the actual username.
        Then it checks if the password is provided in the kwargs or in the request. If not, it returns None.
        Then it checks if the school is provided in the request. If not, it returns None.
        then it checks if the user exists in the database. If not, it returns None.
        Then it checks if the user is active. If not, it returns None.
        Then it checks if the password is correct. If not, it returns None.
        If all the above conditions are met, it returns the user.

        Authenticate a user using either email/username or student_id (for students).   
        """
        school = get_current_school()  # Extract school from request
        username = username or kwargs.get(UserModel.USERNAME_FIELD)

        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
            # username = kwargs.get("username")

        if username is None:
            username = kwargs.get("email")

        print(school, kwargs, UserModel.USERNAME_FIELD,
              UserModel.get_username(username))
        print("========SchoolEmailBackend=========")
        print(kwargs, username, password, school,
              getattr(request, 'school_code', None))

        if username is None or password is None or school is None:
            return None

        print("login", username, password, school,
              getattr(request, 'school_code', None))

        try:
            # Try to find user by username/email first
            if school:
                login_username = UserModel.get_username(username)
            else:
                login_username = f"{username}"

            print("login username", username, password,
                  len(password), login_username)

            try:
                # First try to get user by username/email
                user = UserModel.objects.get(
                    username=login_username, is_active=True)
            except UserModel.DoesNotExist:
                # If user not found by username/email, check if it's a student ID
                try:
                    student_id = kwargs.get("student_id") if kwargs.get(
                        "student_id") else username
                    student = Student.objects.get(
                        student_id=student_id, user__is_active=True)
                    user = student.user
                except Student.DoesNotExist:
                    return None

            print(user, user.check_password(password), self.user_can_authenticate(
                user), user.check_password(password) and self.user_can_authenticate(user))

            if user.check_password(password) and self.user_can_authenticate(user):
                request.user = user
                print("USER AUTHENTICATED", user)
                return user

        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return None

        return None
