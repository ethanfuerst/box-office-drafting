from unittest.mock import patch

import pytest

from tests.conftest import make_config_dict


def test_google_sheet_sync_calls_run_sqlmesh_plan_first(tmp_path):
    """run_sqlmesh_plan is called before load_dashboard_data."""
    config = make_config_dict(update_type='s3')
    config['path'] = tmp_path / 'config.yml'

    call_order = []

    with patch('src.etl.run_sqlmesh_plan') as mock_sqlmesh:
        mock_sqlmesh.side_effect = lambda x: call_order.append('sqlmesh')

        with patch('src.etl.load_dashboard_data') as mock_dashboard:
            mock_dashboard.side_effect = lambda x: call_order.append('dashboard')

            from src.etl import google_sheet_sync

            google_sheet_sync(config)

    assert call_order == ['sqlmesh', 'dashboard']


def test_google_sheet_sync_passes_config_to_both_functions(tmp_path):
    """Config dict is passed to both run_sqlmesh_plan and load_dashboard_data."""
    config = make_config_dict(update_type='s3')
    config['path'] = tmp_path / 'config.yml'

    with patch('src.etl.run_sqlmesh_plan') as mock_sqlmesh:
        with patch('src.etl.load_dashboard_data') as mock_dashboard:
            from src.etl import google_sheet_sync

            google_sheet_sync(config)

    mock_sqlmesh.assert_called_once_with(config)
    mock_dashboard.assert_called_once_with(config)


def test_google_sheet_sync_propagates_sqlmesh_exception(tmp_path):
    """Exception from run_sqlmesh_plan propagates up."""
    config = make_config_dict(update_type='s3')
    config['path'] = tmp_path / 'config.yml'

    with patch('src.etl.run_sqlmesh_plan') as mock_sqlmesh:
        mock_sqlmesh.side_effect = RuntimeError('SQLMesh failed')

        with patch('src.etl.load_dashboard_data') as mock_dashboard:
            from src.etl import google_sheet_sync

            with pytest.raises(RuntimeError, match='SQLMesh failed'):
                google_sheet_sync(config)

    mock_dashboard.assert_not_called()


def test_google_sheet_sync_propagates_dashboard_exception(tmp_path):
    """Exception from load_dashboard_data propagates up."""
    config = make_config_dict(update_type='s3')
    config['path'] = tmp_path / 'config.yml'

    with patch('src.etl.run_sqlmesh_plan'):
        with patch('src.etl.load_dashboard_data') as mock_dashboard:
            mock_dashboard.side_effect = RuntimeError('Dashboard failed')

            from src.etl import google_sheet_sync

            with pytest.raises(RuntimeError, match='Dashboard failed'):
                google_sheet_sync(config)
