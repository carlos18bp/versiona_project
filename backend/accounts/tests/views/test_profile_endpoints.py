"""User profile & preferences endpoint (kit 2/7 — docs/audit/03 SET-*)."""

import pytest


@pytest.mark.django_db
def test_profile_returns_language_and_timezone(authenticated_client):
    response = authenticated_client.get('/api/me/profile/')

    assert response.status_code == 200
    assert response.data['language'] == 'es'
    assert response.data['timezone'] == 'America/Bogota'


@pytest.mark.django_db
def test_profile_updates_language_and_timezone(authenticated_client):
    response = authenticated_client.patch(
        '/api/me/profile/', {'language': 'en', 'timezone': 'Europe/Madrid'}, format='json'
    )

    assert response.status_code == 200
    assert response.data['language'] == 'en'
    assert response.data['timezone'] == 'Europe/Madrid'


@pytest.mark.django_db
def test_profile_rejects_invalid_timezone(authenticated_client):
    response = authenticated_client.patch(
        '/api/me/profile/', {'timezone': 'Marte/Colonia'}, format='json'
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_profile_requires_authentication(api_client):
    response = api_client.get('/api/me/profile/')

    assert response.status_code == 401


@pytest.mark.django_db
def test_profile_email_is_read_only(authenticated_client):
    response = authenticated_client.patch(
        '/api/me/profile/', {'email': 'otro@example.com'}, format='json'
    )

    assert response.status_code == 200
    assert response.data['email'] == 'user@example.com'
