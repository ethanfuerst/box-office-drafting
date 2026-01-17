import pytest

from src.utils.gsheet import calculate_picks_table_layout


@pytest.mark.parametrize(
    'scoreboard_length,released_movies_length,worst_picks_length,best_picks_length,'
    'expected_both_tables,expected_worst_height,expected_best_height',
    [
        # Plenty of space: available=92, usable=88, per_table=44
        pytest.param(5, 100, 50, 50, True, 44, 44, id='plenty_of_space'),
        # Minimal space: available=10, usable=6, per_table=3
        pytest.param(2, 15, 10, 10, True, 3, 3, id='minimal_space'),
        # Odd space: available=11, usable=7, per_table=3, best gets remainder=4
        pytest.param(2, 16, 10, 10, True, 3, 4, id='odd_space'),
        # Fallback to worst only: available=3 < total_required=6
        pytest.param(2, 8, 10, 10, False, 3, 0, id='fallback_worst_only'),
        # Limited worst picks data: capped at worst_picks_length=10
        pytest.param(5, 100, 10, 50, True, 10, 50, id='limited_worst_picks'),
        # Limited best picks data: capped at best_picks_length=10
        pytest.param(5, 100, 50, 10, True, 44, 10, id='limited_best_picks'),
        # No best picks data: falls back to worst only
        pytest.param(2, 20, 10, 0, False, 10, 0, id='no_best_picks'),
        # Equal data both tables: available=15, usable=11, per_table=5
        pytest.param(2, 20, 13, 13, True, 5, 6, id='equal_data'),
        # More worst picks data: available=19, usable=15, per_table=7
        pytest.param(3, 25, 20, 8, True, 7, 8, id='more_worst_picks'),
        # More best picks data: available=19, usable=15, per_table=7
        pytest.param(3, 25, 8, 20, True, 7, 8, id='more_best_picks'),
        # Barely enough space: available=8, usable=4, per_table=2
        pytest.param(5, 16, 10, 10, True, 2, 2, id='barely_enough_space'),
        # Not enough space: available=4 < total_required=6
        pytest.param(5, 12, 10, 10, False, 4, 0, id='not_enough_space'),
        # No worst picks data
        pytest.param(2, 20, 0, 10, False, 0, 0, id='no_worst_picks'),
        # Single row of data each (worst_picks_length <= 1)
        pytest.param(2, 20, 1, 1, False, 0, 0, id='single_row_each'),
        # Large scoreboard: available=47, usable=43, per_table=21
        pytest.param(50, 100, 20, 20, True, 20, 20, id='large_scoreboard'),
    ],
)
def test_layout_calculation(
    scoreboard_length,
    released_movies_length,
    worst_picks_length,
    best_picks_length,
    expected_both_tables,
    expected_worst_height,
    expected_best_height,
):
    """Layout calculation handles various input combinations."""
    result = calculate_picks_table_layout(
        scoreboard_length=scoreboard_length,
        released_movies_length=released_movies_length,
        worst_picks_length=worst_picks_length,
        best_picks_length=best_picks_length,
    )

    assert result['add_both_picks_tables'] is expected_both_tables
    assert result['worst_picks_height'] == expected_worst_height
    assert result['best_picks_height'] == expected_best_height
    assert result['worst_picks_row_num'] == 5 + scoreboard_length + 2
    if expected_both_tables:
        assert result['best_picks_row_num'] is not None
    else:
        assert result['best_picks_row_num'] is None
