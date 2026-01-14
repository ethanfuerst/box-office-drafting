from unittest.mock import MagicMock

import pandas as pd

from src.utils.gspread_format import df_to_sheet


def test_df_to_sheet_updates_worksheet_with_dataframe():
    """DataFrame values and headers are written to worksheet."""
    df = pd.DataFrame({'Name': ['Alice', 'Bob'], 'Score': [100, 95]})
    mock_worksheet = MagicMock()

    df_to_sheet(df, mock_worksheet, 'A1')

    mock_worksheet.update.assert_called_once()
    call_kwargs = mock_worksheet.update.call_args
    values = call_kwargs.kwargs['values']

    assert values[0] == ['Name', 'Score']
    assert values[1] == ['Alice', 100]
    assert values[2] == ['Bob', 95]


def test_df_to_sheet_uses_specified_location():
    """DataFrame is written to specified range location."""
    df = pd.DataFrame({'A': [1]})
    mock_worksheet = MagicMock()

    df_to_sheet(df, mock_worksheet, 'B5')

    call_kwargs = mock_worksheet.update.call_args.kwargs

    assert call_kwargs['range_name'] == 'B5'


def test_df_to_sheet_applies_format_dict_when_provided():
    """Formatting is applied when format_dict is provided."""
    df = pd.DataFrame({'X': [1, 2]})
    mock_worksheet = MagicMock()
    format_dict = {
        'A1:B1': {'textFormat': {'bold': True}},
        'A2:B2': {'backgroundColor': {'red': 1}},
    }

    df_to_sheet(df, mock_worksheet, 'A1', format_dict=format_dict)

    assert mock_worksheet.format.call_count == 2

    format_calls = mock_worksheet.format.call_args_list
    call_ranges = [c.kwargs['ranges'] for c in format_calls]

    assert 'A1:B1' in call_ranges
    assert 'A2:B2' in call_ranges


def test_df_to_sheet_no_formatting_when_format_dict_none():
    """No formatting calls when format_dict is None."""
    df = pd.DataFrame({'X': [1]})
    mock_worksheet = MagicMock()

    df_to_sheet(df, mock_worksheet, 'A1', format_dict=None)

    mock_worksheet.format.assert_not_called()


def test_df_to_sheet_no_formatting_when_format_dict_empty():
    """No formatting calls when format_dict is empty."""
    df = pd.DataFrame({'X': [1]})
    mock_worksheet = MagicMock()

    df_to_sheet(df, mock_worksheet, 'A1', format_dict={})

    mock_worksheet.format.assert_not_called()


def test_df_to_sheet_handles_empty_dataframe():
    """Empty DataFrame writes only header row."""
    df = pd.DataFrame({'Col1': [], 'Col2': []})
    mock_worksheet = MagicMock()

    df_to_sheet(df, mock_worksheet, 'A1')

    call_kwargs = mock_worksheet.update.call_args.kwargs
    values = call_kwargs['values']

    assert len(values) == 1
    assert values[0] == ['Col1', 'Col2']


def test_df_to_sheet_handles_single_row_dataframe():
    """Single row DataFrame is written correctly."""
    df = pd.DataFrame({'Name': ['Solo'], 'Value': [42]})
    mock_worksheet = MagicMock()

    df_to_sheet(df, mock_worksheet, 'C3')

    call_kwargs = mock_worksheet.update.call_args.kwargs
    values = call_kwargs['values']

    assert len(values) == 2
    assert values[0] == ['Name', 'Value']
    assert values[1] == ['Solo', 42]


def test_df_to_sheet_handles_numeric_columns():
    """Numeric columns are preserved in output."""
    df = pd.DataFrame({'Int': [1, 2], 'Float': [1.5, 2.5]})
    mock_worksheet = MagicMock()

    df_to_sheet(df, mock_worksheet, 'A1')

    call_kwargs = mock_worksheet.update.call_args.kwargs
    values = call_kwargs['values']

    assert values[1] == [1, 1.5]
    assert values[2] == [2, 2.5]


def test_df_to_sheet_format_rules_passed_correctly():
    """Format rules are passed to worksheet.format correctly."""
    df = pd.DataFrame({'X': [1]})
    mock_worksheet = MagicMock()
    format_rules = {'textFormat': {'bold': True, 'fontSize': 12}}
    format_dict = {'A1:A1': format_rules}

    df_to_sheet(df, mock_worksheet, 'A1', format_dict=format_dict)

    mock_worksheet.format.assert_called_once_with(
        ranges='A1:A1', format=format_rules
    )


def test_df_to_sheet_multiple_format_locations():
    """Multiple format locations are each applied."""
    df = pd.DataFrame({'A': [1], 'B': [2], 'C': [3]})
    mock_worksheet = MagicMock()
    format_dict = {
        'A1:A10': {'horizontalAlignment': 'LEFT'},
        'B1:B10': {'horizontalAlignment': 'CENTER'},
        'C1:C10': {'horizontalAlignment': 'RIGHT'},
    }

    df_to_sheet(df, mock_worksheet, 'A1', format_dict=format_dict)

    assert mock_worksheet.format.call_count == 3
