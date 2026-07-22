"""Tests for operational Celery tasks: scheduled_backup, silk_garbage_collection,
weekly_slow_queries_report, silk_reports_cleanup, purge_trashed."""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from freezegun import freeze_time


class _FakeQS(list):
    """List subclass with a no-arg .count() to mimic a sliced Django queryset."""

    def count(self):
        return len(self)


def _setup_silk_mocks(mock_request_cls, mock_sql_query_cls, *, slow_queries, n_plus_one):
    slow_qs = _FakeQS(slow_queries)
    n1_qs = _FakeQS(n_plus_one)
    (
        mock_sql_query_cls.objects
        .filter.return_value
        .select_related.return_value
        .order_by.return_value
        .__getitem__
    ) = MagicMock(return_value=slow_qs)
    (
        mock_request_cls.objects
        .filter.return_value
        .annotate.return_value
        .filter.return_value
        .order_by.return_value
        .__getitem__
    ) = MagicMock(return_value=n1_qs)


# ---------------------------------------------------------------------------
# scheduled_backup
# ---------------------------------------------------------------------------

def test_scheduled_backup_runs_db_and_media_backups():
    """scheduled_backup calls dbbackup then mediabackup with --compress --clean and returns True."""
    from versiona_project.tasks import scheduled_backup

    with patch('django.core.management.call_command') as mock_call_command:
        result = scheduled_backup()

    assert result is True
    assert mock_call_command.call_count == 2
    first_call, second_call = mock_call_command.call_args_list
    assert first_call.args == ('dbbackup', '--compress', '--clean')
    assert second_call.args == ('mediabackup', '--compress', '--clean')


def test_scheduled_backup_reraises_when_a_backup_command_fails():
    """scheduled_backup propagates the exception raised by a failing backup command."""
    from versiona_project.tasks import scheduled_backup

    with patch('django.core.management.call_command', side_effect=RuntimeError('disco lleno')):
        with pytest.raises(RuntimeError):
            scheduled_backup()


# ---------------------------------------------------------------------------
# silk_garbage_collection
# ---------------------------------------------------------------------------

def test_silk_garbage_collection_skips_when_silk_disabled(settings):
    """silk_garbage_collection returns early without calling call_command when ENABLE_SILK is False."""
    settings.ENABLE_SILK = False
    from versiona_project.tasks import silk_garbage_collection

    with patch('django.core.management.call_command') as mock_call_command:
        silk_garbage_collection()

    assert mock_call_command.call_count == 0


def test_silk_garbage_collection_calls_command_with_seven_days(settings):
    """silk_garbage_collection calls silk_garbage_collect with --days=7 when ENABLE_SILK is True."""
    settings.ENABLE_SILK = True
    from versiona_project.tasks import silk_garbage_collection

    with patch('django.core.management.call_command') as mock_call_command:
        silk_garbage_collection()

    mock_call_command.assert_called_once()
    args, kwargs = mock_call_command.call_args
    assert args[0] == 'silk_garbage_collect'
    assert '--days=7' in args
    assert 'stdout' in kwargs


# ---------------------------------------------------------------------------
# weekly_slow_queries_report
# ---------------------------------------------------------------------------

def test_weekly_slow_queries_report_skips_when_silk_disabled(settings, tmp_path):
    """weekly_slow_queries_report returns early without writing a log when ENABLE_SILK is False."""
    settings.ENABLE_SILK = False
    settings.BASE_DIR = tmp_path
    from versiona_project.tasks import weekly_slow_queries_report

    weekly_slow_queries_report()

    assert not (tmp_path / 'logs' / 'silk-weekly-report.log').exists()


@freeze_time('2025-06-09')
def test_weekly_slow_queries_report_creates_log_file(settings, tmp_path):
    """weekly_slow_queries_report creates the log file under BASE_DIR/logs/ when ENABLE_SILK is True."""
    settings.ENABLE_SILK = True
    settings.SLOW_QUERY_THRESHOLD_MS = 500
    settings.N_PLUS_ONE_THRESHOLD = 10
    settings.BASE_DIR = tmp_path

    with (
        patch('silk.models.Request') as mock_request_cls,
        patch('silk.models.SQLQuery') as mock_sql_query_cls,
    ):
        _setup_silk_mocks(mock_request_cls, mock_sql_query_cls, slow_queries=[], n_plus_one=[])
        from versiona_project.tasks import weekly_slow_queries_report
        weekly_slow_queries_report()

    assert (tmp_path / 'logs' / 'silk-reports' / 'silk-report-2025-06-09.log').exists()


