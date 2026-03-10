"""Tests for dashboard runner functions."""

from unittest.mock import MagicMock, patch

import pandas as pd


def test_load_credentials_returns_dict(monkeypatch):
    """Credentials are loaded from environment variable."""
    monkeypatch.setenv('TEST_CREDS', '{"type": "service_account"}')

    from src.sheets.runner import _load_credentials

    result = _load_credentials('TEST_CREDS')

    assert result == {'type': 'service_account'}


def test_load_credentials_raises_on_missing_env():
    """ValueError raised when environment variable is not set."""
    import pytest

    from src.sheets.runner import _load_credentials

    with pytest.raises(ValueError, match='is not set'):
        _load_credentials('NONEXISTENT_CREDS')


def test_handle_missing_worksheets_creates_dashboard():
    """Dashboard worksheet is created via pre_run_hooks."""
    mock_ss = MagicMock()
    mock_ss.get_worksheet_names.return_value = ['Draft']

    from src.sheets.runner import _handle_missing_worksheets

    _handle_missing_worksheets(mock_ss)

    create_calls = mock_ss.create_worksheet.call_args_list
    worksheet_names = [call[0][0] for call in create_calls]

    assert worksheet_names == ['Dashboard']


def test_handle_missing_worksheets_deletes_existing_dashboard():
    """Existing Dashboard worksheet is deleted before recreation."""
    mock_ss = MagicMock()
    mock_ss.get_worksheet_names.return_value = ['Dashboard', 'Draft']

    from src.sheets.runner import _handle_missing_worksheets

    _handle_missing_worksheets(mock_ss)

    mock_ss.delete_worksheet.assert_called_once_with('Dashboard')


def test_handle_missing_worksheets_creates_draftee_worksheets():
    """Draftee worksheets are created when draftee_names is provided."""
    mock_ss = MagicMock()
    mock_ss.get_worksheet_names.return_value = ['Draft']

    from src.sheets.runner import _handle_missing_worksheets

    _handle_missing_worksheets(mock_ss, draftee_names=['Alice', 'Bob'])

    create_calls = mock_ss.create_worksheet.call_args_list
    worksheet_names = [call[0][0] for call in create_calls]

    assert 'Alice' in worksheet_names
    assert 'Bob' in worksheet_names


def test_handle_missing_worksheets_deletes_existing_draftee_worksheets():
    """Existing draftee worksheets are deleted before recreation."""
    mock_ss = MagicMock()
    mock_ss.get_worksheet_names.return_value = ['Draft', 'Alice']

    from src.sheets.runner import _handle_missing_worksheets

    _handle_missing_worksheets(mock_ss, draftee_names=['Alice', 'Bob'])

    delete_calls = [call[0][0] for call in mock_ss.delete_worksheet.call_args_list]

    assert 'Alice' in delete_calls
    assert 'Dashboard' not in delete_calls
    assert 'Bob' not in delete_calls


def test_adjust_worksheet_order_without_draftees():
    """Worksheet order is set without draftee tabs."""
    mock_ss = MagicMock()

    from src.sheets.runner import _adjust_worksheet_order

    _adjust_worksheet_order(mock_ss)

    mock_ss.reorder_worksheets.assert_called_once_with(
        ['Dashboard', 'Draft', 'Manual Adds', 'Multipliers and Exclusions']
    )


def test_adjust_worksheet_order_with_draftees():
    """Draftee tabs come after Dashboard, before Draft/Manual Adds/Multipliers."""
    mock_ss = MagicMock()

    from src.sheets.runner import _adjust_worksheet_order

    _adjust_worksheet_order(mock_ss, draftee_names=['Alice', 'Bob'])

    mock_ss.reorder_worksheets.assert_called_once_with(
        [
            'Dashboard',
            'Alice',
            'Bob',
            'Draft',
            'Manual Adds',
            'Multipliers and Exclusions',
        ]
    )


def test_get_draftee_names_returns_names_in_draft_order():
    """Draftee names are returned ordered by their first overall pick."""
    drafter_df = pd.DataFrame({
        'movie': ['M1', 'M2', 'M3', 'M4'],
        'name': ['Bob', 'Alice', 'Bob', 'Alice'],
        'overall_pick': [1, 2, 3, 4],
        'round': [1, 1, 2, 2],
    })

    with patch('src.sheets.runner.table_to_df', return_value=drafter_df):
        from src.sheets.runner import _get_draftee_names

        names = _get_draftee_names({'draft_id': 'test'})

    assert names == ['Bob', 'Alice']


def test_ensure_source_tabs_exist_creates_missing_tabs(monkeypatch):
    """Missing source tabs are created with column headers."""
    monkeypatch.setenv('TEST_CREDS', '{"type": "service_account"}')
    mock_ss = MagicMock()
    mock_ss.get_worksheet_names.return_value = ['Draft']
    mock_ws = MagicMock()
    mock_ss.create_worksheet.return_value = mock_ws

    with patch('src.sheets.runner.Spreadsheet') as mock_spreadsheet:
        mock_spreadsheet.return_value.__enter__ = MagicMock(return_value=mock_ss)
        mock_spreadsheet.return_value.__exit__ = MagicMock(return_value=False)

        from src.sheets.runner import ensure_source_tabs_exist

        ensure_source_tabs_exist({
            'gspread_credentials_name': 'TEST_CREDS',
            'sheet_name': 'Test Sheet',
        })

    create_calls = mock_ss.create_worksheet.call_args_list
    worksheet_names = [call[0][0] for call in create_calls]

    assert 'Manual Adds' in worksheet_names
    assert 'Multipliers and Exclusions' in worksheet_names
    assert mock_ws.write_values.call_count == 2
    assert mock_ws.flush.call_count == 2


def test_ensure_source_tabs_exist_skips_existing_tabs(monkeypatch):
    """Existing source tabs are not recreated."""
    monkeypatch.setenv('TEST_CREDS', '{"type": "service_account"}')
    mock_ss = MagicMock()
    mock_ss.get_worksheet_names.return_value = [
        'Draft', 'Manual Adds', 'Multipliers and Exclusions'
    ]

    with patch('src.sheets.runner.Spreadsheet') as mock_spreadsheet:
        mock_spreadsheet.return_value.__enter__ = MagicMock(return_value=mock_ss)
        mock_spreadsheet.return_value.__exit__ = MagicMock(return_value=False)

        from src.sheets.runner import ensure_source_tabs_exist

        ensure_source_tabs_exist({
            'gspread_credentials_name': 'TEST_CREDS',
            'sheet_name': 'Test Sheet',
        })

    mock_ss.create_worksheet.assert_not_called()
