from __future__ import annotations
from .threadlocals import get_current_request, get_current_school
from django.utils.translation import gettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, post_delete
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from django.db import models
from django.conf import settings

from django.contrib.auth.models import Permission
from main.tenancy.managers import TenantManager


class SchoolOwnedModel(models.Model):
    """
    Mixin to attach the tenant-aware manager to tenant-owned models.
    Set `related_school_field` on subclasses when `school` FK isn't present.
    """
    default_objects = models.Manager()
    objects = TenantManager()

    class Meta:
        abstract = True


class Position(models.Model):
    """
    Per-school position (e.g., Secretary, Bursar). Attaches Django permissions.
    Users can hold multiple positions inside the same school.
    """
    school = models.ForeignKey(
        "main.School", on_delete=models.CASCADE, related_name="positions")
    name = models.CharField(max_length=80)
    permissions = models.ManyToManyField(
        Permission, blank=True, related_name="positions")

    class Meta:
        unique_together = ("school", "name")
        ordering = ["school", "name"]

    def __str__(self):
        return f"{self.name} @ {self.school}"


class PositionAssignment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="position_assignments")
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, related_name="assignments")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name="position_assigned_by")
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "position")
        ordering = ["-assigned_at"]

    def __str__(self):
        return f"{self.user} → {self.position}"


class SchoolAwareModel(SchoolOwnedModel):
    """
    Abstract base class for models that belong to a school.
    Provides common fields and methods for school-based models.
    """
    related_name = 'school_%(class)ss'
    related_school_field = 'school'

    school = models.ForeignKey(
        'main.School',
        on_delete=models.CASCADE,
        related_name=related_name,
        db_index=True,  # Add index on school field
        help_text="The school this item belongs to"
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['school', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __init_subclass__(cls, **kwargs):
        """Ensure all subclasses use a dynamic related_name for the school field."""
        super().__init_subclass__(**kwargs)

        # Only process if this is a direct subclass of SchoolAwareModel
        if SchoolAwareModel in cls.__bases__:
            # Get the actual field object using _meta.get_field()
            school_field = cls._meta.get_field('school')
            # Update the related_name on the remote_field
            school_field.remote_field.related_name = cls.get_related_name()

    @classmethod
    def get_related_name(cls):
        return cls.related_name


class AuditableModel(SchoolOwnedModel):
    """
    Abstract base class for models that need to track who created/updated them.
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_%(class)ss',
        help_text="User who created this record"
    )

    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_%(class)ss',
        help_text="User who last updated this record"
    )

    class Meta:
        abstract = True


class SoftDeleteModel(SchoolOwnedModel):
    """
    Abstract base class for models that support soft delete.
    """
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_%(class)ss',
        help_text="User who deleted this record"
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, deleted_by=None):
        """Soft delete the model instance."""
        from django.utils import timezone
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.save(update_fields=['is_active', 'deleted_at', 'deleted_by'])

    def hard_delete(self, *args, **kwargs):
        """Actually delete the model instance."""
        super().delete(*args, **kwargs)