@freeze_time('2025-06-09')
def test_weekly_slow_queries_report_log_contains_header(settings, tmp_path):
    """The generated log file contains the WEEKLY QUERY REPORT header."""
    settings.ENABLE_SILK = True
    settings.SLOW_QUERY_THRESHOLD_MS = 500
    settings.N_PLUS_ONE_THRESHOLD = 10
    settings.BASE_DIR = tmp_path

    with (
        patch('silk.models.Request') as mock_request_cls,
        patch('silk.models.SQLQuery') as mock_sql_query_cls,
    ):
        _setup_silk_mocks(mock_request_cls, mock_sql_query_cls, slow_queries=[], n_plus_one=[])
        from versiona_project.tasks import weekly_slow_queries_report
        weekly_slow_queries_report()

    content = (tmp_path / 'logs' / 'silk-reports' / 'silk-report-2025-06-09.log').read_text()
    assert 'WEEKLY QUERY REPORT' in content


@freeze_time('2025-06-09')
def test_weekly_slow_queries_report_no_slow_queries_message(settings, tmp_path):
    """Report contains the 'No slow queries found' message when there are no slow queries."""
    settings.ENABLE_SILK = True
    settings.SLOW_QUERY_THRESHOLD_MS = 500
    settings.N_PLUS_ONE_THRESHOLD = 10
    settings.BASE_DIR = tmp_path

    with (
        patch('silk.models.Request') as mock_request_cls,
        patch('silk.models.SQLQuery') as mock_sql_query_cls,
    ):
        _setup_silk_mocks(mock_request_cls, mock_sql_query_cls, slow_queries=[], n_plus_one=[])
        from versiona_project.tasks import weekly_slow_queries_report
        weekly_slow_queries_report()

    content = (tmp_path / 'logs' / 'silk-reports' / 'silk-report-2025-06-09.log').read_text()
    assert 'No slow queries found this week' in content


@freeze_time('2025-06-09')
def test_weekly_slow_queries_report_no_n_plus_one_message(settings, tmp_path):
    """Report contains the 'No N+1 patterns detected' message when there are no N+1 suspects."""
    settings.ENABLE_SILK = True
    settings.SLOW_QUERY_THRESHOLD_MS = 500
    settings.N_PLUS_ONE_THRESHOLD = 10
    settings.BASE_DIR = tmp_path

    with (
        patch('silk.models.Request') as mock_request_cls,
        patch('silk.models.SQLQuery') as mock_sql_query_cls,
    ):
        _setup_silk_mocks(mock_request_cls, mock_sql_query_cls, slow_queries=[], n_plus_one=[])
        from versiona_project.tasks import weekly_slow_queries_report
        weekly_slow_queries_report()

    content = (tmp_path / 'logs' / 'silk-reports' / 'silk-report-2025-06-09.log').read_text()
    assert 'No N+1 patterns detected this week' in content


@freeze_time('2025-06-09')
def test_weekly_slow_queries_report_includes_slow_query_data(settings, tmp_path):
    """Report includes the endpoint path and duration of each detected slow query."""
    settings.ENABLE_SILK = True
    settings.SLOW_QUERY_THRESHOLD_MS = 500
    settings.N_PLUS_ONE_THRESHOLD = 10
    settings.BASE_DIR = tmp_path

    slow_query = SimpleNamespace(
        time_taken=1200.0,
        request=SimpleNamespace(path='/api/products/'),
        query='SELECT * FROM product WHERE id = 1',
    )

    with (
        patch('silk.models.Request') as mock_request_cls,
        patch('silk.models.SQLQuery') as mock_sql_query_cls,
    ):
        _setup_silk_mocks(
            mock_request_cls,
            mock_sql_query_cls,
            slow_queries=[slow_query],
            n_plus_one=[],
        )
        from versiona_project.tasks import weekly_slow_queries_report
        weekly_slow_queries_report()

    content = (tmp_path / 'logs' / 'silk-reports' / 'silk-report-2025-06-09.log').read_text()
    assert '/api/products/' in content
    assert '1200ms' in content


