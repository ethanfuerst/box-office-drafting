"""Google Sheets dashboard module using WorksheetDefinition pattern.

This module provides worksheet definitions for the box office drafting dashboard,
following the eftoolkit WorksheetDefinition protocol for modular, testable sheets.
"""

from src.sheets.layout import calculate_picks_table_layout
from src.sheets.runner import run_dashboard
from src.sheets.tabs import DashboardWorksheet

__all__ = [
    'DashboardWorksheet',
    'calculate_picks_table_layout',
    'run_dashboard',
]
