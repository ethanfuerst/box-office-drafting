"""Tests for DashboardWorksheet definition."""

import logging
from unittest.mock import MagicMock, patch

import numpy as np
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
    """get_formatting returns WorksheetFormatting with notes, merges, and column widths."""
    from eftoolkit.gsheets.runner.types import WorksheetFormatting

    from src.sheets.tabs.dashboard import DASHBOARD_NOTES, DashboardWorksheet

    worksheet = DashboardWorksheet()
    context = {
        'sheet_height': 50,
        'add_picks_table': False,
    }

    formatting = worksheet.get_formatting(context)

    assert isinstance(formatting, WorksheetFormatting)
    assert formatting.notes == DASHBOARD_NOTES
    assert 'B2:F2' in formatting.merge_ranges
    assert 'I2:X2' in formatting.merge_ranges
    assert formatting.column_widths['A'] == 25
    assert formatting.auto_resize_columns == (1, 23)


def test_dashboard_worksheet_get_formatting_includes_picks_merges():
    """get_formatting includes merge ranges for picks tables when present."""
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

    assert 'B11:G11' in formatting.merge_ranges  # Worst Picks title row
    assert 'B19:G19' in formatting.merge_ranges  # Best Picks title row


def test_dashboard_worksheet_get_formatting_conditional_format():
    """get_formatting includes conditional formatting for Still In Theaters column."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    worksheet = DashboardWorksheet()
    context = {'sheet_height': 50, 'add_picks_table': False}

    formatting = worksheet.get_formatting(context)

    assert len(formatting.conditional_formats) == 1
    cond_format = formatting.conditional_formats[0]
    assert cond_format['range'] == 'X5:X50'
    assert cond_format['type'] == 'TEXT_EQ'
    assert cond_format['values'] == ['Yes']


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

    # Scoreboard asset should have 2 hooks (title, header)
    scoreboard_asset = assets[0]
    assert len(scoreboard_asset.post_write_hooks) == 2

    # Released movies asset should have 5 hooks (title, header, clear zeros, timestamp, diagnostics)
    released_movies_asset = assets[1]
    assert len(released_movies_asset.post_write_hooks) == 5


def test_apply_scoreboard_title_writes_dashboard_name():
    """Dashboard name is written to cell B2."""
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


def test_apply_released_movies_title_writes_title():
    """Released Movies title is written to cell I2."""
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


def test_apply_worst_picks_title_writes_title():
    """Worst Picks title is written to correct row based on asset location."""
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
    title_call = [c for c in write_calls if c[0][0].cell == 'B11']

    assert len(title_call) == 1
    assert title_call[0][0][1] == [['Worst Picks']]


def test_apply_best_picks_title_writes_title():
    """Best Picks title is written to correct row based on asset location."""
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
    title_call = [c for c in write_calls if c[0][0].cell == 'B19']

    assert len(title_call) == 1
    assert title_call[0][0][1] == [['Best Picks']]


def test_apply_scoreboard_header_formats_header_row():
    """Scoreboard header row is formatted based on asset location and columns."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    # Scoreboard has 6 columns (B through G)
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({
            'Name': ['Player 1'],
            'Scored Revenue': [1000000],
            '# Released': [5],
            '# Optimal Picks': [3],
            '% Optimal Picks': [0.6],
            'Unadjusted Revenue': [900000],
        }),
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

    format_calls = mock_ws.format_range.call_args_list
    ranges = [c[0][0].value for c in format_calls]

    assert 'B4:G4' in ranges


def test_apply_released_movies_header_formats_header_row():
    """Released movies header row is formatted based on asset location and columns."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    # Released movies has 16 columns (I through X)
    mock_asset = WorksheetAsset(
        df=pd.DataFrame({
            'Rank': [1],
            'Title': ['Movie'],
            'Drafted By': ['Player'],
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
        }),
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

    format_calls = mock_ws.format_range.call_args_list
    ranges = [c[0][0].value for c in format_calls]

    assert 'I4:X4' in ranges


def test_log_missing_movies_logs_movies_not_in_scoreboard(caplog):
    """Movies drafted but not in scoreboard are logged."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    config_dict = make_config_dict(update_type='s3')
    context = {
        'config_dict': config_dict,
        'released_movies_df': pd.DataFrame({
            'Title': ['Movie A', 'Movie B'],
        }),
    }

    draft_df = pd.DataFrame({'movie': ['Movie A', 'Movie B', 'Movie C']})

    with patch('src.sheets.tabs.dashboard.table_to_df', return_value=draft_df):
        with caplog.at_level(logging.INFO):
            worksheet = DashboardWorksheet()
            worksheet._log_missing_movies(context)

    assert 'Movie C' in caplog.text


