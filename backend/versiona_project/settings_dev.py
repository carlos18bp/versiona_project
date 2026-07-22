"""
Development settings for versiona_project.

Usage: DJANGO_SETTINGS_MODULE=versiona_project.settings_dev

Note: The default DJANGO_SETTINGS_MODULE in manage.py points to
versiona_project.settings (base). Use this file explicitly when you want
development-specific overrides (DEBUG=True, permissive hosts).

Database and email come from the base settings + .env: native PostgreSQL
(versiona) and mailpit as the SMTP catcher (docs/plan/07 §2.1 — no Docker).
"""

from .settings import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']
