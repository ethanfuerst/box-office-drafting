"""Tests for layout calculations.

These tests verify the calculate_picks_table_layout function behavior.
"""

import pytest

from src.sheets.tabs.dashboard import calculate_picks_table_layout


@pytest.mark.parametrize(
    'scoreboard_length,released_movies_length,worst_picks_length,best_picks_length,expected',
    [
        # Plenty of space - both tables fit
        (
            5,
            50,
            10,
            10,
            {
                'available_height': 42,
                'add_both_picks_tables': True,
                'worst_picks_row_num': 12,
                'worst_picks_height': 10,
                'best_picks_row_num': 25,
                'best_picks_height': 10,
            },
        ),
        # Minimal space - triggers both tables logic with limited space
        (
            5,
            15,
            10,
            10,
            {
                'available_height': 7,
                'add_both_picks_tables': True,
                'worst_picks_row_num': 12,
                'worst_picks_height': 1,
                'best_picks_row_num': 16,
                'best_picks_height': 2,
            },
        ),
        # No space
        (
            5,
            8,
            10,
            10,
            {
                'available_height': 0,
                'add_both_picks_tables': False,
                'worst_picks_row_num': 12,
                'worst_picks_height': 0,
                'best_picks_row_num': None,
                'best_picks_height': 0,
            },
        ),
        # Negative space (scoreboard larger than released movies)
        (
            20,
            15,
            10,
            10,
            {
                'available_height': -8,
                'add_both_picks_tables': False,
                'worst_picks_row_num': 27,
                'worst_picks_height': 0,
                'best_picks_row_num': None,
                'best_picks_height': 0,
            },
        ),
        # No worst picks data
        (
            5,
            50,
            1,
            10,
            {
                'available_height': 42,
                'add_both_picks_tables': False,
                'worst_picks_row_num': 12,
                'worst_picks_height': 0,
                'best_picks_row_num': None,
                'best_picks_height': 0,
            },
        ),
        # No best picks data
        (
            5,
            50,
            10,
            1,
            {
                'available_height': 42,
                'add_both_picks_tables': False,
                'worst_picks_row_num': 12,
                'worst_picks_height': 10,
                'best_picks_row_num': None,
                'best_picks_height': 0,
            },
        ),
        # Exact minimum space for both tables
        (
            5,
            14,
            2,
            2,
            {
                'available_height': 6,
                'add_both_picks_tables': True,
                'worst_picks_row_num': 12,
                'worst_picks_height': 1,
                'best_picks_row_num': 16,
                'best_picks_height': 1,
            },
        ),
        # Large scoreboard
        (
            25,
            100,
            15,
            15,
            {
                'available_height': 72,
                'add_both_picks_tables': True,
                'worst_picks_row_num': 32,
                'worst_picks_height': 15,
                'best_picks_row_num': 50,
                'best_picks_height': 15,
            },
        ),
        # Single row of data
        (
            1,
            20,
            5,
            5,
            {
                'available_height': 16,
                'add_both_picks_tables': True,
                'worst_picks_row_num': 8,
                'worst_picks_height': 5,
                'best_picks_row_num': 16,
                'best_picks_height': 5,
            },
        ),
        # Empty worst picks but has best picks
        (
            5,
            50,
            0,
            10,
            {
                'available_height': 42,
                'add_both_picks_tables': False,
                'worst_picks_row_num': 12,
                'worst_picks_height': 0,
                'best_picks_row_num': None,
                'best_picks_height': 0,
            },
        ),
        # Space for both with limited room
        (
            5,
            16,
            10,
            10,
            {
                'available_height': 8,
                'add_both_picks_tables': True,
                'worst_picks_row_num': 12,
                'worst_picks_height': 2,
                'best_picks_row_num': 17,
                'best_picks_height': 2,
            },
        ),
        # Test with large best picks exceeding available
        (
            5,
            30,
            5,
            20,
            {
                'available_height': 22,
                'add_both_picks_tables': True,
                'worst_picks_row_num': 12,
                'worst_picks_height': 5,
                'best_picks_row_num': 20,
                'best_picks_height': 13,
            },
        ),
        # Test with large worst picks
        (
            5,
            30,
            20,
            5,
            {
                'available_height': 22,
                'add_both_picks_tables': True,
                'worst_picks_row_num': 12,
                'worst_picks_height': 9,
                'best_picks_row_num': 24,
                'best_picks_height': 5,
            },
        ),
        # Just below minimum space threshold
        (
            5,
            12,
            2,
            2,
            {
                'available_height': 4,
                'add_both_picks_tables': False,
                'worst_picks_row_num': 12,
                'worst_picks_height': 2,
                'best_picks_row_num': None,
                'best_picks_height': 0,
            },
        ),
        # Zero released movies
        (
            5,
            0,
            10,
            10,
            {
                'available_height': -8,
                'add_both_picks_tables': False,
                'worst_picks_row_num': 12,
                'worst_picks_height': 0,
                'best_picks_row_num': None,
                'best_picks_height': 0,
            },
        ),
    ],
)
def test_calculate_picks_table_layout(
    scoreboard_length,
    released_movies_length,
    worst_picks_length,
    best_picks_length,
    expected,
):
    """Layout calculation produces expected results for various inputs."""
    result = calculate_picks_table_layout(
        scoreboard_length=scoreboard_length,
        released_movies_length=released_movies_length,
        worst_picks_length=worst_picks_length,
        best_picks_length=best_picks_length,
    )

    assert result == expected
