from __future__ import annotations
from typing import Optional
import re

SUBDOMAIN_RE = re.compile(r"^(?P<sub>[^.:]+)\.")

def extract_subdomain(host: str, base_domain: Optional[str] = None) -> Optional[str]:
    """
    Extract the first label from host. If base_domain is given (e.g., 'example.com'),
    strip it before extracting. Returns None for naked/base domains.
    """
    if not host:
        return None
    host = host.split(":", 1)[0].strip().lower()
    if base_domain and host.endswith(base_domain.lower()):
        left = host[: -len(base_domain)].rstrip(".")
        return left.split(".")[-1] if left else None
    m = SUBDOMAIN_RE.match(host)
    return m.group("sub") if m else None