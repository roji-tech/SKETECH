# ==============================================
# File: main/common/managers.py
# Purpose: Unified tenant‑scoped queryset & manager
# ==============================================
from __future__ import annotations
from typing import Optional
from django.db import models
from main.tenancy.threadlocals import get_current_school


class SchoolAwareQuerySet(models.QuerySet):
    """QuerySet helpers for tenant scoping."""

    def for_school(self, school) -> "SchoolAwareQuerySet":
        return self.filter(school=school)

    def for_current_school(self) -> "SchoolAwareQuerySet":
        school = get_current_school()
        return self.filter(school=school) if school else self.none()


class TenantScopedManager(models.Manager.from_queryset(SchoolAwareQuerySet)):
    """Default manager that auto‑filters by the current school.

    If the model doesn’t have a direct `school` FK, set `related_school_field` to a
    dotted path (e.g., 'school_class__academic_session__school').
    """

    def __init__(self, *args, related_school_field: Optional[str] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.related_school_field = related_school_field

    def get_queryset(self):
        qs = super().get_queryset()
        school = get_current_school()
        if not school:
            return qs.none()
        field = self.related_school_field or "school"
        return qs.filter(**{field: school})

    # Escape hatch for admin tasks
    def all_tenants(self):
        return super().get_queryset()

