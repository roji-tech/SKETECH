from __future__ import annotations
from main.tenancy.threadlocals import get_current_school

def tenancy(request):
    """Template context: expose the current school for headers/navs."""
    return {"current_school": get_current_school()}
