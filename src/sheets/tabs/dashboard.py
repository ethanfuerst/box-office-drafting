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

# Cell formatting constants (migrated from JSON format files)
CURRENCY_FORMAT = {'numberFormat': {'type': 'CURRENCY', 'pattern': '$#,##0'}}
PERCENT_FORMAT = {'numberFormat': {'type': 'PERCENT', 'pattern': '#0.0#%'}}
LEFT_ALIGN = {'horizontalAlignment': 'LEFT'}
RIGHT_ALIGN = {'horizontalAlignment': 'RIGHT'}
CENTER_ALIGN = {'horizontalAlignment': 'CENTER'}


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

        # Calculate layout
        layout = calculate_picks_table_layout(
            scoreboard_length=len(scoreboard_df),
            released_movies_length=len(released_movies_df),
            worst_picks_length=len(worst_picks_df),
            best_picks_length=len(best_picks_df),
        )

        # Store data in context for formatting phase and post-processing
        context['released_movies_df'] = released_movies_df
        context['scoreboard_df'] = scoreboard_df
        context['layout'] = layout
        context['year'] = config_dict['year']
        context['dashboard_name'] = config_dict['name']
        context['sheet_height'] = len(released_movies_df) + 5
        context['config_dict'] = config_dict

        # Picks tables (conditional on available space)
        add_picks_table = layout['worst_picks_height'] > 0 and len(worst_picks_df) > 1
        context['add_picks_table'] = add_picks_table
        context['add_both_picks_tables'] = layout['add_both_picks_tables']
        context['picks_row_num'] = layout['worst_picks_row_num']
        context['best_picks_row_num'] = layout['best_picks_row_num']

        # Scoreboard asset
        assets.append(
            WorksheetAsset(
                df=scoreboard_df,
                location=CellLocation(cell='B4'),
                post_write_hooks=[
                    self._apply_scoreboard_title,
                    self._apply_scoreboard_header,
                ],
            )
        )

        # Released movies asset
        assets.append(
            WorksheetAsset(
                df=released_movies_df,
                location=CellLocation(cell='I4'),
                post_write_hooks=[
                    self._apply_released_movies_title,
                    self._apply_released_movies_header,
                    self._clear_zero_values,
                    self._write_timestamp_metadata,
                    self._log_diagnostics,
                ],
            )
        )

        # Always write worst_picks if space permits, optionally add best_picks
        if add_picks_table:
            worst_picks_df = worst_picks_df.head(layout['worst_picks_height'])
            assets.append(
                WorksheetAsset(
                    df=worst_picks_df,
                    location=CellLocation(cell=f"B{layout['worst_picks_row_num']}"),
                    post_write_hooks=[
                        self._apply_worst_picks_title,
                        self._apply_worst_picks_header,
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
                        ],
                    )
                )
                logging.info(
                    f"Showing both picks tables: worst_picks ({layout['worst_picks_height']} rows) "
                    f"and best_picks ({layout['best_picks_height']} rows)"
                )

        return assets

    def get_formatting(self, context: dict[str, Any]) -> WorksheetFormatting | None:
        """Return worksheet-level formatting configuration.

        This method returns formatting that can be expressed via WorksheetFormatting.
        Complex operations (writing titles, header formatting, timestamps) are
        handled by post-write hooks.
        """
        sheet_height = context.get('sheet_height', 100)
        add_picks_table = context.get('add_picks_table', False)

        # Note: Merge ranges are handled by post-write hooks (_apply_*_title methods)
        # to ensure proper ordering (write text, merge, format). This guarantees centering.

        # Build column widths - only override specific columns after auto_resize
        # Matches original: auto_resize first, then set specific widths
        column_widths: dict[str | int, int] = {
            # Spacer columns
            'A': 25,
            'H': 25,
            'Y': 25,
            # Title columns
            'J': 284,  # Title (released movies)
            'U': 284,  # Better Pick
            # Revenue columns
            'L': 120,  # Revenue
            'M': 120,  # Scored Revenue
            'R': 142,  # Domestic Revenue %
            'S': 120,  # Foreign Revenue
            # Other specific widths
            'G': 164,  # Unadjusted Revenue
            'W': 104,  # First Seen Date
            'X': 106,  # Still In Theaters
        }
        if add_picks_table:
            column_widths['C'] = 284  # Title column for picks tables

        # Conditional formatting for "Still In Theaters" column
        conditional_formats = [
            {
                'range': CellRange.from_string(f'X5:X{sheet_height}'),
                'type': 'TEXT_EQ',
                'values': ['Yes'],
                'format': {'backgroundColor': {'red': 0, 'green': 0.9, 'blue': 0}},
            }
        ]

        # Build format_dict for cell-level formatting (migrated from JSON format files)
        format_dict = self._build_format_dict(context)

        return WorksheetFormatting(
            notes=DASHBOARD_NOTES,
            column_widths=column_widths,
            conditional_formats=conditional_formats,
            format_dict=format_dict,
            auto_resize_columns=(1, 23),  # Auto-resize first, then column_widths override
        )

    def _build_format_dict(self, context: dict[str, Any]) -> dict[str, Any]:
        """Build the format_dict for cell-level formatting.

        Migrated from the JSON format config files on main branch:
        - scoreboard_format.json
        - released_movies_format.json
        - worst_picks_format.json
        """
        format_dict: dict[str, Any] = {}
        sheet_height = context.get('sheet_height', 100)

        # Scoreboard formatting (B4:G - from scoreboard_format.json)
        # Note: Header row (B4:G4) formatting is applied by post-write hooks
        scoreboard_df = context.get('scoreboard_df')
        scoreboard_end_row = 4 + len(scoreboard_df) if scoreboard_df is not None else 9
        format_dict[f'B5:B{scoreboard_end_row}'] = LEFT_ALIGN  # Name
        format_dict[f'C5:C{scoreboard_end_row}'] = {**RIGHT_ALIGN, **CURRENCY_FORMAT}  # Scored Revenue
        format_dict[f'F5:F{scoreboard_end_row}'] = {**RIGHT_ALIGN, **PERCENT_FORMAT}  # % Optimal Picks
        format_dict[f'G5:G{scoreboard_end_row}'] = {**RIGHT_ALIGN, **CURRENCY_FORMAT}  # Unadjusted Revenue

        # Released movies formatting (I4:X - from released_movies_format.json)
        # Note: Header row (I4:X4) formatting is applied by post-write hooks
        format_dict[f'I5:K{sheet_height}'] = LEFT_ALIGN  # Rank to Drafted By
        format_dict[f'L5:M{sheet_height}'] = {**LEFT_ALIGN, **CURRENCY_FORMAT}  # Revenue, Scored Revenue
        format_dict[f'N5:P{sheet_height}'] = RIGHT_ALIGN  # Round Drafted to Multiplier
        format_dict[f'Q5:Q{sheet_height}'] = {**RIGHT_ALIGN, **CURRENCY_FORMAT}  # Domestic Revenue
        format_dict[f'R5:R{sheet_height}'] = {**RIGHT_ALIGN, **PERCENT_FORMAT}  # Domestic Revenue %
        format_dict[f'S5:S{sheet_height}'] = {**RIGHT_ALIGN, **CURRENCY_FORMAT}  # Foreign Revenue
        format_dict[f'T5:T{sheet_height}'] = {**RIGHT_ALIGN, **PERCENT_FORMAT}  # Foreign Revenue %
        format_dict[f'V5:V{sheet_height}'] = {**RIGHT_ALIGN, **CURRENCY_FORMAT}  # Better Pick Scored Revenue
        format_dict[f'W5:W{sheet_height}'] = RIGHT_ALIGN  # First Seen Date
        format_dict[f'X5:X{sheet_height}'] = CENTER_ALIGN  # Still In Theaters

        # Worst picks formatting (from worst_picks_format.json)
        add_picks_table = context.get('add_picks_table', False)
        if add_picks_table:
            picks_row_num = context.get('picks_row_num')
            data_start = picks_row_num + 1

            # Note: Header row formatting is applied by post-write hooks
            format_dict[f'B{data_start}:B'] = LEFT_ALIGN  # Rank
            format_dict[f'C{data_start}:C'] = LEFT_ALIGN  # Title
            format_dict[f'D{data_start}:D'] = LEFT_ALIGN  # Drafted By
            format_dict[f'E{data_start}:E'] = RIGHT_ALIGN  # Overall Pick
            format_dict[f'F{data_start}:F'] = RIGHT_ALIGN  # Number of Better Picks
            format_dict[f'G{data_start}:G'] = {**RIGHT_ALIGN, **CURRENCY_FORMAT}  # Missed Revenue

            # Best picks formatting (uses same format as worst picks)
            if context.get('add_both_picks_tables'):
                best_picks_row_num = context.get('best_picks_row_num')
                best_data_start = best_picks_row_num + 1

                # Note: Header row formatting is applied by post-write hooks
                format_dict[f'B{best_data_start}:B'] = LEFT_ALIGN  # Rank
                format_dict[f'C{best_data_start}:C'] = LEFT_ALIGN  # Title
                format_dict[f'D{best_data_start}:D'] = LEFT_ALIGN  # Drafted By
                format_dict[f'E{best_data_start}:E'] = RIGHT_ALIGN  # Overall Pick
                format_dict[f'F{best_data_start}:F'] = RIGHT_ALIGN  # Positions Gained
                format_dict[f'G{best_data_start}:G'] = {**RIGHT_ALIGN, **CURRENCY_FORMAT}  # Actual Revenue

        return format_dict

    # Scoreboard hooks
    def _apply_scoreboard_title(self, ctx: HookContext) -> None:
        """Write dashboard title to cell B2 and merge B2:F2."""
        dashboard_name = ctx.runner_context.get('dashboard_name', '')
        title_cell = CellLocation(cell='B2')
        ctx.worksheet.write_values(title_cell, [[dashboard_name]])
        ctx.worksheet.merge_cells('B2:F2')
        ctx.worksheet.format_range(title_cell, TITLE_FORMAT)

    def _apply_scoreboard_header(self, ctx: HookContext) -> None:
        """Apply header formatting to scoreboard header row (B4:G4)."""
        ctx.worksheet.format_range('B4:G4', HEADER_FORMAT)

    # Released movies hooks
    def _apply_released_movies_title(self, ctx: HookContext) -> None:
        """Write Released Movies title to cell I2 and merge I2:X2."""
        title_cell = CellLocation(cell='I2')
        ctx.worksheet.write_values(title_cell, [['Released Movies']])
        ctx.worksheet.merge_cells('I2:X2')
        ctx.worksheet.format_range(title_cell, TITLE_FORMAT)

    def _apply_released_movies_header(self, ctx: HookContext) -> None:
        """Apply header formatting to released movies header row (I4:X4)."""
        ctx.worksheet.format_range('I4:X4', HEADER_FORMAT)

    def _clear_zero_values(self, ctx: HookContext) -> None:
        """Clear $0 values in Better Pick Scored Revenue column."""
        all_data = ctx.worksheet.read()
        if not all_data.empty and 'V' in all_data.columns:
            v_col_idx = list(all_data.columns).index('V')
            for i in range(4, len(all_data)):
                cell_value = all_data.iloc[i, v_col_idx] if i < len(all_data) else None
                if cell_value == '$0':
                    ctx.worksheet.write_values(CellLocation(cell=f'V{i + 1}'), [['']])

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

        # Widen column G when dashboard is done updating (more text to display)
        if dashboard_done_updating:
            ctx.worksheet.set_column_width('G', 200)

    def _log_diagnostics(self, ctx: HookContext) -> None:
        """Log diagnostic information about missing movies and revenue thresholds."""
        self._log_missing_movies(ctx.runner_context)
        self._log_min_revenue_info(ctx.runner_context)

    # Worst picks hooks
    def _apply_worst_picks_title(self, ctx: HookContext) -> None:
        """Write Worst Picks title above the asset location and merge B:G."""
        loc = ctx.asset.location
        title_row = loc.row_1indexed - 1
        title_cell = CellLocation(cell=f'{loc.col_letter}{title_row}')
        ctx.worksheet.write_values(title_cell, [['Worst Picks']])
        ctx.worksheet.merge_cells(f'B{title_row}:G{title_row}')
        ctx.worksheet.format_range(title_cell, PICKS_TITLE_FORMAT)

    def _apply_worst_picks_header(self, ctx: HookContext) -> None:
        """Apply header formatting to worst picks header row."""
        loc = ctx.asset.location
        num_cols = len(ctx.asset.df.columns)
        header_range = CellRange(
            start=loc,
            end=CellLocation(cell=f'{chr(ord(loc.col_letter) + num_cols - 1)}{loc.row_1indexed}'),
        )
        ctx.worksheet.format_range(header_range, HEADER_FORMAT)

    # Best picks hooks
    def _apply_best_picks_title(self, ctx: HookContext) -> None:
        """Write Best Picks title above the asset location and merge B:G."""
        loc = ctx.asset.location
        title_row = loc.row_1indexed - 1
        title_cell = CellLocation(cell=f'{loc.col_letter}{title_row}')
        ctx.worksheet.write_values(title_cell, [['Best Picks']])
        ctx.worksheet.merge_cells(f'B{title_row}:G{title_row}')
        ctx.worksheet.format_range(title_cell, PICKS_TITLE_FORMAT)

    def _apply_best_picks_header(self, ctx: HookContext) -> None:
        """Apply header formatting to best picks header row."""
        loc = ctx.asset.location
        num_cols = len(ctx.asset.df.columns)
        header_range = CellRange(
            start=loc,
            end=CellLocation(cell=f'{chr(ord(loc.col_letter) + num_cols - 1)}{loc.row_1indexed}'),
        )
        ctx.worksheet.format_range(header_range, HEADER_FORMAT)

    # Diagnostic helpers
    def _log_missing_movies(self, context: dict[str, Any]) -> None:
        """Log movies that are drafted but missing from the scoreboard."""
        config_dict = context.get('config_dict')
        released_movies_df = context.get('released_movies_df')

        if config_dict is None or released_movies_df is None:
            return

        draft_df = table_to_df(config_dict, 'cleaned.drafter')

        released_movies = [str(movie) for movie in released_movies_df['Title'].tolist()]
        drafted_movies = [str(movie) for movie in draft_df['movie'].tolist()]
        movies_missing_from_scoreboard = list(set(drafted_movies) - set(released_movies))

        if movies_missing_from_scoreboard:
            logging.info(
                'The following movies are missing from the scoreboard and should be added to the manual_adds.csv file:'
            )
            logging.info(', '.join(sorted(movies_missing_from_scoreboard)))
        else:
            logging.info('All movies are on the scoreboard.')

    def _log_min_revenue_info(self, context: dict[str, Any]) -> None:
        """Log movies with revenue below the minimum threshold."""
        config_dict = context.get('config_dict')
        year = context.get('year')

        if config_dict is None or year is None:
            return

        with get_duckdb(config_dict) as db:
            result = db.connection.query(
                f"""
                with most_recent_data as (
                    select title, revenue
                    from cleaned.box_office_mojo_dump where release_year = {year}
                    qualify rank() over (order by loaded_date desc) = 1
                    order by 2 desc
                )

                select title, revenue
                from most_recent_data qualify row_number() over (order by revenue asc) = 1;
                """
            ).fetchnumpy()['revenue']

            if len(result) == 0:
                logging.info('No revenue data found for this year.')
                return

            min_revenue_of_most_recent_data = result[0]

            logging.info(f'Minimum revenue of most recent data: {min_revenue_of_most_recent_data}')

            movies_under_min_revenue = (
                db.connection.query(
                    f"""
                    with cleaned_data as (
                        select title, revenue
                        from cleaned.box_office_mojo_dump
                        where release_year = {year}
                        qualify row_number() over (partition by title order by loaded_date desc) = 1
                    )

                    select cleaned_data.title from cleaned_data
                    inner join combined.base_query as base_query
                        on cleaned_data.title = base_query.title
                    where cleaned_data.revenue <= {min_revenue_of_most_recent_data}
                    """
                )
                .fetchnumpy()['title']
                .tolist()
            )

        if movies_under_min_revenue:
            logging.info(
                'The most recent records for the following movies are under the minimum revenue of the most recent data pull'
                + ' and may not have the correct revenue and should be added to the manual_adds.csv file:'
            )
            logging.info(', '.join(sorted(movies_under_min_revenue)))
        else:
            logging.info('All movies are above the minimum revenue of the most recent data pull.')
