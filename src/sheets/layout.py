"""Layout calculations for picks tables.

This module re-exports from dashboard.py to maintain backward compatibility.
The actual implementation is now in src.sheets.tabs.dashboard.
"""

from src.sheets.tabs.dashboard import calculate_picks_table_layout

__all__ = ['calculate_picks_table_layout']
