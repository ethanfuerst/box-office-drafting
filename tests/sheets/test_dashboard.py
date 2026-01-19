"""Tests for DashboardWorksheet definition."""

from unittest.mock import MagicMock, patch

import pandas as pd

from tests.conftest import make_config_dict


def test_dashboard_worksheet_name():
    """DashboardWorksheet has correct name property."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    worksheet = DashboardWorksheet()

    assert worksheet.name == 'Dashboard'


def test_dashboard_worksheet_generate_returns_scoreboard_asset():
    """Scoreboard asset is included in generated assets."""
    scoreboard_df = pd.DataFrame({
        'Name': ['Player 1', 'Player 2'],
        'Scored Revenue': [1000000, 2000000],
        '# Released': [5, 6],
        '# Optimal Picks': [3, 4],
        '% Optimal Picks': [0.6, 0.67],
        'Unadjusted Revenue': [900000, 1800000],
    })
    released_movies_df = pd.DataFrame({
        'Rank': [1, 2],
        'Title': ['Movie A', 'Movie B'],
        'Drafted By': ['Player 1', 'Player 2'],
        'Revenue': [1000000, 2000000],
        'Scored Revenue': [1000000, 2000000],
        'Round Drafted': [1, 1],
        'Overall Pick': [1, 2],
        'Multiplier': [1.0, 1.0],
        'Domestic Revenue': [500000, 1000000],
        'Domestic Revenue %': [0.5, 0.5],
        'Foreign Revenue': [500000, 1000000],
        'Foreign Revenue %': [0.5, 0.5],
        'Better Pick': ['', ''],
        'Better Pick Scored Revenue': [0, 0],
        'First Seen Date': ['2025-01-01', '2025-01-02'],
        'Still In Theaters': ['Yes', 'No'],
    })
    worst_picks_df = pd.DataFrame({
        'Rank': [1],
        'Title': ['Bad Movie'],
        'Drafted By': ['Player 1'],
        'Overall Pick': [3],
        'Number of Better Picks': [2],
        'Missed Revenue': [500000],
    })
    best_picks_df = pd.DataFrame({
        'Rank': [1],
        'Title': ['Good Movie'],
        'Drafted By': ['Player 2'],
        'Overall Pick': [4],
        'Positions Gained': [3],
        'Actual Revenue': [1500000],
    })

    def mock_table_to_df(config, table_name, columns=None):
        if table_name == 'dashboards.scoreboard':
            return scoreboard_df
        elif table_name == 'combined.base_query':
            return released_movies_df
        elif table_name == 'dashboards.worst_picks':
            return worst_picks_df
        elif table_name == 'dashboards.best_picks':
            return best_picks_df
        return pd.DataFrame()

    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch('src.sheets.tabs.dashboard.table_to_df', side_effect=mock_table_to_df):
        from src.sheets.tabs.dashboard import DashboardWorksheet

        worksheet = DashboardWorksheet()
        assets = worksheet.generate(config, context)

    # Should have at least scoreboard and released movies
    assert len(assets) >= 2

    # First asset should be scoreboard at B4
    assert assets[0].location.cell == 'B4'
    assert len(assets[0].df) == 2  # 2 players

    # Second asset should be released movies at I4
    assert assets[1].location.cell == 'I4'
    assert len(assets[1].df) == 2  # 2 movies


def test_dashboard_worksheet_generate_populates_context():
    """Context is populated with necessary data for formatting phase."""
    scoreboard_df = pd.DataFrame({
        'Name': ['Player 1'],
        'Scored Revenue': [1000000],
        '# Released': [5],
        '# Optimal Picks': [3],
        '% Optimal Picks': [0.6],
        'Unadjusted Revenue': [900000],
    })
    released_movies_df = pd.DataFrame({
        'Rank': [1],
        'Title': ['Movie A'],
        'Drafted By': ['Player 1'],
        'Revenue': [1000000],
        'Scored Revenue': [1000000],
        'Round Drafted': [1],
        'Overall Pick': [1],
        'Multiplier': [1.0],
        'Domestic Revenue': [500000],
        'Domestic Revenue %': [0.5],
        'Foreign Revenue': [500000],
        'Foreign Revenue %': [0.5],
        'Better Pick': [''],
        'Better Pick Scored Revenue': [0],
        'First Seen Date': ['2025-01-01'],
        'Still In Theaters': ['Yes'],
    })
    worst_picks_df = pd.DataFrame({
        'Rank': [],
        'Title': [],
        'Drafted By': [],
        'Overall Pick': [],
        'Number of Better Picks': [],
        'Missed Revenue': [],
    })
    best_picks_df = pd.DataFrame({
        'Rank': [],
        'Title': [],
        'Drafted By': [],
        'Overall Pick': [],
        'Positions Gained': [],
        'Actual Revenue': [],
    })

    def mock_table_to_df(config, table_name, columns=None):
        if table_name == 'dashboards.scoreboard':
            return scoreboard_df
        elif table_name == 'combined.base_query':
            return released_movies_df
        elif table_name == 'dashboards.worst_picks':
            return worst_picks_df
        elif table_name == 'dashboards.best_picks':
            return best_picks_df
        return pd.DataFrame()

    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch('src.sheets.tabs.dashboard.table_to_df', side_effect=mock_table_to_df):
        from src.sheets.tabs.dashboard import DashboardWorksheet

        worksheet = DashboardWorksheet()
        worksheet.generate(config, context)

    assert 'released_movies_df' in context
    assert 'scoreboard_df' in context
    assert 'layout' in context
    assert 'year' in context
    assert 'dashboard_name' in context
    assert 'sheet_height' in context


def test_dashboard_worksheet_get_formatting():
    """get_formatting returns WorksheetFormatting with notes and column widths."""
    from eftoolkit.gsheets.runner.types import WorksheetFormatting

    from src.sheets.tabs.dashboard import (
        COLUMN_WIDTHS,
        DASHBOARD_NOTES,
        DashboardWorksheet,
    )

    worksheet = DashboardWorksheet()
    context = {
        'sheet_height': 50,
        'add_picks_table': False,
    }

    formatting = worksheet.get_formatting(context)

    assert isinstance(formatting, WorksheetFormatting)
    assert formatting.notes == DASHBOARD_NOTES
    # Merge ranges are handled by post-write hooks, not WorksheetFormatting
    assert formatting.merge_ranges == []
    # Column widths are now in get_formatting
    assert formatting.column_widths == COLUMN_WIDTHS
    assert formatting.auto_resize_columns is None
    # Cell-level and conditional formatting handled by per-asset post-write hooks
    assert formatting.format_dict is None
    assert formatting.conditional_formats == []


def test_dashboard_worksheet_get_formatting_no_merge_ranges():
    """get_formatting returns empty merge_ranges (merges handled by hooks)."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    worksheet = DashboardWorksheet()
    context = {
        'sheet_height': 50,
        'add_picks_table': True,
        'add_both_picks_tables': True,
        'picks_row_num': 12,
        'best_picks_row_num': 20,
    }

    formatting = worksheet.get_formatting(context)

    # Merge ranges are handled by post-write hooks for proper ordering
    # (write text, merge, format) to ensure text centering works correctly
    assert formatting.merge_ranges == []


