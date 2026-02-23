"""Draftee worksheet definition.

Each draftee gets their own worksheet tab showing their drafted movies
with revenue, multiplier, and better pick information.
"""

from typing import Any

import pandas as pd
from eftoolkit.gsheets.runner.types import (
    CellLocation,
    CellRange,
    HookContext,
    WorksheetAsset,
    WorksheetFormatting,
)

from src.sheets.tabs.formats import (
    BETTER_PICK_NOTE,
    CENTER_ALIGN,
    CURRENCY_FORMAT,
    HEADER_FORMAT,
    LEFT_ALIGN,
    PERCENT_FORMAT,
    RIGHT_ALIGN,
    STILL_IN_THEATERS_NOTE,
)
from src.utils.config import ConfigDict
from src.utils.query import table_to_df

DRAFTEE_NOTES = {
    CellLocation(cell='F5'): STILL_IN_THEATERS_NOTE,
    CellLocation(cell='J5'): BETTER_PICK_NOTE,
}

DRAFTEE_COLUMN_WIDTHS = {
    'A': 25,   # Border
    'B': 130,  # Round / Scored Revenue
    'C': 100,  # Overall Pick / # Released
    'D': 284,  # Movie / # Optimal Picks
    'E': 120,  # First Seen Date / % Optimal Picks
    'F': 160,  # Still In Theaters / Unadjusted Revenue
    'G': 120,  # Revenue
    'H': 80,   # Multiplier
    'I': 140,  # Scored Revenue
    'J': 284,  # Better Pick
    'K': 200,  # Better Pick Scored Revenue
    'L': 25,   # Border
}

SCOREBOARD_COLUMNS = [
    'Scored Revenue',
    '# Released',
    '# Optimal Picks',
    '% Optimal Picks',
    'Unadjusted Revenue',
]

PICKS_COLUMN_RENAME = {
    'round': 'Round',
    'overall_pick': 'Overall Pick',
    'movie': 'Movie',
    'first_seen_date': 'First Seen Date',
    'still_in_theaters': 'Still In Theaters',
    'revenue': 'Revenue',
    'multiplier': 'Multiplier',
    'scored_revenue': 'Scored Revenue',
    'better_pick': 'Better Pick',
    'better_pick_scored_revenue': 'Better Pick Scored Revenue',
}

PICKS_DISPLAY_COLUMNS = list(PICKS_COLUMN_RENAME.values())


