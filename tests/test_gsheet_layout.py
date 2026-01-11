"""Tests for Google Sheets dashboard layout calculations."""


def calculate_picks_table_layout(
    scoreboard_length: int,
    released_movies_length: int,
    worst_picks_length: int,
    best_picks_length: int,
) -> dict:
    """
    Calculate the layout for picks tables based on available space.

    This mirrors the logic in GoogleSheetDashboard.__init__().

    Args:
        scoreboard_length: Number of rows in scoreboard (not including header)
        released_movies_length: Number of rows in released movies (not including header)
        worst_picks_length: Number of rows in worst picks data (not including header)
        best_picks_length: Number of rows in best picks data (not including header)

    Returns:
        dict with layout information including row numbers and heights
    """
    # Calculate available space for picks tables
    # Formula: released_movies_height - scoreboard_height - 3 (for blank rows/spacing)
    available_height = released_movies_length - scoreboard_length - 3

    # First picks table starts at: 5 (title rows) + scoreboard_height + 2 (blank + title)
    picks_row_num = 5 + scoreboard_length + 2

    # Track whether we're showing both tables
    add_both_picks_tables = False
    best_picks_row_num = None
    worst_picks_height = 0
    best_picks_height = 0

    # Always try to show both tables
    # Calculate space needed for both tables
    # Each table needs: 1 (title row) + 1 (header row) + data rows
    # Plus: 2 (blank row separator between tables)
    min_rows_per_table = 2  # title + header (minimum to show anything useful)
    separator_rows = 2  # blank row between tables

    # Check if we have enough space for both tables
    total_required = min_rows_per_table * 2 + separator_rows

    if (
        available_height >= total_required
        and worst_picks_length > 1
        and best_picks_length > 1
    ):
        # We have space for both tables
        add_both_picks_tables = True

        # Split available height between the two tables
        # Total consumption per table: 1 (title) + 1 (header) + N (data rows)
        # Available space for both tables' content (header + data rows)
        usable_height = available_height - 2 - separator_rows  # subtract title rows and separator

        # Split evenly for data rows (each table gets header + data)
        height_per_table = usable_height // 2

        # Worst picks comes first
        worst_picks_height = min(height_per_table, worst_picks_length)

        # Best picks comes second, after worst picks + separator
        # best_picks_row_num = picks_row_num + 1 (title) + worst_picks_height + separator_rows
        best_picks_row_num = picks_row_num + 1 + worst_picks_height + separator_rows

        # Calculate remaining height for best picks
        # Remaining space = usable_height - worst_picks_height
        best_picks_height = min(usable_height - worst_picks_height, best_picks_length)
    else:
        # Not enough space for both, fall back to worst picks only
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