def test_apply_still_in_theaters_conditional_format():
    """Conditional formatting is applied to Still In Theaters column (X) via hook."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='I4'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={'sheet_height': 50},
    )

    worksheet = DashboardWorksheet()
    worksheet._apply_still_in_theaters_conditional_format(ctx)

    mock_ws.add_conditional_format.assert_called_once_with(
        range_name='X5:X50',
        rule={
            'type': 'TEXT_EQ',
            'values': ['Yes'],
            'format': {'backgroundColor': {'red': 0, 'green': 0.9, 'blue': 0}},
        },
    )


def test_dashboard_worksheet_adds_picks_tables_when_space_available():
    """Picks tables are added when there is sufficient space."""
    # Create data that will have enough space for both picks tables
    scoreboard_df = pd.DataFrame({
        'Name': ['Player 1', 'Player 2'],
        'Scored Revenue': [1000000, 2000000],
        '# Released': [5, 6],
        '# Optimal Picks': [3, 4],
        '% Optimal Picks': [0.6, 0.67],
        'Unadjusted Revenue': [900000, 1800000],
    })
    # Many released movies = lots of space
    released_movies_df = pd.DataFrame({
        'Rank': list(range(1, 51)),
        'Title': [f'Movie {i}' for i in range(1, 51)],
        'Drafted By': ['Player 1'] * 50,
        'Revenue': [1000000] * 50,
        'Scored Revenue': [1000000] * 50,
        'Round Drafted': [1] * 50,
        'Overall Pick': list(range(1, 51)),
        'Multiplier': [1.0] * 50,
        'Domestic Revenue': [500000] * 50,
        'Domestic Revenue %': [0.5] * 50,
        'Foreign Revenue': [500000] * 50,
        'Foreign Revenue %': [0.5] * 50,
        'Better Pick': [''] * 50,
        'Better Pick Scored Revenue': [0] * 50,
        'First Seen Date': ['2025-01-01'] * 50,
        'Still In Theaters': ['Yes'] * 50,
    })
    worst_picks_df = pd.DataFrame({
        'Rank': [1, 2, 3],
        'Title': ['Bad Movie 1', 'Bad Movie 2', 'Bad Movie 3'],
        'Drafted By': ['Player 1', 'Player 2', 'Player 1'],
        'Overall Pick': [3, 4, 5],
        'Number of Better Picks': [2, 3, 4],
        'Missed Revenue': [500000, 600000, 700000],
    })
    best_picks_df = pd.DataFrame({
        'Rank': [1, 2, 3],
        'Title': ['Good Movie 1', 'Good Movie 2', 'Good Movie 3'],
        'Drafted By': ['Player 2', 'Player 1', 'Player 2'],
        'Overall Pick': [4, 5, 6],
        'Positions Gained': [3, 2, 4],
        'Actual Revenue': [1500000, 1600000, 1700000],
    })

    def mock_table_to_df(config, table_name, columns=None):
        if table_name == 'dashboards.scoreboard':
            return scoreboard_df
        elif table_name == 'combined.base_query':
            return released_movies_df
        elif table_name == 'dashboards.worst_picks':
            return worst_picks_df
        elif table_name == 'dashboards.best_picks':
            return best_picks_df
        return pd.DataFrame()

    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch('src.sheets.tabs.dashboard.table_to_df', side_effect=mock_table_to_df):
        from src.sheets.tabs.dashboard import DashboardWorksheet

        worksheet = DashboardWorksheet()
        assets = worksheet.generate(config, context)

    # Should have 4 assets: scoreboard, released movies, worst picks, best picks
    assert len(assets) == 4
    assert context['add_both_picks_tables'] is True


def test_dashboard_worksheet_generate_attaches_post_write_hooks_per_asset():
    """Post-write hooks are attached to each asset."""
    scoreboard_df = pd.DataFrame({
        'Name': ['Player 1'],
        'Scored Revenue': [1000000],
        '# Released': [5],
        '# Optimal Picks': [3],
        '% Optimal Picks': [0.6],
        'Unadjusted Revenue': [900000],
    })
    released_movies_df = pd.DataFrame({
        'Rank': [1],
        'Title': ['Movie A'],
        'Drafted By': ['Player 1'],
        'Revenue': [1000000],
        'Scored Revenue': [1000000],
        'Round Drafted': [1],
        'Overall Pick': [1],
        'Multiplier': [1.0],
        'Domestic Revenue': [500000],
        'Domestic Revenue %': [0.5],
        'Foreign Revenue': [500000],
        'Foreign Revenue %': [0.5],
        'Better Pick': [''],
        'Better Pick Scored Revenue': [0],
        'First Seen Date': ['2025-01-01'],
        'Still In Theaters': ['Yes'],
    })
    worst_picks_df = pd.DataFrame({
        'Rank': [],
        'Title': [],
        'Drafted By': [],
        'Overall Pick': [],
        'Number of Better Picks': [],
        'Missed Revenue': [],
    })
    best_picks_df = pd.DataFrame({
        'Rank': [],
        'Title': [],
        'Drafted By': [],
        'Overall Pick': [],
        'Positions Gained': [],
        'Actual Revenue': [],
    })

    def mock_table_to_df(config, table_name, columns=None):
        if table_name == 'dashboards.scoreboard':
            return scoreboard_df
        elif table_name == 'combined.base_query':
            return released_movies_df
        elif table_name == 'dashboards.worst_picks':
            return worst_picks_df
        elif table_name == 'dashboards.best_picks':
            return best_picks_df
        return pd.DataFrame()

    config_dict = make_config_dict(update_type='s3')
    config = {'config_dict': config_dict}
    context = {}

    with patch('src.sheets.tabs.dashboard.table_to_df', side_effect=mock_table_to_df):
        from src.sheets.tabs.dashboard import DashboardWorksheet

        worksheet = DashboardWorksheet()
        assets = worksheet.generate(config, context)

    # Scoreboard asset should have 3 hooks (title, header, formatting)
    scoreboard_asset = assets[0]
    assert len(scoreboard_asset.post_write_hooks) == 3

    # Released movies asset should have 6 hooks (title, header, formatting, conditional_format, clear zeros, timestamp)
    released_movies_asset = assets[1]
    assert len(released_movies_asset.post_write_hooks) == 6


def test_apply_scoreboard_title_writes_dashboard_name():
    """Dashboard name is written to cell B2 and cells are merged."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='B4'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={'dashboard_name': 'My Test Dashboard'},
    )

    worksheet = DashboardWorksheet()
    worksheet._apply_scoreboard_title(ctx)

    write_calls = mock_ws.write_values.call_args_list
    b2_call = [c for c in write_calls if c[0][0].cell == 'B2']

    assert len(b2_call) == 1
    assert b2_call[0][0][1] == [['My Test Dashboard']]
    # merge_cells is called with a CellRange object
    merge_call = mock_ws.merge_cells.call_args[0][0]
    assert merge_call.value == 'B2:F2'


