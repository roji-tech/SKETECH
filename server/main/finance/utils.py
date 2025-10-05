# ===============================================
# file: main/finance/constants.py
# ===============================================
from __future__ import annotations
from django.utils.text import slugify
from main.finance.utils import ensure_default_transaction_types, seed_defaults_for_all_schools
from django.dispatch import receiver
from django.db.models.signals import post_save, post_migrate
from django.conf import settings
from main.models import TransactionType  # adjust if model path differs
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
from typing import Iterable, Optional

# Canonical codes (internal); keep stable across time
FEE_PAYMENT = "FEE_PAYMENT"
PURCHASE = "PURCHASE"
REFUND = "REFUND"
OTHER = "OTHER"

# (code, label, is_income)
TRANSACTION_TYPES: list[tuple[str, str, bool]] = [
    (FEE_PAYMENT, "Fee Payment", True),
    # money into school (e.g., books, uniforms)
    (PURCHASE, "Purchase", True),
    (REFUND, "Refund", False),         # money out of school
    (OTHER, "Other", True),
]


def canonical_code(code: str) -> str:
    """Stable slug used in DB (lowercase, hyphenated)."""
    return slugify(code)  # e.g. "FEE_PAYMENT" -> "fee-payment"


# ===============================================
# file: main/finance/utils.py
# ===============================================


def ensure_default_transaction_types(school, *, activate: bool = True) -> int:
    """
    Create/update default TransactionType rows for a given school.
    Idempotent: updates name/is_income/active when they drift.
    Returns number of types created.
    """
    created = 0
    now = timezone.now()
    for raw_code, name, is_income in TRANSACTION_TYPES:
        code = canonical_code(raw_code)
        obj, was_created = TransactionType.objects.get_or_create(
            school=school,
            code=code,
            defaults={"name": name, "is_income": is_income, "active": True},
        )
        if was_created:
            created += 1
        else:
            to_update = {}
            if obj.name != name:
                to_update["name"] = name
            if obj.is_income != is_income:
                to_update["is_income"] = is_income
            if activate and not obj.active:
                to_update["active"] = True
            if to_update:
                TransactionType.objects.filter(pk=obj.pk).update(
                    **to_update, updated_at=now)  # type: ignore[arg-type]
    return created


@transaction.atomic
def seed_defaults_for_all_schools(schools: Optional[Iterable] = None) -> dict[int, int]:
    """
    Seed across schools. Returns {school_id: created_count}.
    """
    from main.models import School  # lazy import to avoid circulars
    if schools is None:
        schools = School.objects.all()
    result = {}
    for s in schools:
        result[s.id] = ensure_default_transaction_types(s)
    return result


# # ===============================================
# # file: main/finance/management/commands/seed_txn_types.py
# # ===============================================
# from __future__ import annotations

# from typing import Optional

# from django.core.management.base import BaseCommand, CommandParser, CommandError

# from main.finance.utils import seed_defaults_for_all_schools, ensure_default_transaction_types

# class Command(BaseCommand):
#     help = "Seed default Transaction Types for schools."

#     def add_arguments(self, parser: CommandParser) -> None:
#         parser.add_argument("--school-id", type=int, help="Seed for a specific school id")
#         parser.add_argument("--all", action="store_true", help="Seed for all schools")

#     def handle(self, *args, **options):
#         from main.models import School  # lazy import
#         school_id: Optional[int] = options.get("school_id")
#         all_flag: bool = options.get("all")

#         if not school_id and not all_flag:
#             raise CommandError("Provide --all or --school-id <id>")

#         if school_id:
#             try:
#                 school = School.objects.get(pk=school_id)
#             except School.DoesNotExist:
#                 raise CommandError(f"School id={school_id} not found")
#             created = ensure_default_transaction_types(school)
#             self.stdout.write(self.style.SUCCESS(f"Seeded {created} types for school {school.id}"))
#             return

#         result = seed_defaults_for_all_schools()
#         total = sum(result.values())
#         self.stdout.write(self.style.SUCCESS(f"Seeded defaults for {len(result)} schools (created {total})."))


# # ===============================================
# # OPTIONAL: example data migration
# # file: main/finance/migrations/0002_seed_default_types.py
# # ===============================================
# from django.db import migrations

# def forwards(apps, schema_editor):
#     TransactionType = apps.get_model("main", "TransactionType")
#     School = apps.get_model("main", "School")
#     from django.utils.text import slugify

#     defaults = [
#         ("FEE_PAYMENT", "Fee Payment", True),
#         ("PURCHASE", "Purchase", True),
#         ("REFUND", "Refund", False),
#         ("OTHER", "Other", True),
#     ]
#     for school in School.objects.all():
#         for raw_code, name, is_income in defaults:
#             code = slugify(raw_code)
#             TransactionType.objects.update_or_create(
#                 school=school,
#                 code=code,
#                 defaults={"name": name, "is_income": is_income, "active": True},
#             )