def test_log_missing_movies_logs_success_when_all_movies_present(caplog):
    """Success message logged when all drafted movies are in scoreboard."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    config_dict = make_config_dict(update_type='s3')
    context = {
        'config_dict': config_dict,
        'released_movies_df': pd.DataFrame({
            'Title': ['Movie A', 'Movie B'],
        }),
    }

    draft_df = pd.DataFrame({'movie': ['Movie A', 'Movie B']})

    with patch('src.sheets.tabs.dashboard.table_to_df', return_value=draft_df):
        with caplog.at_level(logging.INFO):
            worksheet = DashboardWorksheet()
            worksheet._log_missing_movies(context)

    assert 'All movies are on the scoreboard' in caplog.text


def test_log_min_revenue_info_logs_minimum_revenue(caplog):
    """Minimum revenue of most recent data is logged."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    config_dict = make_config_dict(update_type='s3')
    context = {'config_dict': config_dict, 'year': 2025}

    mock_db = MagicMock()
    mock_result1 = MagicMock()
    mock_result1.fetchnumpy.return_value = {'revenue': np.array([1000000])}
    mock_result2 = MagicMock()
    mock_result2.fetchnumpy.return_value = {'title': np.array(['Low Revenue Movie'])}
    mock_db.connection.query.side_effect = [mock_result1, mock_result2]

    with patch('src.sheets.tabs.dashboard.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        with caplog.at_level(logging.INFO):
            worksheet = DashboardWorksheet()
            worksheet._log_min_revenue_info(context)

    assert 'Minimum revenue' in caplog.text


def test_log_min_revenue_info_handles_no_revenue_data(caplog):
    """Handles case when no revenue data is found."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    config_dict = make_config_dict(update_type='s3')
    context = {'config_dict': config_dict, 'year': 2025}

    mock_db = MagicMock()
    mock_result = MagicMock()
    mock_result.fetchnumpy.return_value = {'revenue': np.array([])}
    mock_db.connection.query.return_value = mock_result

    with patch('src.sheets.tabs.dashboard.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        with caplog.at_level(logging.INFO):
            worksheet = DashboardWorksheet()
            worksheet._log_min_revenue_info(context)

    assert 'No revenue data found' in caplog.text


def test_dashboard_worksheet_get_formatting_single_picks_table():
    """get_formatting includes merge range for worst picks only when no space for both."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    worksheet = DashboardWorksheet()
    context = {
        'sheet_height': 50,
        'add_picks_table': True,
        'add_both_picks_tables': False,
        'picks_row_num': 12,
    }

    formatting = worksheet.get_formatting(context)

    assert 'B11:G11' in formatting.merge_ranges  # Worst Picks title row only


def test_clear_zero_values_clears_dollar_zero():
    """$0 values in Better Pick Scored Revenue column are cleared."""
    from eftoolkit.gsheets.runner.types import CellLocation, HookContext, WorksheetAsset

    from src.sheets.tabs.dashboard import DashboardWorksheet

    mock_ws = MagicMock()
    # Create a DataFrame with enough rows for the loop (starts at index 4)
    # The loop checks indices 4, 5, 6, 7 etc.
    mock_ws.read.return_value = pd.DataFrame({
        'V': ['Header', '$100', '$200', '$300', '$0', '$500', '$0', '$700'],
    })
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
    worksheet._clear_zero_values(ctx)

    # Should clear cells at indices 4 and 6 (rows 5 and 7)
    write_calls = mock_ws.write_values.call_args_list
    cleared_cells = [c[0][0].cell for c in write_calls]
    assert 'V5' in cleared_cells  # Index 4 -> row 5
    assert 'V7' in cleared_cells  # Index 6 -> row 7


def test_write_timestamp_metadata_writes_to_g2():
    """Timestamp metadata is written to cell G2."""
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


def test_log_diagnostics_calls_both_helpers():
    """_log_diagnostics calls both _log_missing_movies and _log_min_revenue_info."""
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

    with patch.object(worksheet, '_log_missing_movies') as mock_missing:
        with patch.object(worksheet, '_log_min_revenue_info') as mock_min_rev:
            worksheet._log_diagnostics(ctx)

    mock_missing.assert_called_once_with(ctx.runner_context)
    mock_min_rev.assert_called_once_with(ctx.runner_context)


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

    format_calls = mock_ws.format_range.call_args_list
    ranges = [c[0][0].value for c in format_calls]

    assert 'B12:G12' in ranges


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

    format_calls = mock_ws.format_range.call_args_list
    ranges = [c[0][0].value for c in format_calls]

    assert 'B20:G20' in ranges


def test_log_missing_movies_returns_early_without_config():
    """_log_missing_movies returns early when config_dict is None."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    context = {'released_movies_df': pd.DataFrame({'Title': ['Movie A']})}

    worksheet = DashboardWorksheet()

    with patch('src.sheets.tabs.dashboard.table_to_df') as mock_table_to_df:
        worksheet._log_missing_movies(context)

    mock_table_to_df.assert_not_called()


def test_log_min_revenue_info_returns_early_without_config():
    """_log_min_revenue_info returns early when config_dict is None."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    context = {'year': 2025}  # No config_dict

    worksheet = DashboardWorksheet()

    with patch('src.sheets.tabs.dashboard.get_duckdb') as mock_get_duckdb:
        worksheet._log_min_revenue_info(context)

    mock_get_duckdb.assert_not_called()


def test_log_min_revenue_info_logs_all_movies_above_minimum(caplog):
    """Success message logged when all movies are above minimum revenue."""
    from src.sheets.tabs.dashboard import DashboardWorksheet

    config_dict = make_config_dict(update_type='s3')
    context = {'config_dict': config_dict, 'year': 2025}

    mock_db = MagicMock()
    mock_result1 = MagicMock()
    mock_result1.fetchnumpy.return_value = {'revenue': np.array([1000000])}
    mock_result2 = MagicMock()
    mock_result2.fetchnumpy.return_value = {'title': np.array([])}  # No movies under min
    mock_db.connection.query.side_effect = [mock_result1, mock_result2]

    with patch('src.sheets.tabs.dashboard.get_duckdb') as mock_get_duckdb:
        mock_get_duckdb.return_value.__enter__.return_value = mock_db
        mock_get_duckdb.return_value.__exit__.return_value = None

        with caplog.at_level(logging.INFO):
            worksheet = DashboardWorksheet()
            worksheet._log_min_revenue_info(context)

    assert 'All movies are above the minimum revenue' in caplog.text