def test_apply_released_movies_title_writes_title():
    """Released Movies title is written to cell I2 and cells are merged."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='I4'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={},
    )

    worksheet = DashboardWorksheet()
    worksheet._apply_released_movies_title(ctx)

    write_calls = mock_ws.write_values.call_args_list
    i2_call = [c for c in write_calls if c[0][0].cell == 'I2']

    assert len(i2_call) == 1
    assert i2_call[0][0][1] == [['Released Movies']]
    # merge_cells is called with a CellRange object
    merge_call = mock_ws.merge_cells.call_args[0][0]
    assert merge_call.value == 'I2:X2'


def test_apply_worst_picks_title_writes_title():
    """Worst Picks title is written to correct row and cells are merged."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='B12'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={},
    )

    worksheet = DashboardWorksheet()
    worksheet._apply_worst_picks_title(ctx)

    write_calls = mock_ws.write_values.call_args_list
    # CellLocation uses offset_rows=-1, so .value gives the computed cell
    title_call = [c for c in write_calls if c[0][0].value == 'B11']

    assert len(title_call) == 1
    assert title_call[0][0][1] == [['Worst Picks']]
    # merge_cells is called with a CellRange object
    merge_call = mock_ws.merge_cells.call_args[0][0]
    assert merge_call.value == 'B11:G11'


