from unittest.mock import MagicMock, patch

from tests.conftest import make_config_dict


def test_load_dashboard_data_orchestrates_dashboard_creation():
    """load_dashboard_data orchestrates all dashboard functions."""
    config = make_config_dict(update_type='s3')

    with patch('src.etl.GoogleSheetDashboard') as MockDashboard:
        mock_dashboard = MagicMock()
        MockDashboard.return_value = mock_dashboard

        with patch('src.etl.update_dashboard') as mock_update:
            with patch('src.etl.update_titles') as mock_titles:
                with patch('src.etl.apply_conditional_formatting') as mock_format:
                    with patch('src.etl.add_comments_to_dashboard') as mock_comments:
                        with patch('src.etl.log_missing_movies') as mock_log_missing:
                            with patch(
                                'src.etl.log_min_revenue_info'
                            ) as mock_log_revenue:
                                from src.etl import load_dashboard_data

                                load_dashboard_data(config)

    MockDashboard.assert_called_once_with(config)
    mock_update.assert_called_once_with(mock_dashboard, config)
    mock_titles.assert_called_once_with(mock_dashboard)
    mock_format.assert_called_once_with(mock_dashboard)
    mock_comments.assert_called_once_with(mock_dashboard)
    mock_log_missing.assert_called_once_with(mock_dashboard)
    mock_log_revenue.assert_called_once_with(mock_dashboard, config)