@freeze_time('2025-06-09')
def test_weekly_slow_queries_report_includes_n_plus_one_suspects(settings, tmp_path):
    """Report includes the endpoint path and query count of each detected N+1 suspect."""
    settings.ENABLE_SILK = True
    settings.SLOW_QUERY_THRESHOLD_MS = 500
    settings.N_PLUS_ONE_THRESHOLD = 10
    settings.BASE_DIR = tmp_path

    suspect = SimpleNamespace(query_count=25, path='/api/sales/')

    with (
        patch('silk.models.Request') as mock_request_cls,
        patch('silk.models.SQLQuery') as mock_sql_query_cls,
    ):
        _setup_silk_mocks(
            mock_request_cls,
            mock_sql_query_cls,
            slow_queries=[],
            n_plus_one=[suspect],
        )
        from versiona_project.tasks import weekly_slow_queries_report
        weekly_slow_queries_report()

    content = (tmp_path / 'logs' / 'silk-reports' / 'silk-report-2025-06-09.log').read_text()
    assert '/api/sales/' in content
    assert '25 queries' in content


def test_weekly_slow_queries_report_skips_when_silk_import_fails(settings, tmp_path):
    """weekly_slow_queries_report returns early without a report when silk cannot be imported."""
    settings.ENABLE_SILK = True
    settings.BASE_DIR = tmp_path
    from versiona_project.tasks import weekly_slow_queries_report

    with patch.dict(sys.modules, {'silk.models': None}):
        result = weekly_slow_queries_report()

    assert result is None
    assert not (tmp_path / 'logs' / 'silk-reports').exists()


# ---------------------------------------------------------------------------
# silk_reports_cleanup
# ---------------------------------------------------------------------------

def _reports_dir(base_dir):
    path = base_dir / 'logs' / 'silk-reports'
    path.mkdir(parents=True)
    return path


def test_silk_reports_cleanup_skips_when_silk_disabled(settings, tmp_path):
    """silk_reports_cleanup leaves every report untouched when ENABLE_SILK is False."""
    settings.ENABLE_SILK = False
    settings.BASE_DIR = tmp_path
    old_report = _reports_dir(tmp_path) / 'silk-report-2020-01-01.log'
    old_report.write_text('viejo')
    from versiona_project.tasks import silk_reports_cleanup

    silk_reports_cleanup()

    assert old_report.exists()


def test_silk_reports_cleanup_returns_when_reports_dir_is_missing(settings, tmp_path):
    """silk_reports_cleanup exits without creating anything when the reports dir does not exist."""
    settings.ENABLE_SILK = True
    settings.BASE_DIR = tmp_path
    from versiona_project.tasks import silk_reports_cleanup

    silk_reports_cleanup()

    assert not (tmp_path / 'logs' / 'silk-reports').exists()


@freeze_time('2025-06-09')
def test_silk_reports_cleanup_deletes_reports_older_than_six_months(settings, tmp_path):
    """silk_reports_cleanup deletes report files dated before the 180-day cutoff."""
    settings.ENABLE_SILK = True
    settings.BASE_DIR = tmp_path
    old_report = _reports_dir(tmp_path) / 'silk-report-2024-11-01.log'
    old_report.write_text('viejo')
    from versiona_project.tasks import silk_reports_cleanup

    silk_reports_cleanup()

    assert not old_report.exists()


@freeze_time('2025-06-09')
def test_silk_reports_cleanup_keeps_recent_reports(settings, tmp_path):
    """silk_reports_cleanup keeps report files dated within the 180-day window."""
    settings.ENABLE_SILK = True
    settings.BASE_DIR = tmp_path
    recent_report = _reports_dir(tmp_path) / 'silk-report-2025-06-01.log'
    recent_report.write_text('reciente')
    from versiona_project.tasks import silk_reports_cleanup

    silk_reports_cleanup()

    assert recent_report.exists()


@freeze_time('2025-06-09')
def test_silk_reports_cleanup_ignores_files_with_unparseable_dates(settings, tmp_path):
    """silk_reports_cleanup skips files whose name does not carry a YYYY-MM-DD date."""
    settings.ENABLE_SILK = True
    settings.BASE_DIR = tmp_path
    odd_report = _reports_dir(tmp_path) / 'silk-report-legacy.log'
    odd_report.write_text('sin fecha')
    from versiona_project.tasks import silk_reports_cleanup

    silk_reports_cleanup()

    assert odd_report.exists()


# ---------------------------------------------------------------------------
# purge_trashed
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_purge_trashed_returns_zero_counts_on_a_clean_database():
    """purge_trashed reports zero purged rows when nothing is in the trash."""
    from versiona_project.tasks import purge_trashed

    result = purge_trashed()

    assert result == {'versions': 0, 'documents': 0, 'projects': 0}