def test_apply_best_picks_title_writes_title():
    """Best Picks title is written to correct row and cells are merged."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='B20'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={},
    )

    worksheet = DashboardWorksheet()
    worksheet._apply_best_picks_title(ctx)

    write_calls = mock_ws.write_values.call_args_list
    # CellLocation uses offset_rows=-1, so .value gives the computed cell
    title_call = [c for c in write_calls if c[0][0].value == 'B19']

    assert len(title_call) == 1
    assert title_call[0][0][1] == [['Best Picks']]
    # merge_cells is called with a CellRange object
    merge_call = mock_ws.merge_cells.call_args[0][0]
    assert merge_call.value == 'B19:G19'


def test_apply_scoreboard_header_formats_header_row():
    """Scoreboard header row is formatted at B4:G4."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import HEADER_FORMAT, DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='B4'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={},
    )

    worksheet = DashboardWorksheet()
    worksheet._apply_scoreboard_header(ctx)

    # format_range is called with a CellRange object
    format_call = mock_ws.format_range.call_args[0][0]
    assert format_call.value == 'B4:G4'
    assert mock_ws.format_range.call_args[0][1] == HEADER_FORMAT


def test_apply_released_movies_header_formats_header_row():
    """Released movies header row is formatted at I4:X4."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import HEADER_FORMAT, DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='I4'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={},
    )

    worksheet = DashboardWorksheet()
    worksheet._apply_released_movies_header(ctx)

    # format_range is called with a CellRange object
    format_call = mock_ws.format_range.call_args[0][0]
    assert format_call.value == 'I4:X4'
    assert mock_ws.format_range.call_args[0][1] == HEADER_FORMAT


def test_dashboard_worksheet_get_formatting_single_picks_table():
    """get_formatting returns empty merge_ranges regardless of picks table count."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    worksheet = DashboardWorksheet()
    context = {
        'sheet_height': 50,
        'add_picks_table': True,
        'add_both_picks_tables': False,
        'picks_row_num': 12,
    }

    formatting = worksheet.get_formatting(context)

    # Merge ranges are handled by post-write hooks, not WorksheetFormatting
    assert formatting.merge_ranges == []


