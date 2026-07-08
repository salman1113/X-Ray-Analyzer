"""
Multi-tenancy helpers — subdomain slugify, parsing, validation.
"""

from __future__ import annotations

import re
import unicodedata

from core.settings import settings

SUBDOMAIN_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")
MAX_SUBDOMAIN_LEN = 32


def slugify(name: str) -> str:
    """Convert a hospital name to a DNS-safe lowercase slug."""
    if not name or not name.strip():
        return ""

    normalized = unicodedata.normalize("NFKD", name)
    ascii_only = normalized.encode("ascii", "ignore").decode("ascii")
    lowered = ascii_only.lower()
    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered)
    collapsed = re.sub(r"-+", "-", hyphenated).strip("-")
    result = collapsed[:MAX_SUBDOMAIN_LEN].rstrip("-")

    # Final validity check — if truncation left an invalid slug, return empty
    if not result or not SUBDOMAIN_RE.match(result):
        return ""
    return result


def is_valid_subdomain(sub: str) -> bool:
    """Return True iff sub is a syntactically valid DNS label within our limits."""
    if not sub or len(sub) > MAX_SUBDOMAIN_LEN:
        return False
    return bool(SUBDOMAIN_RE.match(sub))


def is_reserved(sub: str) -> bool:
    """Return True iff this subdomain is on the reserved list."""
    return sub.lower() in settings.reserved_subdomains_set


def extract_subdomain(host: str | None) -> str | None:
    """
    Extract the tenant subdomain from a Host header.

    "abc.domain.com:8000"  →  "abc"
    "domain.com"           →  None (apex)
    "www.domain.com"       →  None (reserved)
    """
    if not host:
        return None

    host_only = host.split(":", 1)[0].strip().lower()
    base = settings.BASE_DOMAIN.strip().lower()

    if not host_only or not base:
        return None
    if host_only == base:
        return None

    suffix = f".{base}"
    if not host_only.endswith(suffix):
        return None

    candidate = host_only[: -len(suffix)]
    if not candidate or "." in candidate:
        return None
    if not is_valid_subdomain(candidate):
        return None
    if is_reserved(candidate):
        return None

    return candidate


def build_tenant_url(subdomain: str) -> str:
    """Build the user-facing URL for a tenant. Returns empty string if invalid."""
    if not subdomain or not is_valid_subdomain(subdomain):
        return ""

    scheme = settings.TENANT_URL_SCHEME or "https"
    port = settings.TENANT_URL_PORT.strip()
    host = f"{subdomain}.{settings.BASE_DOMAIN}"
    if port:
        host = f"{host}:{port}"
    return f"{scheme}://{host}"
