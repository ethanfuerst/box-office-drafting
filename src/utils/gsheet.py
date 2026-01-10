import json
import logging
import os
from datetime import datetime, timezone

import gspread_formatting as gsf
from dotenv import load_dotenv
from gspread import service_account_from_dict

from src import project_root
from src.utils.config import ConfigDict
from src.utils.constants import DATETIME_FORMAT
from src.utils.db_connection import duckdb_connection
from src.utils.format import load_format_config
from src.utils.gspread_format import df_to_sheet
from src.utils.logging_config import setup_logging
from src.utils.query import table_to_df

setup_logging()

load_dotenv()


class GoogleSheetDashboard:
    def __init__(self, config_dict: ConfigDict) -> None:
        """Initialize a Google Sheet dashboard with data from DuckDB."""
        self.config = config_dict
        self.year = self.config['year']
        self.gspread_credentials_name = self.config['gspread_credentials_name']
        self.dashboard_name = self.config['name']
        self.sheet_name = self.config['sheet_name']
        self.released_movies_df = table_to_df(
            self.config,
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

        self.scoreboard_df = table_to_df(
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

        # Always load both dataframes
        self.worst_picks_df = table_to_df(
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

        self.best_picks_df = table_to_df(
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

        self.dashboard_elements = [
            (
                self.scoreboard_df,
                'B4',
                load_format_config(
                    project_root / 'src' / 'assets' / 'scoreboard_format.json'
                ),
            ),
            (
                self.released_movies_df,
                'I4',
                load_format_config(
                    project_root / 'src' / 'assets' / 'released_movies_format.json'
                ),
            ),
        ]

        # Calculate available space for picks tables
        # Formula: released_movies_height - scoreboard_height - 2 (for blank rows/spacing)
        available_height = len(self.released_movies_df) - len(self.scoreboard_df) - 2

        self.add_picks_table = (
            available_height > 0
            and len(self.worst_picks_df) > 1
        )

        # First picks table starts at: 5 (title rows) + scoreboard_height + 2 (blank + title)
        self.picks_row_num = 5 + len(self.scoreboard_df) + 2

        # Track whether we're showing both tables
        self.add_both_picks_tables = False
        self.best_picks_row_num = None

        # Always try to show both tables
        # Calculate space needed for both tables
        # Each table needs: 1 (title row) + 1 (header row) + data rows
        # Plus: 2 (blank row separator between tables)
        min_rows_per_table = 2  # title + header (minimum to show anything useful)
        separator_rows = 2  # blank row between tables

        # Check if we have enough space for both tables
        total_required = min_rows_per_table * 2 + separator_rows

        if available_height >= total_required and len(self.worst_picks_df) > 1 and len(self.best_picks_df) > 1:
            # We have space for both tables
            self.add_both_picks_tables = True
            self.add_picks_table = True

            # Split available height between the two tables
            # Total consumption per table: 1 (title) + 1 (header) + N (data rows)
            # Total space: available_height = worst_title + worst_header + worst_data + separator + best_title + best_header + best_data
            # After subtracting fixed overhead: available_height - 2 (titles) - 2 (separator) = space for headers + data
            # Since headers are 1 row each: available_height - 2 - 2 - 2 = available_height - 6 = space for data only
            # Actually, the header is part of the table, so: available_height - 2 (titles) - 2 (separator) = space for both tables (header+data)

            # Available space for both tables' content (header + data rows)
            usable_height = available_height - 2 - separator_rows  # subtract title rows and separator

            # Split evenly for data rows (each table gets header + data)
            height_per_table = usable_height // 2

            # Worst picks comes first
            worst_picks_height = min(height_per_table, len(self.worst_picks_df))
            self.worst_picks_df = self.worst_picks_df.head(worst_picks_height)

            # Best picks comes second, after worst picks + separator
            # best_picks_row_num = picks_row_num + 1 (title) + worst_picks_height + separator_rows
            self.best_picks_row_num = self.picks_row_num + 1 + worst_picks_height + separator_rows

            # Calculate remaining height for best picks
            # Remaining space = usable_height - worst_picks_height
            best_picks_height = min(
                usable_height - worst_picks_height,
                len(self.best_picks_df)
            )
            self.best_picks_df = self.best_picks_df.head(best_picks_height)

            # Add worst picks table
            self.dashboard_elements.append(
                (
                    self.worst_picks_df,
                    f'B{self.picks_row_num}',
                    {
                        key.replace('12', str(self.picks_row_num)).replace(
                            '13', str(self.picks_row_num + 1)
                        ): value
                        for key, value in load_format_config(
                            project_root / 'src' / 'assets' / 'worst_picks_format.json'
                        ).items()
                    },
                )
            )

            # Add best picks table
            self.dashboard_elements.append(
                (
                    self.best_picks_df,
                    f'B{self.best_picks_row_num}',
                    {
                        key.replace('12', str(self.best_picks_row_num)).replace(
                            '13', str(self.best_picks_row_num + 1)
                        ): value
                        for key, value in load_format_config(
                            project_root / 'src' / 'assets' / 'worst_picks_format.json'
                        ).items()
                    },
                )
            )

            logging.info(f"Showing both picks tables: worst_picks ({worst_picks_height} rows) and best_picks ({best_picks_height} rows)")
        else:
            # Not enough space for both, fall back to worst picks only
            logging.info(f"Not enough space for both tables (available: {available_height}, required: {total_required}). Falling back to worst picks only.")
            self.add_picks_table = available_height > 0 and len(self.worst_picks_df) > 1

            if self.add_picks_table:
                self.worst_picks_df = self.worst_picks_df.head(available_height)

                self.dashboard_elements.append(
                    (
                        self.worst_picks_df,
                        f'B{self.picks_row_num}',
                        {
                            key.replace('12', str(self.picks_row_num)).replace(
                                '13', str(self.picks_row_num + 1)
                            ): value
                            for key, value in load_format_config(
                                project_root / 'src' / 'assets' / 'worst_picks_format.json'
                            ).items()
                        },
                    )
                )

        self.setup_worksheet()

    def setup_worksheet(self) -> None:
        """Create and configure the Google Sheet worksheet."""
        gspread_credentials_key = self.gspread_credentials_name
        gspread_credentials = os.getenv(gspread_credentials_key)

        if gspread_credentials is not None:
            credentials_dict = json.loads(gspread_credentials.replace('\n', '\\n'))
            gc = service_account_from_dict(credentials_dict)
        else:
            raise ValueError(
                f'{gspread_credentials_key} is not set or is invalid in the .env file.'
            )

        sh = gc.open(self.sheet_name)

        worksheet_title = 'Dashboard'
        worksheet = sh.worksheet(worksheet_title)

        sh.del_worksheet(worksheet)
        # 3 rows for title, 1 row for column titles, 1 row for footer
        self.sheet_height = len(self.released_movies_df) + 5
        worksheet = sh.add_worksheet(
            title=worksheet_title, rows=self.sheet_height, cols=25, index=1
        )
        self.worksheet = sh.worksheet(worksheet_title)


def update_dashboard(
    gsheet_dashboard: GoogleSheetDashboard, config_dict: ConfigDict
) -> None:
    """Update the Google Sheet with dashboard data and metadata."""
    for element in gsheet_dashboard.dashboard_elements:
        df_to_sheet(
            df=element[0],
            worksheet=gsheet_dashboard.worksheet,
            location=element[1],
            format_dict=element[2] if len(element) > 2 else None,
        )

    dashboard_done_updating = (
        gsheet_dashboard.released_movies_df['Still In Theaters'].eq('No').all()
        and len(gsheet_dashboard.released_movies_df) > 0
        and gsheet_dashboard.year < datetime.now(timezone.utc).year
    )

    log_string = f'Dashboard Last Updated\n{datetime.now(timezone.utc).strftime(DATETIME_FORMAT)} UTC'

    if dashboard_done_updating:
        log_string += '\nDashboard is done updating\nand can be removed from the etl'

    with duckdb_connection(config_dict) as duckdb_con:
        published_timestamp_of_most_recent_data = duckdb_con.query(
            """
                select max(published_timestamp_utc) as published_timestamp_utc
                from cleaned.box_office_mojo_dump
            """
        ).fetchnumpy()['published_timestamp_utc'][0]

    # Convert numpy.datetime64 to Python datetime
    dt = published_timestamp_of_most_recent_data.item()
    log_string += f'\nData Updated Through\n{dt.strftime(DATETIME_FORMAT)} UTC'

    # Adding last updated header
    gsheet_dashboard.worksheet.update(
        values=[[log_string]],
        range_name='G2',
    )

    gsheet_dashboard.worksheet.format(
        'G2',
        {
            'horizontalAlignment': 'CENTER',
        },
    )

    # Columns are created with 12 point font, then auto resized and reduced to 10 point bold font
    gsheet_dashboard.worksheet.columns_auto_resize(1, 7)
    gsheet_dashboard.worksheet.columns_auto_resize(8, 23)

    gsheet_dashboard.worksheet.format(
        'B4:G4',
        {
            'horizontalAlignment': 'CENTER',
            'textFormat': {
                'fontSize': 10,
                'bold': True,
            },
        },
    )

    if gsheet_dashboard.add_picks_table:
        if gsheet_dashboard.add_both_picks_tables:
            # Format worst picks header
            gsheet_dashboard.worksheet.format(
                f'B{gsheet_dashboard.picks_row_num}:G{gsheet_dashboard.picks_row_num}',
                {
                    'horizontalAlignment': 'CENTER',
                    'textFormat': {
                        'fontSize': 10,
                        'bold': True,
                    },
                },
            )
            # Format best picks header
            gsheet_dashboard.worksheet.format(
                f'B{gsheet_dashboard.best_picks_row_num}:G{gsheet_dashboard.best_picks_row_num}',
                {
                    'horizontalAlignment': 'CENTER',
                    'textFormat': {
                        'fontSize': 10,
                        'bold': True,
                    },
                },
            )
        else:
            # Single table
            gsheet_dashboard.worksheet.format(
                f'B{gsheet_dashboard.picks_row_num}:G{gsheet_dashboard.picks_row_num}',
                {
                    'horizontalAlignment': 'CENTER',
                    'textFormat': {
                        'fontSize': 10,
                        'bold': True,
                    },
                },
            )

    gsheet_dashboard.worksheet.format(
        'I4:X4',
        {
            'horizontalAlignment': 'CENTER',
            'textFormat': {
                'fontSize': 10,
                'bold': True,
            },
        },
    )

    for i in range(5, gsheet_dashboard.sheet_height):
        if gsheet_dashboard.worksheet.acell(f'V{i}').value == '$0':
            gsheet_dashboard.worksheet.update(values=[['']], range_name=f'V{i}')

    # resizing spacer columns
    spacer_columns = ['A', 'H', 'Y']
    for column in spacer_columns:
        gsf.set_column_width(gsheet_dashboard.worksheet, column, 25)

    # for some reason the auto resize still cuts off some of the title
    title_columns = ['J', 'U']

    if gsheet_dashboard.add_picks_table:
        title_columns.append('C')

    for column in title_columns:
        gsf.set_column_width(gsheet_dashboard.worksheet, column, 284)

    # revenue columns will also get cut off
    revenue_columns = ['L', 'M', 'R', 'S']
    for column in revenue_columns:
        gsf.set_column_width(gsheet_dashboard.worksheet, column, 120)

    # gets resized wrong and have to do it manually
    gsf.set_column_width(gsheet_dashboard.worksheet, 'G', 164)
    gsf.set_column_width(gsheet_dashboard.worksheet, 'R', 142)
    gsf.set_column_width(gsheet_dashboard.worksheet, 'W', 104)
    gsf.set_column_width(gsheet_dashboard.worksheet, 'X', 106)

    if dashboard_done_updating:
        gsf.set_column_width(gsheet_dashboard.worksheet, 'G', 200)


def update_titles(gsheet_dashboard: GoogleSheetDashboard) -> None:
    """Update section titles in the Google Sheet."""
    gsheet_dashboard.worksheet.update(
        values=[[gsheet_dashboard.dashboard_name]], range_name='B2'
    )
    gsheet_dashboard.worksheet.format(
        'B2',
        {'horizontalAlignment': 'CENTER', 'textFormat': {'fontSize': 20, 'bold': True}},
    )
    gsheet_dashboard.worksheet.merge_cells('B2:F2')
    gsheet_dashboard.worksheet.update(values=[['Released Movies']], range_name='I2')
    gsheet_dashboard.worksheet.format(
        'I2',
        {'horizontalAlignment': 'CENTER', 'textFormat': {'fontSize': 20, 'bold': True}},
    )
    gsheet_dashboard.worksheet.merge_cells('I2:X2')

    if gsheet_dashboard.add_picks_table:
        if gsheet_dashboard.add_both_picks_tables:
            # Add worst picks title
            worst_picks_title_row_num = gsheet_dashboard.picks_row_num - 1
            gsheet_dashboard.worksheet.update(
                values=[['Worst Picks']],
                range_name=f'B{worst_picks_title_row_num}',
            )
            gsheet_dashboard.worksheet.format(
                f'B{worst_picks_title_row_num}',
                {'horizontalAlignment': 'CENTER', 'textFormat': {'bold': True}},
            )
            gsheet_dashboard.worksheet.merge_cells(
                f'B{worst_picks_title_row_num}:G{worst_picks_title_row_num}'
            )

            # Add best picks title
            best_picks_title_row_num = gsheet_dashboard.best_picks_row_num - 1
            gsheet_dashboard.worksheet.update(
                values=[['Best Picks']],
                range_name=f'B{best_picks_title_row_num}',
            )
            gsheet_dashboard.worksheet.format(
                f'B{best_picks_title_row_num}',
                {'horizontalAlignment': 'CENTER', 'textFormat': {'bold': True}},
            )
            gsheet_dashboard.worksheet.merge_cells(
                f'B{best_picks_title_row_num}:G{best_picks_title_row_num}'
            )
        else:
            # Single table (worst picks only)
            picks_title_row_num = gsheet_dashboard.picks_row_num - 1
            gsheet_dashboard.worksheet.update(
                values=[['Worst Picks']],
                range_name=f'B{picks_title_row_num}',
            )
            gsheet_dashboard.worksheet.format(
                f'B{picks_title_row_num}',
                {'horizontalAlignment': 'CENTER', 'textFormat': {'bold': True}},
            )
            gsheet_dashboard.worksheet.merge_cells(
                f'B{picks_title_row_num}:G{picks_title_row_num}'
            )


def apply_conditional_formatting(gsheet_dashboard: GoogleSheetDashboard) -> None:
    """Apply conditional formatting rules to the Google Sheet."""
    still_in_theater_rule = gsf.ConditionalFormatRule(
        ranges=[gsf.GridRange.from_a1_range('X5:X', gsheet_dashboard.worksheet)],
        booleanRule=gsf.BooleanRule(
            condition=gsf.BooleanCondition('TEXT_EQ', ['Yes']),
            format=gsf.CellFormat(
                backgroundColor=gsf.Color(0, 0.9, 0),
            ),
        ),
    )

    rules = gsf.get_conditional_format_rules(gsheet_dashboard.worksheet)
    rules.append(still_in_theater_rule)
    rules.save()

    logging.info('Dashboard updated and formatted')


def add_comments_to_dashboard(gsheet_dashboard: GoogleSheetDashboard) -> None:
    """Add comments to the dashboard."""
    notes_dict = load_format_config(
        project_root / 'src' / 'assets' / 'dashboard_notes.json'
    )

    worksheet = gsheet_dashboard.worksheet
    worksheet.insert_notes(notes_dict)


def log_missing_movies(gsheet_dashboard: GoogleSheetDashboard) -> None:
    """Log movies that are drafted but missing from the scoreboard."""
    draft_df = table_to_df(
        gsheet_dashboard.config,
        'cleaned.drafter',
    )
    released_movies = [
        str(movie) for movie in gsheet_dashboard.released_movies_df['Title'].tolist()
    ]
    drafted_movies = [str(movie) for movie in draft_df['movie'].tolist()]
    movies_missing_from_scoreboard = list(set(drafted_movies) - set(released_movies))

    if movies_missing_from_scoreboard:
        logging.info(
            'The following movies are missing from the scoreboard and should be added to the manual_adds.csv file:'
        )
        logging.info(', '.join(sorted(movies_missing_from_scoreboard)))
    else:
        logging.info('All movies are on the scoreboard.')


def log_min_revenue_info(
    gsheet_dashboard: GoogleSheetDashboard, config_dict: ConfigDict
) -> None:
    """Log movies with revenue below the minimum threshold."""
    with duckdb_connection(config_dict) as duckdb_con:
        result = duckdb_con.query(
            f"""
            with most_recent_data as (
                select title, revenue
                from cleaned.box_office_mojo_dump where release_year = {gsheet_dashboard.year}
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

        logging.info(
            f'Minimum revenue of most recent data: {min_revenue_of_most_recent_data}'
        )

        movies_under_min_revenue = (
            duckdb_con.query(
                f"""
                with cleaned_data as (
                    select title, revenue
                    from cleaned.box_office_mojo_dump
                    where release_year = {gsheet_dashboard.year}
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
        logging.info(
            'All movies are above the minimum revenue of the most recent data pull.'
        )


def load_dashboard_data(config_dict: ConfigDict) -> None:
    """Load configuration and update the Google Sheet dashboard."""
    gsheet_dashboard = GoogleSheetDashboard(config_dict)

    update_dashboard(gsheet_dashboard, config_dict)
    update_titles(gsheet_dashboard)
    apply_conditional_formatting(gsheet_dashboard)
    add_comments_to_dashboard(gsheet_dashboard)
    log_missing_movies(gsheet_dashboard)
    log_min_revenue_info(gsheet_dashboard, config_dict)
