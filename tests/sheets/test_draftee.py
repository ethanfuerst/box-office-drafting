"""Tests for DrafteeWorksheet definition."""

from unittest.mock import MagicMock, patch

import pandas as pd

from tests.conftest import make_config_dict


def _make_draftee_dashboard_df():
    """Create a sample draftee_dashboard DataFrame matching the SQL model output."""
    return pd.DataFrame({
        'draftee_name': ['Alice', 'Alice', 'Bob', 'Bob'],
        'round': [1, 2, 1, 2],
        'overall_pick': [1, 3, 2, 4],
        'movie': ['Movie A', 'Movie C', 'Movie B', 'Movie D'],
        'first_seen_date': ['01/15/2026', None, '01/20/2026', None],
        'still_in_theaters': ['Yes', None, 'No', None],
        'revenue': [1000000.0, None, 2000000.0, None],
        'multiplier': [1.0, 3.0, 1.0, 1.0],
        'scored_revenue': [1000000.0, None, 2000000.0, None],
        'better_pick': ['', None, 'Movie X', None],
        'better_pick_scored_revenue': [None, None, 500000.0, None],
    })


def _make_scoreboard_df():
    """Create a sample scoreboard DataFrame matching the SQL model output."""
    return pd.DataFrame({
        'Name': ['Bob', 'Alice'],
        'Scored Revenue': [2000000, 1000000],
        '# Released': [1, 1],
        '# Optimal Picks': [1, 1],
        '% Optimal Picks': [1.0, 1.0],
        'Unadjusted Revenue': [2000000, 1000000],
    })


def _mock_table_to_df(config, table_name, columns=None):
    """Mock table_to_df that returns appropriate DataFrames."""
    if table_name == 'dashboards.draftee_dashboard':
        return _make_draftee_dashboard_df()
    elif table_name == 'dashboards.scoreboard':
        return _make_scoreboard_df()
    return pd.DataFrame()


# --- DrafteeWorksheet tests ---


def test_draftee_worksheet_name():
    """DrafteeWorksheet name matches draftee name."""
    from src.sheets.tabs.draftee import DrafteeWorksheet

    worksheet = DrafteeWorksheet('Alice')

    assert worksheet.name == 'Alice'


def test_draftee_worksheet_generate_returns_two_assets():
    """Generate returns scoreboard asset at B2 and picks asset at B5."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Alice')
        assets = worksheet.generate(config, context)

    assert len(assets) == 2
    assert assets[0].location.cell == 'B2'
    assert assets[1].location.cell == 'B5'


def test_draftee_worksheet_generate_scoreboard_has_draftee_data():
    """Scoreboard asset contains data for the specified draftee."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Alice')
        assets = worksheet.generate(config, context)

    scoreboard = assets[0].df

    assert len(scoreboard) == 1
    assert scoreboard.iloc[0]['Scored Revenue'] == 1000000
    assert 'Name' not in scoreboard.columns


def test_draftee_worksheet_generate_scoreboard_empty_draftee():
    """Scoreboard shows zeros when draftee has no released movies."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Unknown')
        assets = worksheet.generate(config, context)

    scoreboard = assets[0].df

    assert len(scoreboard) == 1
    assert scoreboard.iloc[0]['Scored Revenue'] == 0


def test_draftee_worksheet_generate_filters_picks_by_draftee_name():
    """Picks asset only includes picks for the specified draftee."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Bob')
        assets = worksheet.generate(config, context)

    assert list(assets[1].df['Movie']) == ['Movie B', 'Movie D']


def test_draftee_worksheet_generate_drops_draftee_name_column():
    """Picks DataFrame does not contain the draftee_name column."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Alice')
        assets = worksheet.generate(config, context)

    assert 'draftee_name' not in assets[1].df.columns


def test_draftee_worksheet_generate_renames_columns():
    """Picks DataFrame uses display column names."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Alice')
        assets = worksheet.generate(config, context)

    expected_columns = [
        'Round',
        'Overall Pick',
        'Movie',
        'First Seen Date',
        'Still In Theaters',
        'Revenue',
        'Multiplier',
        'Scored Revenue',
        'Better Pick',
        'Better Pick Scored Revenue',
    ]

    assert list(assets[1].df.columns) == expected_columns


def test_draftee_worksheet_generate_fills_none_with_empty_string():
    """None/NaN values are replaced with empty strings for display."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Alice')
        assets = worksheet.generate(config, context)

    unreleased_row = assets[1].df[assets[1].df['Movie'] == 'Movie C'].iloc[0]

    assert unreleased_row['First Seen Date'] == ''
    assert unreleased_row['Still In Theaters'] == ''
    assert unreleased_row['Revenue'] == ''
    assert unreleased_row['Scored Revenue'] == ''


def test_draftee_worksheet_generate_populates_context():
    """Generate stores picks DataFrame in context."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Alice')
        worksheet.generate(config, context)

    assert 'draftee_Alice_df' in context
    assert len(context['draftee_Alice_df']) == 2


def test_draftee_worksheet_generate_caches_shared_data():
    """Shared data is loaded once and cached in context."""
    call_count = {'count': 0}

    def counting_mock(config, table_name, columns=None):
        call_count['count'] += 1
        return _mock_table_to_df(config, table_name, columns)

    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch('src.sheets.tabs.draftee.table_to_df', side_effect=counting_mock):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        alice = DrafteeWorksheet('Alice')
        alice.generate(config, context)
        initial_count = call_count['count']

        bob = DrafteeWorksheet('Bob')
        bob.generate(config, context)

    # Second worksheet should not reload data (0 additional calls)
    assert call_count['count'] == initial_count


