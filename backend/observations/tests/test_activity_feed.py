"""Project activity feed (kit 6): whitelist + privacy + permissions."""

import pytest

from audit import services as audit
from audit.views import ACTIVITY_WHITELIST


@pytest.fixture
def seeded_events(versiona_context):
    context = versiona_context
    audit.record(
        org=context.org, project=context.project, actor=context.users['editor'],
        event_type='version.uploaded', obj=context.project,
        payload={'number': 1},
    )
    audit.record(
        org=context.org, project=context.project, actor=context.users['reviewer'],
        event_type='seal.created', obj=context.project, payload={'version': 1},
    )
    # NOT whitelisted: an internal login event never reaches the feed.
    audit.record(
        org=context.org, project=context.project, actor=context.users['editor'],
        event_type='auth.login', obj=context.project, payload={},
    )
    return context


def feed_url(context):
    return f'/api/projects/{context.project.public_id}/activity/'


@pytest.mark.django_db
@pytest.mark.escenario('ACT-F01')
@pytest.mark.escenario('F3-A01')
def test_feed_lists_whitelisted_events_newest_first(client_as, seeded_events):
    response = client_as('viewer').get(feed_url(seeded_events))

    assert response.status_code == 200
    types = [row['event_type'] for row in response.data['results']]
    assert types == ['seal.created', 'version.uploaded']
    assert 'auth.login' not in types


@pytest.mark.django_db
@pytest.mark.escenario('ACT-F02')
def test_feed_rows_never_expose_ip_or_request_id(client_as, seeded_events):
    response = client_as('viewer').get(feed_url(seeded_events))

    for row in response.data['results']:
        assert set(row) == {'event_type', 'actor_email', 'payload', 'created_at'}


@pytest.mark.django_db
def test_feed_filters_by_event_type(client_as, seeded_events):
    response = client_as('viewer').get(feed_url(seeded_events) + '?type=seal.created')

    assert [row['event_type'] for row in response.data['results']] == ['seal.created']


@pytest.mark.django_db
@pytest.mark.parametrize('actor, expected', [
    pytest.param('viewer', 200, id='act-p01-viewer'),
    pytest.param('anonymous', 401, id='act-p03-anonymous'),
    pytest.param('non_member', 404, id='act-p04-non-member'),
])
@pytest.mark.escenario('F3-A01')
def test_feed_permission_matrix(client_as, seeded_events, actor, expected):
    response = client_as(actor).get(feed_url(seeded_events))

    assert response.status_code == expected


def test_whitelist_covers_the_domain_events_not_the_plumbing():
    assert 'version.uploaded' in ACTIVITY_WHITELIST
    assert 'seal.invalidated' in ACTIVITY_WHITELIST
    assert 'auth.login' not in ACTIVITY_WHITELIST
