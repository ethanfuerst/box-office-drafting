"""Tests for dashboard runner functions."""

from unittest.mock import MagicMock


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


def test_handle_missing_worksheets_creates_worksheets():
    """Worksheet structure is created correctly via pre_run_hooks."""
    mock_ss = MagicMock()
    mock_ss.get_worksheet_names.return_value = ['Draft']

    from src.sheets.runner import _handle_missing_worksheets

    _handle_missing_worksheets(mock_ss)

    # Should create Manual Adds, Multipliers, and Dashboard
    create_calls = mock_ss.create_worksheet.call_args_list
    worksheet_names = [call[0][0] for call in create_calls]

    assert 'Manual Adds' in worksheet_names
    assert 'Multipliers and Exclusions' in worksheet_names
    assert 'Dashboard' in worksheet_names


def test_handle_missing_worksheets_deletes_existing_dashboard():
    """Existing Dashboard worksheet is deleted before recreation."""
    mock_ss = MagicMock()
    mock_ss.get_worksheet_names.return_value = ['Dashboard', 'Draft']

    from src.sheets.runner import _handle_missing_worksheets

    _handle_missing_worksheets(mock_ss)

    mock_ss.delete_worksheet.assert_called_once_with('Dashboard')
