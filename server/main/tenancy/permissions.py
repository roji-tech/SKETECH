from __future__ import annotations
from typing import Iterable
from rest_framework.permissions import BasePermission, SAFE_METHODS

class RoleRequired(BasePermission):
    """Allow when user's `role` is one of `allowed_roles` on the view; superuser bypass."""
    allowed_roles: Iterable[str] = ()

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        allowed = getattr(view, "allowed_roles", tuple(self.allowed_roles))
        return getattr(user, "role", None) in allowed

class HasAnyPosition(BasePermission):
    """Allow when the user has any position in the current school; superuser bypass."""
    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.position_assignments.filter(position__school=request.school).exists()

class HasPositionPerm(BasePermission):
    """
    Allow when the user holds at least one Position in current school that includes
    any of the `required_perms` listed on the view (codename or 'app_label.codename').
    """
    required_perms: Iterable[str] = ()

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        req = tuple(getattr(view, "required_perms", tuple(self.required_perms)))
        if not req:
            return True

        # Accept codename or "app.codename"
        wanted = {p.split(".", 1)[-1] for p in req}
        # wanted = {p.split(".", 1)[-1] for p in getattr(view, "required_perms", tuple(self.required_perms))}
        return user.position_assignments.filter(
            position__school=request.school,
            position__permissions__codename__in=wanted,
        ).exists()
        
        




# ==============================================
# File: main/permissions.py
# Purpose: RBAC for DRF + object/school scoping
# ==============================================
from __future__ import annotations
from rest_framework.permissions import BasePermission, SAFE_METHODS

ROLE_SUPERADMIN = "superadmin"
ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_TEACHER = "teacher"
ROLE_STUDENT = "student"


class IsAuthenticatedAndInSchool(BasePermission):
    """User must be authenticated and bound to the current school."""
    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request, "school", None) is not None


class HasRole(BasePermission):
    """Allow only users whose role is in `allowed_roles` on the view."""
    allowed_roles: tuple[str, ...] = ()

    def has_permission(self, request, view) -> bool:
        if not request.user or not request.user.is_authenticated:
            return False
        roles = getattr(view, "allowed_roles", None) or self.allowed_roles
        return (getattr(request.user, "role", None) in roles) or getattr(request.user, "is_superuser", False)


class IsSchoolAdminOrOwner(HasRole):
    allowed_roles = (ROLE_SUPERADMIN, ROLE_OWNER, ROLE_ADMIN)


class IsTeacher(HasRole):
    allowed_roles = (ROLE_TEACHER,)


class IsStudent(HasRole):
    allowed_roles = (ROLE_STUDENT,)


class IsSameSchoolObject(BasePermission):
    """Object‑level check: instance.school must equal request.school."""
    def has_object_permission(self, request, view, obj) -> bool:
        school = getattr(request, "school", None)
        obj_school = getattr(obj, "school", None)
        return school is not None and obj_school is not None and school == obj_school

