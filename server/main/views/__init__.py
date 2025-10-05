# from django.shortcuts import render
# from main.models import User
# from main.models import School
# from .teacher_views import *
# from .admin_views import *
# from .student_views import *
# from .superadmin_views import *
# from .settings import *

# from .gmeet_views import *
# from .lesson_plan_views import *
# from .profile_views import *

# from django.shortcuts import redirect
# from django.views import View
# from django.contrib.auth.mixins import LoginRequiredMixin
# from django.contrib.auth import logout
# # Assuming your User model has a `role` attribute


# class DashboardRedirectView(LoginRequiredMixin, View):
#     def get(self, request, *args, **kwargs):
#         # Check user's role and redirect accordingly
#         user: User = request.user
#         if user.is_student:
#             return redirect('students')
#         elif user.is_teacher:
#             return redirect('teachers')
#         elif user.is_admin:
#             return redirect('myadmin')
#         else:
#             # If no matching role, redirect to a default dashboard
#             return redirect('home')


# class LogoutRedirectView(LoginRequiredMixin, View):
#     def get(self, request, *args, **kwargs):
#         try:
#             user = request.user
#             role = user.role

#             # Log the user out first
#             logout(request)

#             # Check user's role and redirect accordingly
#             if role == 'student':
#                 return redirect('student-login')
#             elif role == 'teacher':
#                 return redirect('teacher-login')
#             elif role == 'admin':
#                 return redirect('admin-login')
#             else:
#                 # If no matching role, redirect to a default login
#                 return redirect('home')
#         except Exception as e:
#             print(e)
#             return redirect('home')
