import importlib

import pytest


@pytest.mark.django_db
def test_url_modules_import_and_have_patterns():
    """Verifies each URL sub-module imports successfully and registers the expected named patterns."""
    package_urls = importlib.import_module('accounts.urls')
    assert hasattr(package_urls, 'urlpatterns')

    auth_urls = importlib.import_module('accounts.urls.auth')
    captcha_urls = importlib.import_module('accounts.urls.captcha')

    assert any(pattern.name == 'sign_up' for pattern in auth_urls.urlpatterns)
    assert any(pattern.name == 'captcha-site-key' for pattern in captcha_urls.urlpatterns)


@pytest.mark.django_db
def test_core_urls_expose_staging_banner():
    core_urls = importlib.import_module('core.urls')

    assert any(pattern.name == 'staging-banner' for pattern in core_urls.urlpatterns)
