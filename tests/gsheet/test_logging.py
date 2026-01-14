import logging
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from tests.conftest import make_config_dict


def test_log_missing_movies_logs_movies_not_in_scoreboard(caplog):
    """Movies drafted but not in scoreboard are logged."""
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.config = make_config_dict(update_type='s3')
    mock_gsheet_dashboard.released_movies_df = pd.DataFrame({
        'Title': ['Movie A', 'Movie B'],
    })

    draft_df = pd.DataFrame({'movie': ['Movie A', 'Movie B', 'Movie C']})

    with patch('src.utils.gsheet.table_to_df', return_value=draft_df):
        with caplog.at_level(logging.INFO):
            from src.utils.gsheet import log_missing_movies

            log_missing_movies(mock_gsheet_dashboard)

    assert 'Movie C' in caplog.text


def test_log_missing_movies_logs_success_when_all_movies_present(caplog):
    """Success message logged when all drafted movies are in scoreboard."""
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.config = make_config_dict(update_type='s3')
    mock_gsheet_dashboard.released_movies_df = pd.DataFrame({
        'Title': ['Movie A', 'Movie B'],
    })

    draft_df = pd.DataFrame({'movie': ['Movie A', 'Movie B']})

    with patch('src.utils.gsheet.table_to_df', return_value=draft_df):
        with caplog.at_level(logging.INFO):
            from src.utils.gsheet import log_missing_movies

            log_missing_movies(mock_gsheet_dashboard)

    assert 'All movies are on the scoreboard' in caplog.text


def test_log_min_revenue_info_logs_minimum_revenue(caplog):
    """Minimum revenue of most recent data is logged."""
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.year = 2025
    config = make_config_dict(update_type='s3')

    mock_conn = MagicMock()
    mock_result1 = MagicMock()
    mock_result1.fetchnumpy.return_value = {'revenue': np.array([1000000])}
    mock_result2 = MagicMock()
    mock_result2.fetchnumpy.return_value = {'title': np.array(['Low Revenue Movie'])}
    mock_conn.query.side_effect = [mock_result1, mock_result2]

    with patch('src.utils.gsheet.duckdb_connection') as mock_ctx:
        mock_ctx.return_value.__enter__.return_value = mock_conn
        mock_ctx.return_value.__exit__.return_value = None

        with caplog.at_level(logging.INFO):
            from src.utils.gsheet import log_min_revenue_info

            log_min_revenue_info(mock_gsheet_dashboard, config)

    assert 'Minimum revenue' in caplog.text


def test_log_min_revenue_info_handles_no_revenue_data(caplog):
    """Handles case when no revenue data is found."""
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.year = 2025
    config = make_config_dict(update_type='s3')

    mock_conn = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchnumpy.return_value = {'revenue': np.array([])}
    mock_conn.query.return_value = mock_result

    with patch('src.utils.gsheet.duckdb_connection') as mock_ctx:
        mock_ctx.return_value.__enter__.return_value = mock_conn
        mock_ctx.return_value.__exit__.return_value = None

        with caplog.at_level(logging.INFO):
            from src.utils.gsheet import log_min_revenue_info

            log_min_revenue_info(mock_gsheet_dashboard, config)

    assert 'No revenue data found' in caplog.text
