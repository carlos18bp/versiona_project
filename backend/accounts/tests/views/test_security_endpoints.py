"""A3 security endpoints: 2FA lifecycle + session revocation through the API."""

import pyotp
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts import twofactor


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email='segura@versiona.test', password='secreta123'
    )


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def enabled_user(user):
    setup = twofactor.setup(user)
    code = pyotp.TOTP(setup['secret']).now()
    backup_codes = twofactor.enable(user, code)
    user.refresh_from_db()
    return user, setup['secret'], backup_codes


@pytest.mark.django_db
@pytest.mark.escenario('A3-C01')
def test_setup_endpoint_returns_enrolment_material(auth_client, user):
    response = auth_client.post('/api/me/2fa/setup/')

    assert response.status_code == 200
    assert response.data['qr'].startswith('data:image/png;base64,')
    user.refresh_from_db()
    assert user.totp_secret == response.data['secret']


@pytest.mark.django_db
@pytest.mark.escenario('A3-C02')
def test_setup_endpoint_conflicts_when_2fa_already_active(auth_client, enabled_user):
    response = auth_client.post('/api/me/2fa/setup/')

    assert response.status_code == 409
    assert response.data['error'] == 'El 2FA ya está activo. Desactívalo antes de re-enrolar.'


@pytest.mark.django_db
@pytest.mark.escenario('A3-C03')
def test_enable_endpoint_returns_backup_codes(auth_client, user):
    secret = twofactor.setup(user)['secret']

    response = auth_client.post(
        '/api/me/2fa/enable/', {'code': pyotp.TOTP(secret).now()}, format='json'
    )

    assert response.status_code == 201
    assert len(response.data['backup_codes']) == twofactor.BACKUP_CODE_COUNT


@pytest.mark.django_db
@pytest.mark.escenario('A3-C04')
def test_enable_endpoint_rejects_a_wrong_code(auth_client, user):
    twofactor.setup(user)

    response = auth_client.post('/api/me/2fa/enable/', {'code': '000000'}, format='json')

    assert response.status_code == 400
    assert response.data['error'] == 'Código incorrecto. Verifica la hora de tu dispositivo.'


@pytest.mark.django_db
@pytest.mark.escenario('A3-C05')
def test_disable_endpoint_turns_2fa_off(auth_client, enabled_user):
    user, secret, _ = enabled_user

    response = auth_client.post(
        '/api/me/2fa/disable/', {'code': pyotp.TOTP(secret).now()}, format='json'
    )

    assert response.status_code == 200
    assert response.data == {'totp_enabled': False}
    user.refresh_from_db()
    assert user.totp_enabled_at is None


@pytest.mark.django_db
@pytest.mark.escenario('A3-C06')
def test_disable_endpoint_rejects_a_wrong_code(auth_client, enabled_user):
    response = auth_client.post('/api/me/2fa/disable/', {'code': '000000'}, format='json')

    assert response.status_code == 400
    assert response.data['error'] == 'Código incorrecto.'


@pytest.mark.django_db
@pytest.mark.escenario('A3-C07')
def test_session_revoke_endpoint_blacklists_the_session(auth_client, user):
    RefreshToken.for_user(user)
    session_id = twofactor.list_sessions(user)[0]['id']

    response = auth_client.post(f'/api/me/sessions/{session_id}/revoke/')

    assert response.status_code == 200
    assert response.data == {'revoked': session_id}
    assert twofactor.list_sessions(user) == []


@pytest.mark.django_db
@pytest.mark.escenario('A3-C08')
def test_session_revoke_endpoint_returns_404_for_unknown_session(auth_client):
    response = auth_client.post('/api/me/sessions/999999/revoke/')

    assert response.status_code == 404
    assert response.data['error'] == 'Sesión no encontrada.'


@pytest.mark.django_db
@pytest.mark.escenario('A3-C09')
def test_revoke_others_endpoint_keeps_only_the_given_refresh(auth_client, user):
    keep = RefreshToken.for_user(user)
    RefreshToken.for_user(user)
    RefreshToken.for_user(user)

    response = auth_client.post(
        '/api/me/sessions/revoke_others/', {'refresh': str(keep)}, format='json'
    )

    assert response.status_code == 200
    assert response.data == {'revoked': 2}
    assert len(twofactor.list_sessions(user)) == 1
