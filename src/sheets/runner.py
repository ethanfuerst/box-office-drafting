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


def run_dashboard(config_dict: ConfigDict) -> None:
    """Run the complete dashboard update workflow.

    This orchestrates:
    1. Setup worksheet structure via pre_run_hooks (Manual Adds, Multipliers, Dashboard)
    2. Generate and write dashboard data via DashboardRunner
    3. Apply formatting via WorksheetFormatting
    4. Run post-write hooks (titles, header formatting, timestamps)

    Args:
        config_dict: Configuration dictionary with sheet settings.
    """
    credentials_dict = _load_credentials(config_dict['gspread_credentials_name'])
    sheet_name = config_dict['sheet_name']

    DashboardRunner(
        config={
            'sheet_name': sheet_name,
            'config_dict': config_dict,
        },
        credentials=credentials_dict,
        worksheets=[DashboardWorksheet()],
        pre_run_hooks=[_adjust_worksheet_order],
    ).run()

    logging.info('Dashboard updated and formatted')


def _load_credentials(gspread_credentials_name: str) -> dict[str, Any]:
    """Load Google service account credentials from environment."""
    gspread_credentials = os.getenv(gspread_credentials_name)

    if gspread_credentials is not None:
        return json.loads(gspread_credentials.replace('\n', '\\n'))
    else:
        raise ValueError(
            f'{gspread_credentials_name} is not set or is invalid in the .env file.'
        )


def _adjust_worksheet_order(context: dict[str, Any]) -> None:
    """Create and configure the Google Sheet worksheet structure.

    This is used as a pre_run_hooks entry for DashboardRunner (eftoolkit 1.2.0+).
    The context contains 'spreadsheet' with the active Spreadsheet instance.
    """
    ss = context['spreadsheet']
    existing_worksheets = ss.get_worksheet_names()
    if 'Manual Adds' not in existing_worksheets:
        ss.create_worksheet('Manual Adds', rows=100, cols=5)
    if 'Multipliers and Exclusions' not in existing_worksheets:
        ss.create_worksheet('Multipliers and Exclusions', rows=100, cols=3)
    if 'Dashboard' in existing_worksheets:
        ss.delete_worksheet('Dashboard')
    ss.create_worksheet('Dashboard', rows=500, cols=25)

    ss.reorder_worksheets(
        ['Dashboard', 'Draft', 'Manual Adds', 'Multipliers and Exclusions']
    )