class DrafteeWorksheet:
    """Worksheet definition for a draftee's picks tab.

    Each draftee gets their own tab showing their drafted movies ordered by
    round and overall pick, with revenue and scoring information.
    """

    def __init__(self, draftee_name: str) -> None:
        self._draftee_name = draftee_name

    @property
    def name(self) -> str:
        """The worksheet tab name (draftee's name)."""
        return self._draftee_name

    def generate(
        self, config: dict[str, Any], context: dict[str, Any]
    ) -> list[WorksheetAsset]:
        """Generate draftee scoreboard and picks assets.

        Args:
            config: Configuration dictionary containing 'config_dict' key.
            context: Runtime context shared across all worksheets.

        Returns:
            List of WorksheetAssets: scoreboard at B2 and picks table at B5.
        """
        config_dict: ConfigDict = config['config_dict']

        if '_draftee_dashboard_df' not in context:
            context['_draftee_dashboard_df'] = table_to_df(
                config_dict, 'dashboards.draftee_dashboard'
            )
        if '_scoreboard_df' not in context:
            context['_scoreboard_df'] = table_to_df(
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

        # Build scoreboard for this draftee
        scoreboard_df: pd.DataFrame = context['_scoreboard_df']
        draftee_scoreboard = scoreboard_df[
            scoreboard_df['Name'] == self._draftee_name
        ].copy()
        draftee_scoreboard = draftee_scoreboard.drop(columns=['Name'])

        if draftee_scoreboard.empty:
            draftee_scoreboard = pd.DataFrame(
                [[0, 0, 0, 0, 0]], columns=SCOREBOARD_COLUMNS
            )

        # Build picks for this draftee
        full_df: pd.DataFrame = context['_draftee_dashboard_df']
        picks_df = full_df[full_df['draftee_name'] == self._draftee_name].copy()
        picks_df = picks_df.drop(columns=['draftee_name'])
        picks_df = picks_df.rename(columns=PICKS_COLUMN_RENAME)
        picks_df = picks_df[PICKS_DISPLAY_COLUMNS]
        picks_df = picks_df.infer_objects(copy=False).fillna('')

        context_key = f'draftee_{self._draftee_name}_df'
        context[context_key] = picks_df

        return [
            WorksheetAsset(
                df=draftee_scoreboard,
                location=CellLocation(cell='B2'),
                post_write_hooks=[
                    self._apply_scoreboard_header,
                    self._apply_scoreboard_formatting,
                ],
            ),
            WorksheetAsset(
                df=picks_df,
                location=CellLocation(cell='B5'),
                post_write_hooks=[
                    self._apply_picks_header,
                    self._apply_picks_formatting,
                    self._apply_still_in_theaters_conditional_format,
                ],
            ),
        ]

    def get_formatting(
        self, context: dict[str, Any]
    ) -> WorksheetFormatting | None:  # noqa: ARG002
        """Return worksheet-level formatting (column widths and notes)."""
        return WorksheetFormatting(
            notes=DRAFTEE_NOTES, column_widths=DRAFTEE_COLUMN_WIDTHS
        )

    # Scoreboard hooks

    def _apply_scoreboard_header(self, ctx: HookContext) -> None:
        """Apply header formatting to scoreboard row B2:F2."""
        header_range = CellRange.from_string('B2:F2')
        ctx.worksheet.format_range(header_range, HEADER_FORMAT)

    def _apply_scoreboard_formatting(self, ctx: HookContext) -> None:
        """Apply cell-level formatting to scoreboard data row."""
        ctx.worksheet.format_range('B3:B3', {**RIGHT_ALIGN, **CURRENCY_FORMAT})
        ctx.worksheet.format_range('C3:D3', RIGHT_ALIGN)
        ctx.worksheet.format_range('E3:E3', {**RIGHT_ALIGN, **PERCENT_FORMAT})
        ctx.worksheet.format_range('F3:F3', {**RIGHT_ALIGN, **CURRENCY_FORMAT})

    # Picks hooks

    def _apply_picks_header(self, ctx: HookContext) -> None:
        """Apply header formatting to picks row B5:K5."""
        header_range = CellRange.from_string('B5:K5')
        ctx.worksheet.format_range(header_range, HEADER_FORMAT)

    def _apply_picks_formatting(self, ctx: HookContext) -> None:
        """Apply cell-level formatting to picks data rows."""
        context_key = f'draftee_{self._draftee_name}_df'
        picks_df = ctx.runner_context.get(context_key)
        if picks_df is None or picks_df.empty:
            return

        num_rows = len(picks_df)
        data_start = 6  # Data starts at row 6 (header is row 5)
        data_end = data_start + num_rows - 1

        ctx.worksheet.format_range(
            f'B{data_start}:B{data_end}', RIGHT_ALIGN
        )  # Round
        ctx.worksheet.format_range(
            f'C{data_start}:C{data_end}', RIGHT_ALIGN
        )  # Overall Pick
        ctx.worksheet.format_range(
            f'D{data_start}:D{data_end}', LEFT_ALIGN
        )  # Movie
        ctx.worksheet.format_range(
            f'E{data_start}:E{data_end}', RIGHT_ALIGN
        )  # First Seen Date
        ctx.worksheet.format_range(
            f'F{data_start}:F{data_end}', CENTER_ALIGN
        )  # Still In Theaters
        ctx.worksheet.format_range(
            f'G{data_start}:G{data_end}', {**RIGHT_ALIGN, **CURRENCY_FORMAT}
        )  # Revenue
        ctx.worksheet.format_range(
            f'H{data_start}:H{data_end}', RIGHT_ALIGN
        )  # Multiplier
        ctx.worksheet.format_range(
            f'I{data_start}:I{data_end}', {**RIGHT_ALIGN, **CURRENCY_FORMAT}
        )  # Scored Revenue
        ctx.worksheet.format_range(
            f'J{data_start}:J{data_end}', LEFT_ALIGN
        )  # Better Pick
        ctx.worksheet.format_range(
            f'K{data_start}:K{data_end}', {**RIGHT_ALIGN, **CURRENCY_FORMAT}
        )  # Better Pick Scored Revenue

    def _apply_still_in_theaters_conditional_format(
        self, ctx: HookContext
    ) -> None:
        """Apply conditional formatting to Still In Theaters column (F)."""
        context_key = f'draftee_{self._draftee_name}_df'
        picks_df = ctx.runner_context.get(context_key)
        if picks_df is None or picks_df.empty:
            return

        num_rows = len(picks_df)
        data_start = 6
        data_end = data_start + num_rows - 1

        ctx.worksheet.add_conditional_format(
            range_name=f'F{data_start}:F{data_end}',
            rule={
                'type': 'TEXT_EQ',
                'values': ['Yes'],
                'format': {
                    'backgroundColor': {'red': 0, 'green': 0.9, 'blue': 0}
                },
            },
        )
