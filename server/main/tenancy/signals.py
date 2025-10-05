# -------- Signals (pre/post save, post delete) --------
from typing import Any

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db import models
from django.utils.translation import gettext_lazy as _
from .audit_utils import log_action

# Configure logger
import logging
audit_logger = logging.getLogger('audit')

# Fields to exclude from audit logging
EXCLUDED_FIELDS = {"updated_at", "created_at"}


def _in_project(sender) -> bool:
    """Check if the sender is a model from our project."""
    if not hasattr(sender, '_meta'):
        return False
    # Skip audit-related models to prevent recursion
    if sender.__name__ in ['AuditLog', 'AuditEntry']:
        return False
    # Only process models from our main app
    return getattr(sender._meta, "app_label", "").startswith("main")


def _tracked_fields(instance: models.Model) -> list:
    """Get list of fields to track for a model."""
    return [
        f.name for f in instance._meta.fields
        if f.editable and f.name not in EXCLUDED_FIELDS
    ]


def _serialize_instance(instance) -> dict:
    """Convert model instance to a serializable dictionary."""
    if not instance:
        return {}
    return {
        f.name: _make_json_serializable(getattr(instance, f.name, None))
        for f in instance._meta.fields
        if f.editable and f.name not in EXCLUDED_FIELDS
    }


def _make_json_serializable(value: Any) -> Any:
    """Convert non-JSON-serializable values to serializable formats."""
    if value is None or value == '':
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (list, tuple, set)):
        return [_make_json_serializable(item) for item in value]
    if isinstance(value, dict):
        return {k: _make_json_serializable(v) for k, v in value.items()}
    if isinstance(value, models.Model):
        return f"{value.__class__.__name__}(pk={value.pk})"
    if hasattr(value, 'url') and hasattr(value, 'name'):
        try:
            return value.url if value else None
        except ValueError:
            return value.name if hasattr(value, 'name') and value.name else None
    return str(value)


@receiver(pre_save)
def _audit_pre_save(sender, instance, **kwargs):
    """Capture the original state of a model before saving."""
    if not _in_project(sender) or not isinstance(instance, models.Model):
        return

    # Skip if this is an AuditLog model
    if instance.__class__.__name__ == 'AuditLog':
        return

    # For new instances, nothing to capture
    if not hasattr(instance, 'pk') or instance.pk is None:
        instance.__original_state__ = None
        return

    # Capture the original state
    try:
        old = sender.objects.get(pk=instance.pk)
        instance.__original_state__ = _serialize_instance(old)
    except (sender.DoesNotExist, Exception) as e:
        audit_logger.debug(
            f"Could not get original state for {sender.__name__}: {e}")
        instance.__original_state__ = None


@receiver(post_save)
def _audit_post_save(sender, instance, created, **kwargs):
    """Log model creation and updates."""
    if not _in_project(sender) or not isinstance(instance, models.Model):
        return

    # Skip if this is an AuditLog model
    if instance.__class__.__name__ == 'AuditLog':
        return

    action = 'create' if created else 'update'
    changes = {}

    # For updates, calculate changes from original state
    if not created and hasattr(instance, '__original_state__') and instance.__original_state__ is not None:
        current_state = _serialize_instance(instance)
        for field in _tracked_fields(instance):
            old_value = instance.__original_state__.get(field)
            new_value = current_state.get(field)
            if old_value != new_value:
                changes[field] = {'from': old_value, 'to': new_value}

    # Only log if it's a creation or there are changes
    if created or changes:
        log_action(
            action=action,
            instance=instance,
            changes=changes,
            success=True
        )


@receiver(post_delete)
def _audit_post_delete(sender, instance, **kwargs):
    """Log model deletions."""
    if not _in_project(sender) or not isinstance(instance, models.Model):
        return

    # Skip if this is an AuditLog model
    if instance.__class__.__name__ == 'AuditLog':
        return

    log_action(
        action='delete',
        instance=instance,
        changes=_serialize_instance(instance),
        success=True
    )
