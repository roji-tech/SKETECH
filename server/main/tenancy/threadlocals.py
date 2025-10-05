# ==============================================
# File: main/tenancy/threadlocals.py
# Purpose: Single source of truth for per-request context
# ==============================================
from __future__ import annotations
import threading

_thread_locals = threading.local()


def set_current_request(request) -> None:
    """Store the current HttpRequest in thread‑local storage.
    Why: allows managers and utilities to resolve the current school without passing request around.
    """
    _thread_locals.request = request


def get_current_request():
    """Return the current HttpRequest or None."""
    return getattr(_thread_locals, "request", None)


def set_current_school(school_id: int | str, request=None) -> None:
    """Store the resolved School instance for non-HTTP contexts (signals, tasks)."""
    _thread_locals.school_id = school_id
    req = request or get_current_request()
    if req is not None:
        setattr(req, "school_id", school_id)


def get_current_school():
    """Return the current School from the request (preferred) or thread‑local fallback."""
    from django.apps import apps

    # Return None if apps aren't ready yet
    if not apps.ready:
        return None

    try:
        School = apps.get_model("main.School")
    except (LookupError, ImportError):
        return None

    sch = None
    req = get_current_request()
    # Try to get school from request first
    if req is not None and hasattr(req, "school_id"):
        try:
            sch = School.objects.filter(id=req.school_id).first()
        except (TypeError, ValueError):
            pass

    # Fall back to thread-local storage
    if hasattr(_thread_locals, 'school_id') and _thread_locals.school_id:
        try:
            sch = School.objects.filter(id=_thread_locals.school_id).first()
        except (TypeError, ValueError):
            pass

    if sch:
        # print(sch, type(sch))
        return sch

    return None
