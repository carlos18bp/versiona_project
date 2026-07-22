"""GET /api/public/plans/ — the AllowAny catalog behind /precios."""

import pytest
from django.core.cache import cache

from billing.views import PublicPlansThrottle


@pytest.fixture(autouse=True)
def _clean_throttle_cache():
    cache.clear()
    yield
    cache.clear()


URL = '/api/public/plans/'


@pytest.mark.django_db
@pytest.mark.escenario('F1-P01')
def test_public_plans_is_open_to_anonymous_visitors(api_client):
    response = api_client.get(URL)

    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.escenario('F1-P01')
def test_public_plans_lists_the_three_plans_in_order(api_client):
    response = api_client.get(URL)

    assert [plan['key'] for plan in response.data['plans']] == [
        'free', 'pro', 'enterprise',
    ]


@pytest.mark.django_db
@pytest.mark.escenario('F1-P01')
def test_public_plans_carries_prices_and_limits(api_client):
    response = api_client.get(URL)

    pro = response.data['plans'][1]
    assert pro['price_cop'] == 149000
    assert pro['limits'] == {
        'max_active_projects': 20, 'max_members': 25, 'history_days': None,
    }


@pytest.mark.django_db
@pytest.mark.escenario('F1-P01')
def test_public_plans_exposes_the_trial_days(api_client, settings):
    settings.BILLING_TRIAL_DAYS = 14

    response = api_client.get(URL)

    assert response.data['trial_days'] == 14


@pytest.mark.django_db
@pytest.mark.escenario('F1-P02')
def test_public_plans_rejects_non_get_methods(api_client):
    response = api_client.post(URL, {}, format='json')

    assert response.status_code == 405


@pytest.mark.django_db
@pytest.mark.escenario('F1-P02')
def test_public_plans_throttles_anonymous_bursts(api_client, monkeypatch):
    monkeypatch.setattr(PublicPlansThrottle, 'rate', '2/min', raising=False)

    api_client.get(URL)
    api_client.get(URL)
    third = api_client.get(URL)

    assert third.status_code == 429
