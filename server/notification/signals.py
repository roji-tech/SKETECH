from django.db.models.signals import post_save, post_delete
from django.conf import settings
from django.dispatch import receiver, Signal
from django.contrib.auth import get_user_model



from .models import Notification
from main.models import Staff

User = get_user_model()


@receiver(post_save, sender=Staff)
def notify_teacher_creation(sender, instance, created, **kwargs):
    if created:
        # Create a notification when a new teacher is added
        Notification.objects.create(
            title="New teacher added",
            message=f"Teacher {instance.full_name} has been added to the system.",
            user=instance.user
        )
