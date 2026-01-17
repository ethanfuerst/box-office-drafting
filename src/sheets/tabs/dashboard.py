"""Dashboard worksheet definition.

This module implements the WorksheetDefinition protocol for the main dashboard
that displays scoreboard, released movies, and picks tables.

The DashboardWorksheet class generates data and applies post-write formatting
via hooks that receive context with the worksheet reference.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from eftoolkit.gsheets.runner.types import (
    CellLocation,
    CellRange,
    HookContext,
    WorksheetAsset,
    WorksheetFormatting,
)

from src.utils.config import ConfigDict
from src.utils.db_connection import get_duckdb
from src.utils.query import table_to_df

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

DASHBOARD_NOTES = {
    CellLocation(cell='U4'): 'A movie is considered a better pick if it was drafted after by a different drafter and made more revenue (adjusted for multiplier).',
    CellLocation(cell='W4'): 'The first date a movie was seen in the database.',
    CellLocation(cell='X4'): 'A movie is considered still in theaters if the first record is within the last week or the revenue has changed in the last week.',
}

TITLE_FORMAT = {'horizontalAlignment': 'CENTER', 'textFormat': {'fontSize': 20, 'bold': True}}
PICKS_TITLE_FORMAT = {'horizontalAlignment': 'CENTER', 'textFormat': {'bold': True}}
HEADER_FORMAT = {'horizontalAlignment': 'CENTER', 'textFormat': {'fontSize': 10, 'bold': True}}

CURRENCY_FORMAT = {'numberFormat': {'type': 'CURRENCY', 'pattern': '$#,##0'}}
PERCENT_FORMAT = {'numberFormat': {'type': 'PERCENT', 'pattern': '#0.0#%'}}
LEFT_ALIGN = {'horizontalAlignment': 'LEFT'}
RIGHT_ALIGN = {'horizontalAlignment': 'RIGHT'}
CENTER_ALIGN = {'horizontalAlignment': 'CENTER'}

COLUMN_WIDTHS = {
    'A': 25,   # Spacer
    'B': 80,   # Name in Dashboard and Rank in Worst/Best Pick
    'C': 284,  # Scored Revenue in Dashboard and Title in Worst/Best Pick
    'D': 84,   # Num Released in Dashboard and Drafted by in Worst/Best Pick
    'E': 116,  # Num Optimal Picks in Dashboard and Overall Pick in Worst/Best Pick
    'F': 168,  # % Optimal Picks in Dashboard and Num Better Picks/Positions Gained
    'G': 164,  # Dashboard Log and Unadjusted Revenue and Missed/Actual Revenue
    'H': 25,   # Spacer
    'I': 42,   # Rank in Released Movies
    'J': 284,  # Title in Released Movies
    'K': 80,   # Drafted by in Released Movies
    'L': 120,  # Revenue in Released Movies
    'M': 120,  # Scored Revenue in Released Movies
    'N': 106,  # Round Drafted in Released Movies
    'O': 88,   # Overall Pick in Released Movies
    'P': 72,   # Multiplier in Released Movies
    'Q': 135,  # Domestic Revenue in Released Movies
    'R': 142,  # Domestic Revenue % in Released Movies
    'S': 120,  # Foreign Revenue in Released Movies
    'T': 136,  # Foreign Revenue % in Released Movies
    'U': 284,  # Better Pick in Released Movies
    'V': 200,  # Better Pick Scored Revenue in Released Movies
    'W': 104,  # First Seen Date in Released Movies
    'X': 106,  # Still In Theaters in Released Movies
    'Y': 25,   # Spacer
}


def calculate_picks_table_layout(
    scoreboard_length: int,
    released_movies_length: int,
    worst_picks_length: int,
    best_picks_length: int,
) -> dict:
    """
    Calculate the layout for picks tables based on available space.

    Args:
        scoreboard_length: Number of rows in scoreboard (not including header)
        released_movies_length: Number of rows in released movies (not including header)
        worst_picks_length: Number of rows in worst picks data (not including header)
        best_picks_length: Number of rows in best picks data (not including header)

    Returns:
        dict with layout information including row numbers and heights
    """
    available_height = released_movies_length - scoreboard_length - 3
    picks_row_num = 5 + scoreboard_length + 2
    add_both_picks_tables = False
    best_picks_row_num = None
    worst_picks_height = 0
    best_picks_height = 0

    min_rows_per_table = 2
    separator_rows = 2
    total_required = min_rows_per_table * 2 + separator_rows

    if (
        available_height >= total_required
        and worst_picks_length > 1
        and best_picks_length > 1
    ):
        add_both_picks_tables = True
        usable_height = available_height - 2 - separator_rows
        height_per_table = usable_height // 2
        worst_picks_height = min(height_per_table, worst_picks_length)
        best_picks_row_num = picks_row_num + 1 + worst_picks_height + separator_rows
        best_picks_height = min(usable_height - worst_picks_height, best_picks_length)
    else:
        if available_height > 0 and worst_picks_length > 1:
            worst_picks_height = min(available_height, worst_picks_length)

    return {
        'available_height': available_height,
        'add_both_picks_tables': add_both_picks_tables,
        'worst_picks_row_num': picks_row_num,
        'worst_picks_height': worst_picks_height,
        'best_picks_row_num': best_picks_row_num,
        'best_picks_height': best_picks_height,
    }


class DashboardWorksheet:
    """Worksheet definition for the main dashboard.

    Generates all dashboard content: scoreboard, released movies, and picks tables.
    Post-write hooks handle operations that cannot be expressed via WorksheetFormatting
    (writing cell values, header formatting, timestamps, diagnostics).
    """

    @property
    def name(self) -> str:
        """The worksheet name in the spreadsheet."""
        return 'Dashboard'

    def generate(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> list[WorksheetAsset]:
        """Generate all dashboard assets.

        Args:
            config: Configuration dictionary containing 'config_dict' key with ConfigDict.
            context: Runtime context (populated with data for dependent processing).

        Returns:
            List of WorksheetAssets for scoreboard, released movies, and picks tables.
        """
        config_dict: ConfigDict = config['config_dict']
        assets = []

        released_movies_df = table_to_df(
            config_dict,
            'combined.base_query',
            columns=[
                'Rank',
                'Title',
                'Drafted By',
                'Revenue',
                'Scored Revenue',
                'Round Drafted',
                'Overall Pick',
                'Multiplier',
                'Domestic Revenue',
                'Domestic Revenue %',
                'Foreign Revenue',
                'Foreign Revenue %',
                'Better Pick',
                'Better Pick Scored Revenue',
                'First Seen Date',
                'Still In Theaters',
            ],
        )

        scoreboard_df = table_to_df(
            config_dict,
            'dashboards.scoreboard',
            columns=[
                'Name',
                'Scored Revenue',
                '# Released',
                '# Optimal Picks',
                '% Optimal Picks',
                'Unadjusted Revenue',
            ],
        )

        worst_picks_df = table_to_df(
            config_dict,
            'dashboards.worst_picks',
            columns=[
                'Rank',
                'Title',
                'Drafted By',
                'Overall Pick',
                'Number of Better Picks',
                'Missed Revenue',
            ],
        )

        best_picks_df = table_to_df(
            config_dict,
            'dashboards.best_picks',
            columns=[
                'Rank',
                'Title',
                'Drafted By',
                'Overall Pick',
                'Positions Gained',
                'Actual Revenue',
            ],
        )

        layout = calculate_picks_table_layout(
            scoreboard_length=len(scoreboard_df),
            released_movies_length=len(released_movies_df),
            worst_picks_length=len(worst_picks_df),
            best_picks_length=len(best_picks_df),
        )

        context['released_movies_df'] = released_movies_df
        context['scoreboard_df'] = scoreboard_df
        context['layout'] = layout
        context['year'] = config_dict['year']
        context['dashboard_name'] = config_dict['name']
        context['sheet_height'] = len(released_movies_df) + 5
        context['config_dict'] = config_dict

        add_picks_table = layout['worst_picks_height'] > 0 and len(worst_picks_df) > 1
        context['add_picks_table'] = add_picks_table
        context['add_both_picks_tables'] = layout['add_both_picks_tables']
        context['picks_row_num'] = layout['worst_picks_row_num']
        context['worst_picks_height'] = layout['worst_picks_height']
        context['best_picks_row_num'] = layout['best_picks_row_num']
        context['best_picks_height'] = layout['best_picks_height']

        assets.append(
            WorksheetAsset(
                df=scoreboard_df,
                location=CellLocation(cell='B4'),
                post_write_hooks=[
                    self._apply_scoreboard_title,
                    self._apply_scoreboard_header,
                    self._apply_scoreboard_formatting,
                ],
            )
        )

        assets.append(
            WorksheetAsset(
                df=released_movies_df,
                location=CellLocation(cell='I4'),
                post_write_hooks=[
                    self._apply_released_movies_title,
                    self._apply_released_movies_header,
                    self._apply_released_movies_formatting,
                    self._apply_still_in_theaters_conditional_format,
                    self._clear_zero_values,
                    self._write_timestamp_metadata,
                ],
            )
        )

        if add_picks_table:
            worst_picks_df = worst_picks_df.head(layout['worst_picks_height'])
            assets.append(
                WorksheetAsset(
                    df=worst_picks_df,
                    location=CellLocation(cell=f"B{layout['worst_picks_row_num']}"),
                    post_write_hooks=[
                        self._apply_worst_picks_title,
                        self._apply_worst_picks_header,
                        self._apply_worst_picks_formatting,
                    ],
                )
            )

            if layout['add_both_picks_tables']:
                best_picks_df = best_picks_df.head(layout['best_picks_height'])
                assets.append(
                    WorksheetAsset(
                        df=best_picks_df,
                        location=CellLocation(cell=f"B{layout['best_picks_row_num']}"),
                        post_write_hooks=[
                            self._apply_best_picks_title,
                            self._apply_best_picks_header,
                            self._apply_best_picks_formatting,
                        ],
                    )
                )
                logging.info(
                    f"Showing both picks tables: worst_picks ({layout['worst_picks_height']} rows) "
                    f"and best_picks ({layout['best_picks_height']} rows)"
                )

        return assets

    def get_formatting(self, context: dict[str, Any]) -> WorksheetFormatting | None:  # noqa: ARG002
        """Return worksheet-level formatting configuration.

        This method returns sheet-wide formatting (notes, column widths).
        Cell-level and conditional formatting is handled by per-asset post-write hooks.
        """
        return WorksheetFormatting(notes=DASHBOARD_NOTES, column_widths=COLUMN_WIDTHS)

    # Scoreboard hooks
    def _apply_scoreboard_title(self, ctx: HookContext) -> None:
        """Write dashboard title to cell B2 and merge B2:F2."""
        dashboard_name = ctx.runner_context.get('dashboard_name', '')
        title_cell = CellLocation(cell='B2')
        merge_range = CellRange.from_string('B2:F2')
        ctx.worksheet.write_values(title_cell, [[dashboard_name]])
        ctx.worksheet.merge_cells(merge_range)
        ctx.worksheet.format_range(title_cell, TITLE_FORMAT)

    def _apply_scoreboard_header(self, ctx: HookContext) -> None:
        """Apply header formatting to scoreboard header row (B4:G4)."""
        header_range = CellRange.from_string('B4:G4')
        ctx.worksheet.format_range(header_range, HEADER_FORMAT)

    def _apply_scoreboard_formatting(self, ctx: HookContext) -> None:
        """Apply cell-level formatting to scoreboard data rows."""
        scoreboard_df = ctx.runner_context.get('scoreboard_df')
        if scoreboard_df is None:
            return
        end_row = 4 + len(scoreboard_df)
        ctx.worksheet.format_range(f'B5:B{end_row}', LEFT_ALIGN)  # Name
        ctx.worksheet.format_range(f'C5:C{end_row}', {**RIGHT_ALIGN, **CURRENCY_FORMAT})  # Scored Revenue
        ctx.worksheet.format_range(f'F5:F{end_row}', {**RIGHT_ALIGN, **PERCENT_FORMAT})  # % Optimal Picks
        ctx.worksheet.format_range(f'G5:G{end_row}', {**RIGHT_ALIGN, **CURRENCY_FORMAT})  # Unadjusted Revenue

    def _apply_released_movies_title(self, ctx: HookContext) -> None:
        """Write Released Movies title to cell I2 and merge I2:X2."""
        title_cell = CellLocation(cell='I2')
        merge_range = CellRange.from_string('I2:X2')
        ctx.worksheet.write_values(title_cell, [['Released Movies']])
        ctx.worksheet.merge_cells(merge_range)
        ctx.worksheet.format_range(title_cell, TITLE_FORMAT)

    def _apply_released_movies_header(self, ctx: HookContext) -> None:
        """Apply header formatting to released movies header row (I4:X4)."""
        header_range = CellRange.from_string('I4:X4')
        ctx.worksheet.format_range(header_range, HEADER_FORMAT)

    def _apply_released_movies_formatting(self, ctx: HookContext) -> None:
        """Apply cell-level formatting to released movies data rows."""
        sheet_height = ctx.runner_context.get('sheet_height')
        ctx.worksheet.format_range(f'I5:K{sheet_height}', LEFT_ALIGN)  # Rank to Drafted By
        ctx.worksheet.format_range(f'L5:M{sheet_height}', {**LEFT_ALIGN, **CURRENCY_FORMAT})  # Revenue, Scored Revenue
        ctx.worksheet.format_range(f'N5:P{sheet_height}', RIGHT_ALIGN)  # Round Drafted to Multiplier
        ctx.worksheet.format_range(f'Q5:Q{sheet_height}', {**RIGHT_ALIGN, **CURRENCY_FORMAT})  # Domestic Revenue
        ctx.worksheet.format_range(f'R5:R{sheet_height}', {**RIGHT_ALIGN, **PERCENT_FORMAT})  # Domestic Revenue %
        ctx.worksheet.format_range(f'S5:S{sheet_height}', {**RIGHT_ALIGN, **CURRENCY_FORMAT})  # Foreign Revenue
        ctx.worksheet.format_range(f'T5:T{sheet_height}', {**RIGHT_ALIGN, **PERCENT_FORMAT})  # Foreign Revenue %
        ctx.worksheet.format_range(f'V5:V{sheet_height}', {**RIGHT_ALIGN, **CURRENCY_FORMAT})  # Better Pick Scored Revenue
        ctx.worksheet.format_range(f'W5:W{sheet_height}', RIGHT_ALIGN)  # First Seen Date
        ctx.worksheet.format_range(f'X5:X{sheet_height}', CENTER_ALIGN)  # Still In Theaters

    def _apply_still_in_theaters_conditional_format(self, ctx: HookContext) -> None:
        """Apply conditional formatting to Still In Theaters column (X)."""
        sheet_height = ctx.runner_context.get('sheet_height')
        ctx.worksheet.add_conditional_format(
            range_name=f'X5:X{sheet_height}',
            rule={
                'type': 'TEXT_EQ',
                'values': ['Yes'],
                'format': {'backgroundColor': {'red': 0, 'green': 0.9, 'blue': 0}},
            },
        )

    def _clear_zero_values(self, ctx: HookContext) -> None:
        """Clear $0 values in Better Pick Scored Revenue column."""
        released_movies_df = ctx.runner_context.get('released_movies_df')
        if released_movies_df is None or released_movies_df.empty:
            return
        col_name = 'Better Pick Scored Revenue'
        if col_name not in released_movies_df.columns:
            return
        for df_idx, value in enumerate(released_movies_df[col_name]):
            if value == 0 or value == 0.0:
                # Data starts at row 5 (V5), df_idx 0 = V5, df_idx 1 = V6, etc.
                cell = CellLocation(cell='V5', offset_rows=df_idx)
                ctx.worksheet.write_values(cell, [['']])


    def _apply_worst_picks_title(self, ctx: HookContext) -> None:
        """Write Worst Picks title above the asset location and merge B:G."""
        loc = ctx.asset.location
        title_cell = CellLocation(cell=loc.cell, offset_rows=-1)
        merge_end = CellLocation(cell=loc.cell, offset_rows=-1, offset_cols=5)
        merge_range = CellRange.from_bounds(
            title_cell.row, title_cell.col, merge_end.row, merge_end.col
        )
        ctx.worksheet.write_values(title_cell, [['Worst Picks']])
        ctx.worksheet.merge_cells(merge_range)
        ctx.worksheet.format_range(title_cell, PICKS_TITLE_FORMAT)

    def _apply_worst_picks_header(self, ctx: HookContext) -> None:
        """Apply header formatting to worst picks header row."""
        loc = ctx.asset.location
        num_cols = len(ctx.asset.df.columns)
        end_cell = CellLocation(cell=loc.cell, offset_cols=num_cols - 1)
        header_range = CellRange.from_bounds(loc.row, loc.col, end_cell.row, end_cell.col)
        ctx.worksheet.format_range(header_range, HEADER_FORMAT)

    def _apply_worst_picks_formatting(self, ctx: HookContext) -> None:
        """Apply cell-level formatting to worst picks data rows."""
        loc = ctx.asset.location
        num_rows = len(ctx.asset.df)
        data_start = loc.row_1indexed + 1  # Skip header row
        data_end = loc.row_1indexed + num_rows
        ctx.worksheet.format_range(f'B{data_start}:B{data_end}', LEFT_ALIGN)  # Rank
        ctx.worksheet.format_range(f'C{data_start}:C{data_end}', LEFT_ALIGN)  # Title
        ctx.worksheet.format_range(f'D{data_start}:D{data_end}', LEFT_ALIGN)  # Drafted By
        ctx.worksheet.format_range(f'E{data_start}:E{data_end}', RIGHT_ALIGN)  # Overall Pick
        ctx.worksheet.format_range(f'F{data_start}:F{data_end}', RIGHT_ALIGN)  # Number of Better Picks
        ctx.worksheet.format_range(f'G{data_start}:G{data_end}', {**RIGHT_ALIGN, **CURRENCY_FORMAT})  # Missed Revenue

    def _apply_best_picks_title(self, ctx: HookContext) -> None:
        """Write Best Picks title above the asset location and merge B:G."""
        loc = ctx.asset.location
        title_cell = CellLocation(cell=loc.cell, offset_rows=-1)
        merge_end = CellLocation(cell=loc.cell, offset_rows=-1, offset_cols=5)
        merge_range = CellRange.from_bounds(
            title_cell.row, title_cell.col, merge_end.row, merge_end.col
        )
        ctx.worksheet.write_values(title_cell, [['Best Picks']])
        ctx.worksheet.merge_cells(merge_range)
        ctx.worksheet.format_range(title_cell, PICKS_TITLE_FORMAT)

    def _apply_best_picks_header(self, ctx: HookContext) -> None:
        """Apply header formatting to best picks header row."""
        loc = ctx.asset.location
        num_cols = len(ctx.asset.df.columns)
        end_cell = CellLocation(cell=loc.cell, offset_cols=num_cols - 1)
        header_range = CellRange.from_bounds(loc.row, loc.col, end_cell.row, end_cell.col)
        ctx.worksheet.format_range(header_range, HEADER_FORMAT)

    def _apply_best_picks_formatting(self, ctx: HookContext) -> None:
        """Apply cell-level formatting to best picks data rows."""
        loc = ctx.asset.location
        num_rows = len(ctx.asset.df)
        data_start = loc.row_1indexed + 1  # Skip header row
        data_end = loc.row_1indexed + num_rows
        ctx.worksheet.format_range(f'B{data_start}:B{data_end}', LEFT_ALIGN)  # Rank
        ctx.worksheet.format_range(f'C{data_start}:C{data_end}', LEFT_ALIGN)  # Title
        ctx.worksheet.format_range(f'D{data_start}:D{data_end}', LEFT_ALIGN)  # Drafted By
        ctx.worksheet.format_range(f'E{data_start}:E{data_end}', RIGHT_ALIGN)  # Overall Pick
        ctx.worksheet.format_range(f'F{data_start}:F{data_end}', RIGHT_ALIGN)  # Positions Gained
        ctx.worksheet.format_range(f'G{data_start}:G{data_end}', {**RIGHT_ALIGN, **CURRENCY_FORMAT})  # Actual Revenue

    def _write_timestamp_metadata(self, ctx: HookContext) -> None:
        """Write timestamp and update status metadata."""
        config_dict = ctx.runner_context.get('config_dict')
        if config_dict is None:
            return

        released_movies_df = ctx.runner_context.get('released_movies_df')
        year = ctx.runner_context.get('year')

        dashboard_done_updating = (
            released_movies_df is not None
            and released_movies_df['Still In Theaters'].eq('No').all()
            and len(released_movies_df) > 0
            and year < datetime.now(timezone.utc).year
        )

        log_string = f'Dashboard Last Updated\n{datetime.now(timezone.utc).strftime(DATETIME_FORMAT)} UTC'

        if dashboard_done_updating:
            log_string += '\nDashboard is done updating\nand can be removed from the etl'

        with get_duckdb(config_dict) as db:
            published_timestamp_of_most_recent_data = db.connection.query(
                """
                    select max(published_timestamp_utc) as published_timestamp_utc
                    from cleaned.box_office_mojo_dump
                """
            ).fetchnumpy()['published_timestamp_utc'][0]

        dt = published_timestamp_of_most_recent_data.item()
        log_string += f'\nData Updated Through\n{dt.strftime(DATETIME_FORMAT)} UTC'

        metadata_cell = CellLocation(cell='G2')
        ctx.worksheet.write_values(metadata_cell, [[log_string]])
        ctx.worksheet.format_range(metadata_cell, {'horizontalAlignment': 'CENTER'})

        if dashboard_done_updating:
            ctx.worksheet.set_column_width('G', 200)
