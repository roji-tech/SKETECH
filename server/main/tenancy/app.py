from __future__ import annotations
from django.apps import AppConfig

class TenancyConfig(AppConfig):
    name = "main.tenancy"
    verbose_name = "Tenancy / RBAC / Audit"

    def ready(self):
        # Ensure audit signal receivers are registered.
        ...
