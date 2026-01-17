"""Google Sheets dashboard module using WorksheetDefinition pattern.

This module provides worksheet definitions for the box office drafting dashboard,
following the eftoolkit WorksheetDefinition protocol for modular, testable sheets.
"""

from src.sheets.tabs import DashboardWorksheet

__all__ = [
    'DashboardWorksheet']