def test_clear_zero_values_clears_dollar_zero():
    """$0 values in Better Pick Scored Revenue column are cleared."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='I4'),
    )
    # Create released_movies_df with some zero values in Better Pick Scored Revenue
    released_movies_df = pd.DataFrame({
        'Better Pick Scored Revenue': [100, 0, 200, 0, 300],
    })
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={'released_movies_df': released_movies_df},
    )

    worksheet = DashboardWorksheet()
    worksheet._clear_zero_values(ctx)

    # Should clear cells at indices 1 and 3 (V6 and V8)
    write_calls = mock_ws.write_values.call_args_list
    cleared_cells = [c[0][0].value for c in write_calls]

    assert len(cleared_cells) == 2
    assert 'V6' in cleared_cells  # df_idx 1 -> V5 + offset 1 = V6
    assert 'V8' in cleared_cells  # df_idx 3 -> V5 + offset 3 = V8


def test_write_timestamp_metadata_writes_to_g2():
    """Timestamp metadata is written to cell G2."""
    import numpy as np
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='I4'),
    )

    config_dict = make_config_dict(update_type='s3')
    released_movies_df = pd.DataFrame({'Still In Theaters': ['Yes']})

    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={
            'config_dict': config_dict,
            'released_movies_df': released_movies_df,
            'year': 2025,
        },
    )

    mock_db = MagicMock()
    mock_result = MagicMock()
    # Use numpy datetime64 since .item() is called on it
    mock_result.fetchnumpy.return_value = {
        'published_timestamp_utc': np.array(['2025-01-15T12:00:00'], dtype='datetime64[s]')
    }
    mock_db.connection.query.return_value = mock_result

    with patch('src.sheets.tabs.dashboard.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        worksheet = DashboardWorksheet()
        worksheet._write_timestamp_metadata(ctx)

    write_calls = mock_ws.write_values.call_args_list
    g2_call = [c for c in write_calls if c[0][0].cell == 'G2']

    assert len(g2_call) == 1
    assert 'Dashboard Last Updated' in g2_call[0][0][1][0][0]


def test_write_timestamp_metadata_includes_done_message_when_complete():
    """Timestamp includes 'done updating' message when all movies done and year passed."""
    import numpy as np
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='I4'),
    )

    config_dict = make_config_dict(update_type='s3')
    # All movies have "Still In Theaters" = "No" and year is in the past
    released_movies_df = pd.DataFrame({'Still In Theaters': ['No', 'No', 'No']})

    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={
            'config_dict': config_dict,
            'released_movies_df': released_movies_df,
            'year': 2020,  # Past year to trigger "done updating" message
        },
    )

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchnumpy.return_value = {
        'published_timestamp_utc': np.array(['2025-01-15T12:00:00'], dtype='datetime64[s]')
    }
    mock_db.connection.query.return_value = mock_result

    with patch('src.sheets.tabs.dashboard.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        worksheet = DashboardWorksheet()
        worksheet._write_timestamp_metadata(ctx)

    write_calls = mock_ws.write_values.call_args_list
    g2_call = [c for c in write_calls if c[0][0].cell == 'G2']

    assert len(g2_call) == 1
    assert 'Dashboard is done updating' in g2_call[0][0][1][0][0]


def test_write_timestamp_metadata_returns_early_without_config():
    """_write_timestamp_metadata returns early when config_dict is None."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({'col': [1]}),
        location=CellLocation(cell='I4'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={},  # No config_dict
    )

    worksheet = DashboardWorksheet()
    worksheet._write_timestamp_metadata(ctx)

    mock_ws.write_values.assert_not_called()


def test_apply_worst_picks_header_formats_header_row():
    """Worst picks header row is formatted based on asset location and columns."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({
            'Rank': [1],
            'Title': ['Movie'],
            'Drafted By': ['Player'],
            'Overall Pick': [1],
            'Number of Better Picks': [2],
            'Missed Revenue': [100000],
        }),
        location=CellLocation(cell='B12'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={},
    )

    worksheet = DashboardWorksheet()
    worksheet._apply_worst_picks_header(ctx)

    # format_range is called with a CellRange object
    format_call = mock_ws.format_range.call_args[0][0]
    assert format_call.value == 'B12:G12'


def test_apply_best_picks_header_formats_header_row():
    """Best picks header row is formatted based on asset location and columns."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({
            'Rank': [1],
            'Title': ['Movie'],
            'Drafted By': ['Player'],
            'Overall Pick': [1],
            'Positions Gained': [3],
            'Actual Revenue': [1500000],
        }),
        location=CellLocation(cell='B20'),
    )
    ctx = HookContext(
        worksheet=mock_ws,
        asset=mock_asset,
        worksheet_name='Dashboard',
        runner_context={},
    )

    worksheet = DashboardWorksheet()
    worksheet._apply_best_picks_header(ctx)

    # format_range is called with a CellRange object
    format_call = mock_ws.format_range.call_args[0][0]
    assert format_call.value == 'B20:G20'
