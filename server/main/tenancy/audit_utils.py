"""
Utility functions for audit logging.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from main.models import AuditLog
import logging
from typing import Optional
from django.db import models
from main.tenancy.threadlocals import get_current_request, get_current_school
from django.utils.translation import gettext_lazy as _


def log_action(user, action, model_name, object_id=None, changes=None, ip_address=None, school=None):
    """
    Log an action to the audit log.

    Args:
        user: The user performing the action
        action: The action being performed (create, update, delete, etc.)
        model_name: Name of the model being acted upon
        object_id: ID of the object being acted upon
        changes: Dictionary of changes made
        ip_address: IP address of the request
        school: School associated with the action
    """
    # If school is not provided but user is associated with a school, use that
    if school is None and hasattr(user, 'school'):
        school = user.school

    # Create the audit log entry
    AuditLog.objects.create(
        user=user,
        school=school,
        action=action,
        model=model_name,
        object_id=str(object_id) if object_id is not None else None,
        changes=changes or {},
        ip_address=ip_address
    )


# Configure logger
audit_logger = logging.getLogger('audit')

# Fields to exclude from audit logging
EXCLUDED_FIELDS = {"updated_at", "created_at"}


def log_action(
    action: str,
    instance: Optional[models.Model] = None,
    changes: Optional[dict] = None,
    user=None,
    request=None,
    **extra
) -> AuditLog:
    """
    Create an audit log entry.

    Args:
        action: Action performed (create, update, delete, etc.)
        instance: The model instance being acted upon
        changes: Dictionary of changes (for updates)
        user: The user performing the action
        request: The current request object (for IP, user agent, etc.)
        **extra: Additional data to store in the extra field
    """
    if request is None:
        request = get_current_request()

    if user is None and request and hasattr(request, 'user'):
        user = request.user if request.user.is_authenticated else None

    model_name = instance.__class__.__name__ if instance else None
    object_id = str(instance.pk) if instance and hasattr(
        instance, 'pk') else None

    # Get school from instance, request, or current thread
    school = None
    if instance and hasattr(instance, 'school'):
        school = instance.school
    elif hasattr(request, 'school'):
        school = request.school
    else:
        school = get_current_school()

    # Get request info if available
    ip_address = None
    user_agent = ""
    request_path = ""
    request_method = ""

    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        user_agent = request.META.get('HTTP_USER_AGENT', '')
        request_path = getattr(request, 'path', '')
        request_method = getattr(request, 'method', '')

    # Create the audit log entry
    log_entry = AuditLog.objects.create(
        user=user,
        school=school,
        ip_address=ip_address,
        user_agent=user_agent,
        request_path=request_path,
        request_method=request_method,
        action=action,
        model=model_name,
        object_id=object_id,
        changes=changes or {},
        extra=extra,
        content_object=instance
    )

    return log_entry


def get_client_ip(request):
    """ Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def track_model_changes(model, fields_to_track=None):
    """
    Decorator to track changes to model fields.

    Args:
        model: The model class to track
        fields_to_track: List of field names to track (None to track all)
    """
    def wrapper(cls):
        # Connect to the post_save signal
        @receiver(post_save, sender=model)
        def model_post_save(sender, instance, created, **kwargs):
            if created:
                action = AuditLog.ACTION_CREATE
                changes = {}
            else:
                action = AuditLog.ACTION_UPDATE
                changes = get_changes(instance, fields_to_track)

            log_action(
                user=getattr(instance, 'updated_by', None) or getattr(
                    instance, 'created_by', None),
                action=action,
                model_name=f"{instance._meta.app_label}.{instance._meta.model_name}",
                object_id=instance.pk,
                changes=changes,
                school=getattr(instance, 'school', None)
            )

        # Connect to the post_delete signal
        @receiver(post_delete, sender=model)
        def model_post_delete(sender, instance, **kwargs):
            log_action(
                user=getattr(instance, 'updated_by', None) or getattr(
                    instance, 'created_by', None),
                action=AuditLog.ACTION_DELETE,
                model_name=f"{instance._meta.app_label}.{instance._meta.model_name}",
                object_id=instance.pk,
                school=getattr(instance, 'school', None)
            )

        return cls
    return wrapper


def get_changes(instance, fields_to_track=None):
    """
    Get the changes made to a model instance.

    Args:
        instance: The model instance
        fields_to_track: List of field names to track (None to track all)
    """
    if not instance.pk:
        return {}

    # Get the current state from the database
    old_instance = instance.__class__.objects.get(pk=instance.pk)

    changes = {}
    for field in instance._meta.fields:
        field_name = field.name

        # Skip fields we don't want to track
        if fields_to_track is not None and field_name not in fields_to_track:
            continue

        # Skip private fields
        if field_name.startswith('_'):
            continue

        # Get the old and new values
        old_value = getattr(old_instance, field_name, None)
        new_value = getattr(instance, field_name, None)

        # Convert to string for comparison
        if hasattr(old_value, 'pk'):
            old_value = old_value.pk
        if hasattr(new_value, 'pk'):
            new_value = new_value.pk

        # If the value has changed, add it to the changes dictionary
        if old_value != new_value:
            changes[field_name] = {
                'old': old_value,
                'new': new_value
            }

    return changes


# Request logging middleware
class AuditMiddleware:
    """Middleware to log HTTP requests."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip static/media files
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        # Process the request
        response = self.get_response(request)

        # Log the request
        try:
            user = request.user if hasattr(
                request, 'user') and request.user.is_authenticated else None

            log_action(
                action='request',
                user=user,
                request=request,
                status_code=response.status_code,
                success=200 <= response.status_code < 400,
                content_type=response.get('Content-Type', '')
            )
        except Exception as e:
            audit_logger.error(
                f"Failed to log request: {str(e)}", exc_info=True)

        return response
