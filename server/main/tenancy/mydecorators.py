from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from functools import wraps
from django.shortcuts import redirect, render


def role_required(role_check, login_url):
    def decorator(view_func_or_class):
        if isinstance(view_func_or_class, type):  # If it's a class-based view
            @method_decorator(login_required(login_url=login_url), name='dispatch')
            class Wrapper(view_func_or_class):
                def dispatch(self, request, *args, **kwargs):
                    if not role_check(request.user):
                        return render(request, '403.html', status=403)

                    return super().dispatch(request, *args, **kwargs)
            return Wrapper
        else:  # If it's a function-based view
            @wraps(view_func_or_class)
            def wrapper(request, *args, **kwargs):
                if not request.user.is_authenticated:
                    return redirect(f"{login_url}?next={request.path}")
                if not role_check(request.user):
                    # Render custom 403 template
                    return render(request, '403.html', status=403)

                return view_func_or_class(request, *args, **kwargs)
            return wrapper
    return decorator

# Specific role-based decorators


def admin_is_authenticated(view_func_or_class):
    return role_required(
        lambda user: user.is_admin or user.is_superadmin,
        login_url="/admin/login/"
    )(view_func_or_class)


def student_is_authenticated(view_func_or_class):
    return role_required(
        lambda user: user.is_student,
        login_url="/students/login/"
    )(view_func_or_class)


def teacher_is_authenticated(view_func_or_class):
    return role_required(
        lambda user: user.is_teacher,
        login_url="/staff/login/"
    )(view_func_or_class)


def superadmin_is_authenticated(view_func_or_class):
    return role_required(
        lambda user: user.is_superadmin,
        login_url="/djangoadmin/"
    )(view_func_or_class)


def admin_superadmin_teacher_is_authenticated(view_func_or_class):
    return role_required(
        lambda user: user.is_teacher or user.is_admin or user.is_superadmin,
        login_url="/staff/login/"
    )(view_func_or_class)


def is_authenticated(view_func_or_class):
    return role_required(
        lambda user: user.is_teacher or user.is_admin or user.is_superadmin or user.is_student,
        login_url="/"
    )(view_func_or_class)

# @admin_is_authenticated
# class AdminDashboardView(View):
#     # Your view logic here
#     pass


# @teacher_is_authenticated
# def teacher_dashboard(request):
#     # Your view logic here
#     return render(request, 'teacher_dashboard.html')
