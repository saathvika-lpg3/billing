"""Authoritative runtime identity for the PRM desktop product.

Database schema revisions, installer upgrade history, and third-party protocol
versions are intentionally separate from this product release identity.
"""

from __future__ import annotations


PRODUCT_NAME = "PRM BILLING INVENTORY"
PRODUCT_VERSION = "1.0.0"
DISPLAY_VERSION = "V1.0"
RELEASE_NAME = f"{PRODUCT_NAME} {DISPLAY_VERSION}"

# Standard Python package-style version export for runtime/build consumers.
__version__ = PRODUCT_VERSION


def runtime_version_record() -> dict[str, str]:
    """Return the canonical dashboard/diagnostic representation."""

    return {
        "component": "Desktop Runtime",
        "version": DISPLAY_VERSION,
        "notes": f"{PRODUCT_NAME} technical version {PRODUCT_VERSION}",
        "updated_at": "",
    }