def test_draftee_worksheet_generate_scoreboard_has_hooks():
    """Scoreboard asset has 2 post-write hooks."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Alice')
        assets = worksheet.generate(config, context)

    assert len(assets[0].post_write_hooks) == 2


def test_draftee_worksheet_generate_picks_has_hooks():
    """Picks asset has 3 post-write hooks."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Alice')
        assets = worksheet.generate(config, context)

    assert len(assets[1].post_write_hooks) == 3


def test_draftee_worksheet_generate_empty_picks():
    """Returns empty picks DataFrame with correct columns when draftee has no picks."""
    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch(
        'src.sheets.tabs.draftee.table_to_df', side_effect=_mock_table_to_df
    ):
        from src.sheets.tabs.draftee import DrafteeWorksheet

        worksheet = DrafteeWorksheet('Unknown')
        assets = worksheet.generate(config, context)

    assert len(assets[1].df) == 0
    assert 'Round' in assets[1].df.columns
    assert 'Movie' in assets[1].df.columns


def test_draftee_worksheet_get_formatting():
    """get_formatting returns WorksheetFormatting with column widths and notes."""
    from eftoolkit.gsheets.runner.types import WorksheetFormatting

    from src.sheets.tabs.draftee import (
        DRAFTEE_COLUMN_WIDTHS,
        DRAFTEE_NOTES,
        DrafteeWorksheet,
    )

    worksheet = DrafteeWorksheet('Alice')
    formatting = worksheet.get_formatting({})

    assert isinstance(formatting, WorksheetFormatting)
    assert formatting.column_widths == DRAFTEE_COLUMN_WIDTHS
    assert formatting.notes == DRAFTEE_NOTES


# --- Scoreboard hook tests ---


def test_apply_scoreboard_header_formats_b2_f2():
    """Scoreboard header formatting is applied to B2:F2."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.draftee import DrafteeWorksheet
    from src.sheets.tabs.formats import HEADER_FORMAT

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='B2'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Alice',
        runner_context={},
    )

    worksheet = DrafteeWorksheet('Alice')
    worksheet._apply_scoreboard_header(ctx)

    format_call = mock_ws.format_range.call_args[0][0]

    assert format_call.value == 'B2:F2'
    assert mock_ws.format_range.call_args[0][1] == HEADER_FORMAT


def test_apply_scoreboard_formatting():
    """Scoreboard data formatting is applied to row 3."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.draftee import DrafteeWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='B2'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Alice',
        runner_context={},
    )

    worksheet = DrafteeWorksheet('Alice')
    worksheet._apply_scoreboard_formatting(ctx)

    # 4 format calls: B3 currency, C3:D3, E3 percent, F3 currency
    assert mock_ws.format_range.call_count == 4


# --- Picks hook tests ---


def test_apply_picks_header_formats_b5_k5():
    """Picks header formatting is applied to B5:K5."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.draftee import DrafteeWorksheet
    from src.sheets.tabs.formats import HEADER_FORMAT

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='B5'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Alice',
        runner_context={},
    )

    worksheet = DrafteeWorksheet('Alice')
    worksheet._apply_picks_header(ctx)

    format_call = mock_ws.format_range.call_args[0][0]

    assert format_call.value == 'B5:K5'
    assert mock_ws.format_range.call_args[0][1] == HEADER_FORMAT


def test_apply_picks_formatting_formats_data_columns():
    """Cell formatting is applied to all picks data columns starting at row 6."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.draftee import DrafteeWorksheet

    mock_ws = MagicMock()
    picks_df = pd.DataFrame({
        'Round': [1, 2],
        'Overall Pick': [1, 3],
        'Movie': ['Movie A', 'Movie C'],
        'First Seen Date': ['01/15/2026', ''],
        'Still In Theaters': ['Yes', ''],
        'Revenue': [1000000, ''],
        'Multiplier': [1.0, 3.0],
        'Scored Revenue': [1000000, ''],
        'Better Pick': ['', ''],
        'Better Pick Scored Revenue': ['', ''],
    })
    mock_asset = WorksheetAsset(
        df=picks_df,
        location=CellLocation(cell='B5'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Alice',
        runner_context={'draftee_Alice_df': picks_df},
    )

    worksheet = DrafteeWorksheet('Alice')
    worksheet._apply_picks_formatting(ctx)

    # 10 columns formatted: B through K
    assert mock_ws.format_range.call_count == 10
    # Verify data starts at row 6
    first_call_range = mock_ws.format_range.call_args_list[0][0][0]
    assert first_call_range == 'B6:B7'


def test_apply_picks_formatting_returns_early_when_empty():
    """Formatting is skipped when picks DataFrame is empty."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.draftee import DrafteeWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='B5'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Alice',
        runner_context={'draftee_Alice_df': pd.DataFrame()},
    )

    worksheet = DrafteeWorksheet('Alice')
    worksheet._apply_picks_formatting(ctx)

    mock_ws.format_range.assert_not_called()


def test_apply_still_in_theaters_conditional_format():
    """Conditional formatting is applied to Still In Theaters column (F) at row 6+."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.draftee import DrafteeWorksheet

    mock_ws = MagicMock()
    picks_df = pd.DataFrame({
        'Round': [1, 2, 3],
        'Movie': ['A', 'B', 'C'],
    })
    mock_asset = WorksheetAsset(
        df=picks_df,
        location=CellLocation(cell='B5'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Alice',
        runner_context={'draftee_Alice_df': picks_df},
    )

    worksheet = DrafteeWorksheet('Alice')
    worksheet._apply_still_in_theaters_conditional_format(ctx)

    mock_ws.add_conditional_format.assert_called_once_with(
        range_name='F6:F8',
        rule={
            'type': 'TEXT_EQ',
            'values': ['Yes'],
            'format': {'backgroundColor': {'red': 0, 'green': 0.9, 'blue': 0}},
        },
    )
