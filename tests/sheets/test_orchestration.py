"""Tests for ETL orchestration."""

from unittest.mock import MagicMock, patch

from tests.conftest import make_config_dict


def test_run_dashboard_creates_and_runs_dashboard_runner():
    """run_dashboard creates DashboardRunner and calls run()."""
    config = make_config_dict(update_type='s3')

    mock_runner_instance = MagicMock()
    with patch('src.sheets.runner._load_credentials', return_value={'key': 'value'}):
        with patch('src.sheets.runner.DashboardRunner') as mock_runner_class:
            with patch('src.sheets.runner._log_missing_movies'):
                with patch('src.sheets.runner._log_min_revenue_info'):
                    mock_runner_class.return_value = mock_runner_instance

                    from src.sheets.runner import run_dashboard

                    run_dashboard(config)

    mock_runner_class.assert_called_once()
    mock_runner_instance.run.assert_called_once()
