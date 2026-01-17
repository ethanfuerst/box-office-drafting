"""Tests for ETL orchestration."""

from unittest.mock import patch

from tests.conftest import make_config_dict


def test_load_dashboard_data_calls_run_dashboard():
    """load_dashboard_data calls run_dashboard with config."""
    config = make_config_dict(update_type='s3')

    with patch('src.etl.run_dashboard') as mock_run_dashboard:
        from src.etl import load_dashboard_data

        load_dashboard_data(config)

    mock_run_dashboard.assert_called_once_with(config)
