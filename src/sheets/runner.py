"""Dashboard runner with custom formatting and post-processing.

This module wraps eftoolkit's DashboardRunner with worksheet structure setup
specific to the box office drafting dashboard.

Post-processing is implemented via post_write_hooks on WorksheetAsset,
which receive context with the worksheet reference (eftoolkit 1.1.1+).
Worksheet structure setup uses pre_run_hooks (eftoolkit 1.2.0+).
"""

import json
import logging
import os
from typing import Any

from eftoolkit.gsheets.runner import DashboardRunner

from src.sheets.tabs import DashboardWorksheet
from src.utils.config import ConfigDict
from src.utils.db_connection import get_duckdb
from src.utils.query import table_to_df


def run_dashboard(config_dict: ConfigDict) -> None:
    """Run the complete dashboard update workflow.

    This orchestrates:
    1. Setup worksheet structure via pre_run_hooks (Manual Adds, Multipliers, Dashboard)
    2. Generate and write dashboard data via DashboardRunner
    3. Apply formatting via WorksheetFormatting
    4. Run post-write hooks (titles, header formatting, timestamps)
    5. Run runner post-hooks (sheet resize, worksheet order)

    Args:
        config_dict: Configuration dictionary with sheet settings.
    """
    credentials_dict = _load_credentials(config_dict['gspread_credentials_name'])
    sheet_name = config_dict['sheet_name']

    runner: DashboardRunner | None = None

    def _resize_sheet(ss: Any) -> None:
        """Resize sheet to match data height."""
        nonlocal runner
        if runner is None:
            return
        sheet_height = runner.context.get('sheet_height', 100)
        ws = ss.worksheet('Dashboard')
        ws.resize_sheet(rows=sheet_height, columns=25)

    runner = DashboardRunner(
        config={
            'sheet_name': sheet_name,
            'config_dict': config_dict,
        },
        credentials=credentials_dict,
        worksheets=[DashboardWorksheet()],
        pre_run_hooks=[_handle_missing_worksheets],
        post_run_hooks=[_resize_sheet, _adjust_worksheet_order],
    )
    runner.run()

    logging.info('Dashboard updated and formatted')

    _log_missing_movies(config_dict)
    _log_min_revenue_info(config_dict)


def _load_credentials(gspread_credentials_name: str) -> dict[str, Any]:
    """Load Google service account credentials from environment."""
    gspread_credentials = os.getenv(gspread_credentials_name)

    if gspread_credentials is not None:
        return json.loads(gspread_credentials.replace('\n', '\\n'))
    else:
        raise ValueError(
            f'{gspread_credentials_name} is not set or is invalid in the .env file.'
        )


def _handle_missing_worksheets(ss: Any) -> None:
    """Create missing worksheets if missing."""
    existing_worksheets = ss.get_worksheet_names()
    if 'Manual Adds' not in existing_worksheets:
        ss.create_worksheet('Manual Adds', rows=100, cols=5)
    if 'Multipliers and Exclusions' not in existing_worksheets:
        ss.create_worksheet('Multipliers and Exclusions', rows=100, cols=3)
    if 'Dashboard' in existing_worksheets:
        ss.delete_worksheet('Dashboard')
    ss.create_worksheet('Dashboard', rows=500, cols=25)


def _adjust_worksheet_order(ss: Any) -> None:
    """Put worksheets in correct order"""
    ss.reorder_worksheets(
        ['Dashboard', 'Draft', 'Manual Adds', 'Multipliers and Exclusions']
    )


def _log_missing_movies(config_dict: ConfigDict) -> None:
    """Log movies that are drafted but missing from the scoreboard."""
    draft_df = table_to_df(config_dict, 'cleaned.drafter')
    released_df = table_to_df(config_dict, 'combined.base_query')

    released_movies = set(str(movie) for movie in released_df['title'].tolist())
    drafted_movies = set(str(movie) for movie in draft_df['movie'].tolist())
    movies_missing_from_scoreboard = sorted(drafted_movies - released_movies)

    if movies_missing_from_scoreboard:
        logging.info(
            'The following movies are missing from the scoreboard and should be added to the manual_adds.csv file:'
        )
        logging.info(', '.join(movies_missing_from_scoreboard))
    else:
        logging.info('All movies are on the scoreboard.')


def _log_min_revenue_info(config_dict: ConfigDict) -> None:
    """Log movies with revenue below the minimum threshold."""
    year = config_dict['year']

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
