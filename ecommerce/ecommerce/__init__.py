from .celery_app import app as celery_app
"""Application package init.

Exposes the Celery app as ``celery_app`` so other modules can do:
	from ecommerce import celery_app
without triggering an early import of Django settings in awkward contexts.

This also helps some deployment platforms & IDEs that expect the conventional
`from project import celery_app` pattern.
"""

from .celery_app import app as celery_app  # noqa: F401

__all__ = ["celery_app"]