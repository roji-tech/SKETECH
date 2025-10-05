# ==============================================
# File: main/apps.py (snippet)
# Purpose: Ensure audit signal receivers are registered
# ==============================================
from __future__ import annotations
from django.apps import AppConfig


class MainConfig(AppConfig):
    name = "main"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Import signal handlers
        from main.tenancy import signals  # noqa: F401

    # def ready(self):
    #     import main.signals
