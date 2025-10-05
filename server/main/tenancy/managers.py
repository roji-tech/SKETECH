# main/tenancy/manager.py
from __future__ import annotations

from typing import Optional, Any

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Q

from main.tenancy.threadlocals import get_current_request, get_current_school


class TenantManager(models.Manager):
    """
    Auto-scopes by current school (thread-local). Works when the model has either:
      - FK named `school`, or
      - class attr/manager arg `related_school_field` with dotted path, e.g. "class_section__grade__school".
    Unscoped operations are superadmin-only.

    Methods:
      - for_user(user): scoped/unscoped by user.is_superuser/is_superadmin
      - all_for_user(user): unscoped, raises PermissionError if not superadmin
      - get_all()/filter_all(): unscoped, raises PermissionError if not superadmin
      - for_school(school): explicit scoping by a provided school instance
      - filter_for_user(): convenience wrapper using the current request user
    """

    use_in_migrations = True

    def __init__(
        self,
        related_school_field: Optional[str] = None,
        school_field: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__()
        # allow either kw; do not forward unknown kwargs to base Manager
        self.related_school_field = related_school_field or school_field

    # -------- request/scope helpers --------
    def _in_schema_generation_context(self) -> bool:
        """Skip filtering during schema generation to avoid polluting OpenAPI/Swagger."""
        req = get_current_request()
        if req and getattr(req, "is_schema_request", False):
            return True
        if getattr(self, "swagger_fake_view", False):
            return True
        return False

    def _is_superuser(self, user: Optional[object] = None) -> bool:
        req_user = None
        if user is not None:
            req_user = user
        else:
            req = get_current_request()
            req_user = getattr(req, "user", None) if req else None
        return bool(
            req_user
            and (
                getattr(req_user, "is_superuser", False)
                or getattr(req_user, "is_superadmin", False)
            )
        )

    def _assert_superadmin(self, user: Optional[object] = None) -> None:
        if not self._is_superuser(user):
            raise PermissionError(
                "Unscoped access is restricted to superadmin.")

    def _school_field_name(self) -> str:
        # Manager arg wins, then model attr, then default "school"
        return (
            getattr(self.model.objects, "related_school_field", None)
            or getattr(self.model, "related_school_field", None)
            or self.related_school_field
            or "school"
        )

    def _validate_school_field(self, field: str) -> None:
        """
        Validate the 1st hop of the dotted path exists; raise AttributeError on invalid config.
        Why: keeps failures explicit and matches test expectations.
        """
        first_hop = field.split("__", 1)[0]
        try:
            self.model._meta.get_field(first_hop)
        except FieldDoesNotExist as e:
            raise AttributeError(
                f"TenantManager._validate_school_field(): Invalid school field '{field}' "
                f"for model {self.model.__name__}. Set related_school_field correctly "
                f"(e.g. 'school' or 'class_section__grade__school')."
            ) from e

    # -------- writes --------
    def create(self, **kwargs: Any):
        """
        Auto-attach school from thread-local if model has a 'school' FK and caller didn't set it.
        Why: avoids brittle tests where thread-local is set but caller forgot to pass school.
        """
        if "school" not in kwargs and hasattr(self.model, "school"):
            school = get_current_school()
            if school is not None:
                kwargs["school"] = school
        obj = self.model(**kwargs)
        using = getattr(self, "db", None)
        try:
            obj.save(using=using)
        except Exception:
            obj = super().create(**kwargs)
        return obj

    # -------- reads (default scoping) --------
    def get_queryset(self):
        if self._in_schema_generation_context():
            return super().get_queryset()

        qs = super().get_queryset()

        # Superusers bypass scoping
        if self._is_superuser():
            return qs

        field = self._school_field_name()
        self._validate_school_field(field)

        school = get_current_school()
        if school is None:
            return qs.none()

        try:
            try:
                if hasattr(self.model, "is_active"):
                    return qs.filter(Q(**{field: school, "is_active": True}))
                return qs.filter(Q(**{field: school}))
            except Exception as e:
                return qs.filter(Q(**{field: school}))
        except Exception as e:
            # Normalize lookup issues to AttributeError (consistent with tests)
            print("TenantManager.get_queryset() Error: ", str(e))
            raise AttributeError(
                f"TenantManager.get_queryset(): Invalid school field '{field}' for model {self.model.__name__}"
            ) from e

    # -------- explicit scoping APIs --------
    def for_user(self, user):
        """Return scoped queryset for the given user (unscoped if superadmin)."""
        if self._in_schema_generation_context():
            return super().get_queryset()

        qs = super().get_queryset()

        if self._is_superuser(user):
            return qs

        field = self._school_field_name()
        self._validate_school_field(field)

        school = get_current_school()
        if school is None:
            return qs.none()
        return qs.filter(Q(**{field: school}))

    def all_for_user(self, user):
        """Unscoped queryset for the given user; PermissionError if not superadmin."""
        self._assert_superadmin(user)
        return super().all()

    # -------- superadmin escape hatches --------
    def get_all(self):
        self._assert_superadmin()
        return super().get_queryset()

    def filter_all(self, *args, **kwargs):
        self._assert_superadmin()
        return super().get_queryset().filter(*args, **kwargs)

    # -------- convenience helpers --------
    def for_school(self, school):
        """Explicit scoping by a provided school instance."""
        field = self._school_field_name()
        self._validate_school_field(field)
        return super().get_queryset().filter(Q(**{field: school}))

    # -------- convenience helpers --------
    def my_school(self):
        """Explicit scoping by a provided school instance."""
        field = self._school_field_name()
        self._validate_school_field(field)
        return super().get_queryset().filter(Q(**{field: get_current_school()}))

    def filter_for_user(self):
        """
        Get objects for the current request user.
        Superusers get unscoped; others get current-school scoped; no user → none().
        """
        req = get_current_request()
        user = getattr(req, "user", None) if req else None
        if not user:
            return self.get_queryset().none()
        if self._is_superuser(user):
            return self.get_all()
        # Prefer thread-local school; if absent, fall back to user-attached school if present
        school = get_current_school() or getattr(user, "school", None)
        if school is None:
            # Try staff/student profile conventions
            school = getattr(getattr(user, "staff_profile", None), "school", None) or getattr(
                getattr(user, "student_profile", None), "school", None
            )
        if school is None:
            return self.get_queryset().none()
        return self.for_school(school)

    def filter_active(self):
        """Filter active records when model has `is_active`; otherwise return all (non-breaking)."""
        qs = self.get_queryset()
        if "is_active" not in [f.name for f in self.model._meta.fields]:
            return qs
        return qs.filter(is_active=True)
