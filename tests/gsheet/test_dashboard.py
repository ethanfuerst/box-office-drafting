from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from tests.conftest import make_config_dict


def test_update_dashboard_writes_all_dashboard_elements(monkeypatch):
    """All dashboard elements are written to the worksheet."""
    monkeypatch.setenv('TEST_GSPREAD_CREDS', '{}')

    mock_worksheet = MagicMock()
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.worksheet = mock_worksheet
    mock_gsheet_dashboard.released_movies_df = pd.DataFrame({
        'Still In Theaters': ['No', 'No'],
    })
    mock_gsheet_dashboard.year = 2024
    mock_gsheet_dashboard.add_picks_table = False
    mock_gsheet_dashboard.dashboard_elements = [
        (pd.DataFrame({'A': [1]}), 'B4', {'B4': {'bold': True}}),
        (pd.DataFrame({'B': [2]}), 'I4', None),
    ]

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchnumpy.return_value = {
        'published_timestamp_utc': np.array([np.datetime64('2024-01-01T00:00:00')])
    }
    mock_db.connection.query.return_value = mock_result

    config = make_config_dict(update_type='s3')

    with patch('src.utils.gsheet.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        with patch('src.utils.gsheet.df_to_sheet') as mock_df_to_sheet:
            from src.utils.gsheet import update_dashboard

            update_dashboard(mock_gsheet_dashboard, config)

    assert mock_df_to_sheet.call_count == 2


def test_update_dashboard_updates_last_updated_timestamp(monkeypatch):
    """Last updated timestamp is written to the worksheet."""
    monkeypatch.setenv('TEST_GSPREAD_CREDS', '{}')

    mock_worksheet = MagicMock()
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.worksheet = mock_worksheet
    mock_gsheet_dashboard.released_movies_df = pd.DataFrame({
        'Still In Theaters': ['Yes'],
    })
    mock_gsheet_dashboard.year = 2025
    mock_gsheet_dashboard.add_picks_table = False
    mock_gsheet_dashboard.sheet_height = 10
    mock_gsheet_dashboard.dashboard_elements = []

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchnumpy.return_value = {
        'published_timestamp_utc': np.array([np.datetime64('2025-01-15T12:00:00')])
    }
    mock_db.connection.query.return_value = mock_result

    config = make_config_dict(update_type='s3')

    with patch('src.utils.gsheet.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        with patch('src.utils.gsheet.df_to_sheet'):
            from src.utils.gsheet import update_dashboard

            update_dashboard(mock_gsheet_dashboard, config)

    update_calls = mock_worksheet.update.call_args_list
    g2_call = [c for c in update_calls if c.kwargs.get('range_name') == 'G2']

    assert len(g2_call) == 1


def test_update_titles_sets_dashboard_name():
    """Dashboard name is written to cell B2."""
    mock_worksheet = MagicMock()
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.worksheet = mock_worksheet
    mock_gsheet_dashboard.dashboard_name = 'My Test Dashboard'
    mock_gsheet_dashboard.add_picks_table = False

    from src.utils.gsheet import update_titles

    update_titles(mock_gsheet_dashboard)

    update_calls = mock_worksheet.update.call_args_list
    b2_call = [c for c in update_calls if c.kwargs.get('range_name') == 'B2']

    assert len(b2_call) == 1
    assert b2_call[0].kwargs['values'] == [['My Test Dashboard']]


def test_update_titles_sets_released_movies_title():
    """Released Movies title is written to cell I2."""
    mock_worksheet = MagicMock()
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.worksheet = mock_worksheet
    mock_gsheet_dashboard.dashboard_name = 'Test'
    mock_gsheet_dashboard.add_picks_table = False

    from src.utils.gsheet import update_titles

    update_titles(mock_gsheet_dashboard)

    update_calls = mock_worksheet.update.call_args_list
    i2_call = [c for c in update_calls if c.kwargs.get('range_name') == 'I2']

    assert len(i2_call) == 1
    assert i2_call[0].kwargs['values'] == [['Released Movies']]


def test_update_titles_merges_title_cells():
    """Title cells are merged."""
    mock_worksheet = MagicMock()
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.worksheet = mock_worksheet
    mock_gsheet_dashboard.dashboard_name = 'Test'
    mock_gsheet_dashboard.add_picks_table = False

    from src.utils.gsheet import update_titles

    update_titles(mock_gsheet_dashboard)

    merge_calls = [str(c) for c in mock_worksheet.merge_cells.call_args_list]

    assert any('B2:F2' in c for c in merge_calls)
    assert any('I2:X2' in c for c in merge_calls)


def test_update_titles_adds_worst_picks_title_when_single_table():
    """Worst Picks title is added when showing single picks table."""
    mock_worksheet = MagicMock()
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.worksheet = mock_worksheet
    mock_gsheet_dashboard.dashboard_name = 'Test'
    mock_gsheet_dashboard.add_picks_table = True
    mock_gsheet_dashboard.add_both_picks_tables = False
    mock_gsheet_dashboard.picks_row_num = 12

    from src.utils.gsheet import update_titles

    update_titles(mock_gsheet_dashboard)

    update_calls = mock_worksheet.update.call_args_list
    worst_picks_call = [
        c for c in update_calls if 'B11' in str(c.kwargs.get('range_name', ''))
    ]

    assert len(worst_picks_call) == 1
    assert worst_picks_call[0].kwargs['values'] == [['Worst Picks']]


def test_update_titles_adds_both_picks_titles_when_both_tables():
    """Both Worst Picks and Best Picks titles are added when showing both tables."""
    mock_worksheet = MagicMock()
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.worksheet = mock_worksheet
    mock_gsheet_dashboard.dashboard_name = 'Test'
    mock_gsheet_dashboard.add_picks_table = True
    mock_gsheet_dashboard.add_both_picks_tables = True
    mock_gsheet_dashboard.picks_row_num = 12
    mock_gsheet_dashboard.best_picks_row_num = 20

    from src.utils.gsheet import update_titles

    update_titles(mock_gsheet_dashboard)

    update_calls = mock_worksheet.update.call_args_list
    range_names = [str(c.kwargs.get('range_name', '')) for c in update_calls]

    assert 'B11' in range_names
    assert 'B19' in range_names


def test_apply_conditional_formatting_adds_still_in_theater_rule():
    """Conditional formatting rule for 'Still In Theaters' is added."""
    mock_worksheet = MagicMock()
    mock_rules = MagicMock()
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.worksheet = mock_worksheet

    with patch('src.utils.gsheet.gsf') as mock_gsf:
        mock_gsf.get_conditional_format_rules.return_value = mock_rules

        from src.utils.gsheet import apply_conditional_formatting

        apply_conditional_formatting(mock_gsheet_dashboard)

    mock_rules.append.assert_called_once()
    mock_rules.save.assert_called_once()


def test_add_comments_to_dashboard_inserts_notes_from_config():
    """Notes from dashboard_notes.json are inserted."""
    mock_worksheet = MagicMock()
    mock_gsheet_dashboard = MagicMock()
    mock_gsheet_dashboard.worksheet = mock_worksheet

    notes_dict = {'A1': 'Test note', 'B2': 'Another note'}

    with patch('src.utils.gsheet.load_format_config', return_value=notes_dict):
        from src.utils.gsheet import add_comments_to_dashboard

        add_comments_to_dashboard(mock_gsheet_dashboard)

    mock_worksheet.insert_notes.assert_called_once_with(notes_dict)
