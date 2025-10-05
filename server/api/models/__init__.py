from django.conf import settings
from django.db import models
from django.utils.timezone import now
from datetime import timedelta


class RefreshTokenUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    refresh_token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def cleanup_expired_tokens(time_range_seconds):
        """
        Delete all RefreshTokenUsage entries older than time_range_seconds * 2.
        """
        expiration_threshold = now() - timedelta(seconds=time_range_seconds * 2)
        expired_tokens = RefreshTokenUsage.objects.filter(
            created_at__lt=expiration_threshold)
        deleted_count, _ = expired_tokens.delete()
        return deleted_count

    @staticmethod
    def get_valid_token(user, time_range_seconds):
        """
        Check if there's a valid token for the user within the time range.
        Returns the valid token if available, otherwise None.
        """
        time_threshold = now() - timedelta(seconds=time_range_seconds)
        token_entry = RefreshTokenUsage.objects.filter(
            user=user,
            created_at__gte=time_threshold
        ).order_by('-created_at').first()

        if token_entry:
            return token_entry.refresh_token

        RefreshTokenUsage.cleanup_expired_tokens(time_range_seconds)
        return None
