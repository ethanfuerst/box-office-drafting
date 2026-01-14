from unittest.mock import MagicMock, patch

from tests.conftest import make_config_dict


def test_load_dashboard_data_orchestrates_dashboard_creation():
    """load_dashboard_data orchestrates all dashboard functions."""
    config = make_config_dict(update_type='s3')

    with patch('src.utils.gsheet.GoogleSheetDashboard') as MockDashboard:
        mock_dashboard = MagicMock()
        MockDashboard.return_value = mock_dashboard

        with patch('src.utils.gsheet.update_dashboard') as mock_update:
            with patch('src.utils.gsheet.update_titles') as mock_titles:
                with patch(
                    'src.utils.gsheet.apply_conditional_formatting'
                ) as mock_format:
                    with patch(
                        'src.utils.gsheet.add_comments_to_dashboard'
                    ) as mock_comments:
                        with patch(
                            'src.utils.gsheet.log_missing_movies'
                        ) as mock_log_missing:
                            with patch(
                                'src.utils.gsheet.log_min_revenue_info'
                            ) as mock_log_revenue:
                                from src.utils.gsheet import load_dashboard_data

                                load_dashboard_data(config)

    MockDashboard.assert_called_once_with(config)
    mock_update.assert_called_once_with(mock_dashboard, config)
    mock_titles.assert_called_once_with(mock_dashboard)
    mock_format.assert_called_once_with(mock_dashboard)
    mock_comments.assert_called_once_with(mock_dashboard)
    mock_log_missing.assert_called_once_with(mock_dashboard)
    mock_log_revenue.assert_called_once_with(mock_dashboard, config)
