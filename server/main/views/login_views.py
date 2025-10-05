# from django.http import HttpResponse
# from django.contrib import messages
# from django.contrib.auth import authenticate, login
# from django.shortcuts import get_object_or_404, redirect, render
# from django.views import View
# from django.views.generic import ListView

# from django.urls import reverse_lazy
# from django.contrib.auth.views import LoginView
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.views.generic import TemplateView

# from django.core.exceptions import (
#     NON_FIELD_ERRORS,
#     FieldError,
#     ImproperlyConfigured,
#     ValidationError,
# )

# from django import forms
# from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# from ..models import User, STUDENT, TEACHER, SUPERADMIN, ADMIN, OWNER
# # Custom Authentication Form


# class CustomAuthenticationForm(AuthenticationForm):
#     role = None
#     # username = forms.EmailField(
#     #     label="Email", max_length=254, widget=forms.EmailInput(attrs={'autofocus': True}))

#     # username = forms.CharField(
#     #     label="Email or Student ID", max_length=254, widget=forms.TextInput(attrs={'autofocus': True})
#     # )

#     def __init__(self, request=None, *args, **kwargs):
#         self.role = kwargs.pop('role', None)

#         if not self.role:
#             raise ImproperlyConfigured(
#                 "The role kwargs must be supplied to CustomAuthenticationForm, The role attribute must be set in CustomLoginView or its subclasses."
#             )

#         super().__init__(*args, **kwargs)

#         if self.role == STUDENT:
#             self.fields['username'].widget = forms.TextInput(
#                 attrs={'autofocus': True, 'placeholder': 'Student ID'})
#             self.fields['username'].label = "Student ID"

#     def clean(self):
#         # Override the clean method to support `student_id` login for students
#         username = self.cleaned_data.get('username')
#         password = self.cleaned_data.get('password')

#         if username and password:
#             if self.role == STUDENT:
#                 # Authenticate using student_id
#                 self.user_cache = self.authenticate_student(username, password)
#             else:
#                 # Default email-based authentication for other roles
#                 self.user_cache = authenticate(
#                     self.request, username=username, password=password)

#             if self.user_cache is None:
#                 raise self.get_invalid_login_error()
#             else:
#                 self.confirm_login_allowed(self.user_cache)

#         return self.cleaned_data

#     def authenticate_student(self, student_id, password):
#         """Custom authentication logic for students using student_id."""
#         try:
#             # Get the user based on student_id from the Student model
#             user = User.objects.get(student_profile__student_id=student_id)
#         except User.DoesNotExist:
#             raise ValidationError(
#                 "Invalid student ID or password.", code='invalid_login')

#         # Verify the password for the user
#         if user.check_password(password):
#             return user

#         raise ValidationError(
#             "Invalid student ID or password.", code='invalid_login')

#     # def confirm_login_allowed(self, user):
#     #     # Logic to confirm login is allowed based on the user role and status
#     #     if not user.is_active:
#     #         raise ValidationError("This account is inactive.", code='inactive')

#     #     if self.role == STUDENT and user.role != STUDENT:
#     #         raise ValidationError(
#     #             "Invalid login, access denied.", code='access_denied')
#     #     elif self.role != STUDENT and user.role != self.role:
#     #         raise ValidationError(
#     #             "Invalid login, access denied.", code='access_denied')

#     def confirm_login_allowed(self, user):
#         user_role = user.role
#         if user.role == OWNER:
#             user_role = ADMIN

#         print("user_role", "self.role")
#         print(user_role, self.role)
#         if not user.is_active:
#             raise forms.ValidationError(
#                 "This account is inactive.", code='inactive')

#         if user_role != self.role or user_role == SUPERADMIN:
#             raise forms.ValidationError(
#                 "Invalid login, Access Denied", code='access_denied')

#     def clean_username(self):
#         username = self.cleaned_data.get('username')

#         # Validate based on the role
#         if self.role == STUDENT:
#             # Add custom validation for student_id if necessary
#             if not str(username).isalnum():
#                 raise forms.ValidationError("Student ID must be alphanumeric.")
#         else:
#             # Basic email validation
#             if "@" not in username:
#                 raise forms.ValidationError("Enter a valid email address.")

#         return username


# class SuperAdminAuthenticationForm(CustomAuthenticationForm):
#     role = SUPERADMIN

#     def confirm_login_allowed(self, user):
#         if not user.is_active:
#             raise forms.ValidationError(
#                 "This account is inactive.", code='inactive')

#         if user.role != SUPERADMIN:
#             raise forms.ValidationError(
#                 "Invalid login, Access Denied", code='access_denied')


# class CustomLoginView(LoginView):
#     authentication_form = CustomAuthenticationForm
#     template_name = "myadmin/login.html"
#     role = None
#     page = None

#     def __init__(self, *args, **kwargs):
#         if not self.role:
#             raise ImproperlyConfigured(
#                 "The role kwargs must be supplied to CustomLoginView."
#             )
#         print(self.__class__, self.role)

#         if not self.page:
#             raise ImproperlyConfigured(
#                 "The page attribute must be set in CustomLoginView or its subclasses. (e.g Teacher, Admin, Student )"
#             )
#         super().__init__(*args, **kwargs)

#     def get_form(self, form_class=None):
#         print(self.__class__, self.role)

#         if form_class is None:
#             form_class = self.get_form_class()
#         return form_class(role=self.role, **self.get_form_kwargs())

#     def form_invalid(self, form):
#         messages.error(self.request, "Invalid email or password.")
#         return super().form_invalid(form)

#     def get_success_url(self):
#         # Check if there's a 'next' parameter in the query string
#         next_url = self.request.GET.get('next')

#         if next_url:
#             return next_url

#         # Fallback to role-based default URL
#         user = self.request.user
#         if user.is_owner or user.is_admin:
#             return reverse_lazy('myadmin')
#         elif user.is_teacher:
#             return reverse_lazy('teachers')
#         elif user.is_student:
#             return reverse_lazy('students')
#         else:
#             return reverse_lazy('home')  # Default fallback

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context.update({"page": self.page, })
#         return context


# class AdminLoginView(CustomLoginView):
#     template_name = "myadmin/login.html"
#     role = ADMIN
#     page = "Admin"


# class TeacherLoginView(CustomLoginView):
#     page = "Teacher"
#     template_name = "myadmin/login.html"
#     role = TEACHER


# class StudentLoginView(CustomLoginView):
#     template_name = "myadmin/login.html"
#     page = "Student"
#     role = STUDENT
#     ...

#     def form_invalid(self, form):
#         messages.error(self.request, "Invalid student ID or password.")
#         return super().form_invalid(form)

#     def get_success_url(self):
#         # Redirect to the student dashboard after successful login
#         return reverse_lazy('students')


# class SuperAdminLoginView(CustomLoginView):
#     role = SUPERADMIN
#     authentication_form = CustomAuthenticationForm
#     template_name = 'login.htm'
#     page = "Super Admin"

#     def form_invalid(self, form):
#         messages.error(self.request, "Invalid email or password.")
#         return super().form_invalid(form)

#     def get_success_url(self):
#         user = self.request.user

#         if user.is_superadmin:
#             return reverse_lazy('superadmin')
#         else:
#             return reverse_lazy('home')  # Fallback
