from main.models import Staff
from notification.models import Notification
from main.finance.utils import ensure_default_transaction_types, seed_defaults_for_all_schools
from django.conf import settings
from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, post_migrate

# New user has registered. Args: user, request.
user_registered = Signal()

# User has activated his or her account. Args: user, request.
user_activated = Signal()

# User has been updated. Args: user, request.
user_updated = Signal()


@receiver(post_save, sender=Staff)
def notify_staff_creation(sender, instance, created, **kwargs):
    if created:
        # Create a notification when a new teacher is added
        Notification.objects.create(
            title="New teacher added",
            message=f"Teacher {instance.full_name} has been added to the system.",
            user=instance.user
        )


AUTO_SEED_ON_SCHOOL_CREATE = getattr(
    settings, "FINANCE_AUTO_SEED_TYPES_ON_SCHOOL_CREATE", True)
AUTO_BACKFILL_ON_MIGRATE = getattr(
    settings, "FINANCE_AUTO_BACKFILL_TYPES_ON_MIGRATE", True)


# app_label.ModelName style avoids import cycle
@receiver(post_save, sender="main.School")
def _seed_txn_types_on_school_create(sender, instance, created, **kwargs):
    if not AUTO_SEED_ON_SCHOOL_CREATE:
        return
    if created:
        ensure_default_transaction_types(instance)


@receiver(post_migrate)
def _backfill_txn_types_after_migrate(sender, app_config, **kwargs):
    """
    Backfill after migrations so existing schools get defaults.
    Guarded by setting to keep CI predictable.
    """
    print("Backfilling transaction types after migration...")
    if not AUTO_BACKFILL_ON_MIGRATE:
        return
    # Only run when our finance app is ready (or always if you prefer)
    if getattr(app_config, "label", None) not in {"main"}:
        return
    try:
        seed_defaults_for_all_schools()
    except Exception:
        # Avoid breaking migrations if something external fails
        pass