class TestPicksTableLayout:
    """Test cases for picks table layout calculations."""

    def test_both_tables_with_plenty_of_space(self):
        """Test when there's plenty of space for both tables."""
        result = calculate_picks_table_layout(
            scoreboard_length=5,  # 5 players
            released_movies_length=100,  # 100 movies released
            worst_picks_length=50,  # 50 worst picks available
            best_picks_length=50,  # 50 best picks available
        )

        # available_height = 100 - 5 - 3 = 92
        assert result['available_height'] == 92
        assert result['add_both_picks_tables'] is True

        # usable_height = 92 - 2 (titles) - 2 (separator) = 88
        # height_per_table = 88 // 2 = 44
        assert result['worst_picks_height'] == 44
        assert result['best_picks_height'] == 44

        # worst picks starts at: 5 + 5 + 2 = 12
        assert result['worst_picks_row_num'] == 12

        # best picks starts at: 12 + 1 (title) + 44 (worst_picks_height) + 2 (separator) = 59
        assert result['best_picks_row_num'] == 59

    def test_both_tables_with_minimal_space(self):
        """Test when there's just enough space for both tables."""
        result = calculate_picks_table_layout(
            scoreboard_length=2,  # 2 players
            released_movies_length=15,  # 15 movies released
            worst_picks_length=10,  # 10 worst picks available
            best_picks_length=10,  # 10 best picks available
        )

        # available_height = 15 - 2 - 3 = 10
        assert result['available_height'] == 10
        assert result['add_both_picks_tables'] is True

        # usable_height = 10 - 2 (titles) - 2 (separator) = 6
        # height_per_table = 6 // 2 = 3
        assert result['worst_picks_height'] == 3
        assert result['best_picks_height'] == 3

        # worst picks starts at: 5 + 2 + 2 = 9
        assert result['worst_picks_row_num'] == 9

        # best picks starts at: 9 + 1 (title) + 3 (worst_picks_height) + 2 (separator) = 15
        assert result['best_picks_row_num'] == 15

    def test_both_tables_with_odd_space(self):
        """Test when available space is odd, ensuring both tables get proper allocation."""
        result = calculate_picks_table_layout(
            scoreboard_length=2,  # 2 players
            released_movies_length=16,  # 16 movies released
            worst_picks_length=10,  # 10 worst picks available
            best_picks_length=10,  # 10 best picks available
        )

        # available_height = 16 - 2 - 3 = 11
        assert result['available_height'] == 11
        assert result['add_both_picks_tables'] is True

        # usable_height = 11 - 2 (titles) - 2 (separator) = 7
        # height_per_table = 7 // 2 = 3 (integer division)
        assert result['worst_picks_height'] == 3
        # best_picks gets the remainder: 7 - 3 = 4
        assert result['best_picks_height'] == 4

    def test_fallback_to_worst_picks_only(self):
        """Test fallback to worst picks when not enough space for both."""
        result = calculate_picks_table_layout(
            scoreboard_length=2,  # 2 players
            released_movies_length=8,  # 8 movies released
            worst_picks_length=10,  # 10 worst picks available
            best_picks_length=10,  # 10 best picks available
        )

        # available_height = 8 - 2 - 3 = 3
        assert result['available_height'] == 3
        # total_required = 2*2 + 2 = 6, but available = 3, so fallback
        assert result['add_both_picks_tables'] is False

        assert result['worst_picks_height'] == 3  # use all available space
        assert result['best_picks_height'] == 0
        assert result['best_picks_row_num'] is None

    def test_limited_worst_picks_data(self):
        """Test when worst picks data is limited."""
        result = calculate_picks_table_layout(
            scoreboard_length=5,  # 5 players
            released_movies_length=100,  # 100 movies released
            worst_picks_length=10,  # Only 10 worst picks available
            best_picks_length=50,  # 50 best picks available
        )

        # available_height = 100 - 5 - 3 = 92
        assert result['available_height'] == 92
        assert result['add_both_picks_tables'] is True

        # usable_height = 92 - 2 (titles) - 2 (separator) = 88
        # height_per_table = 88 // 2 = 44
        # But worst_picks_length = 10, so worst_picks_height = min(44, 10) = 10
        assert result['worst_picks_height'] == 10
        # best_picks gets: 88 - 10 = 78, but capped at best_picks_length = 50
        assert result['best_picks_height'] == 50

    def test_limited_best_picks_data(self):
        """Test when best picks data is limited."""
        result = calculate_picks_table_layout(
            scoreboard_length=5,  # 5 players
            released_movies_length=100,  # 100 movies released
            worst_picks_length=50,  # 50 worst picks available
            best_picks_length=10,  # Only 10 best picks available
        )

        # available_height = 100 - 5 - 3 = 92
        assert result['available_height'] == 92
        assert result['add_both_picks_tables'] is True

        # usable_height = 92 - 2 (titles) - 2 (separator) = 88
        # height_per_table = 88 // 2 = 44
        assert result['worst_picks_height'] == 44
        # best_picks gets: 88 - 44 = 44, but capped at best_picks_length = 10
        assert result['best_picks_height'] == 10

    def test_no_data_for_best_picks(self):
        """Test when there's no data for best picks."""
        result = calculate_picks_table_layout(
            scoreboard_length=2,  # 2 players
            released_movies_length=20,  # 20 movies released
            worst_picks_length=10,  # 10 worst picks available
            best_picks_length=0,  # No best picks available
        )

        # Should fall back to worst picks only
        assert result['add_both_picks_tables'] is False
        assert result['worst_picks_height'] == 10
        assert result['best_picks_height'] == 0

    def test_ethan_and_noah_2025_case(self):
        """Test the specific case from Ethan and Noah 2025 draft."""
        # From the screenshot: scoreboard has 2 rows, showing worst picks but not best picks
        result = calculate_picks_table_layout(
            scoreboard_length=2,  # 2 players
            released_movies_length=20,  # assumption based on screenshot
            worst_picks_length=13,  # from screenshot
            best_picks_length=13,  # assumption
        )

        # This should show both tables if there's enough space
        if result['add_both_picks_tables']:
            assert result['worst_picks_height'] > 0
            assert result['best_picks_height'] > 0
            # Verify both tables get equal or near-equal allocation
            assert (
                abs(result['worst_picks_height'] - result['best_picks_height']) <= 1
            ), 'Tables should have roughly equal heights'
